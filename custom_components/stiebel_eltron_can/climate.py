"""Support for stiebel_eltron_can climate platform."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
import ctypes

import can
from homeassistant.components.climate import (
    PRESET_ECO,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature, CONF_LIGHTS, CONF_NAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


from .const import *

_LOGGER = logging.getLogger(DOMAIN)
_LOGGER.setLevel(logging.DEBUG)


PRESET_DAY = "day"
PRESET_SETBACK = "setback"
PRESET_EMERGENCY = "emergency"

SUPPORT_HVAC = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]
SUPPORT_PRESET = [PRESET_ECO, PRESET_DAY, PRESET_EMERGENCY, PRESET_SETBACK]

# Mapping STIEBEL ELTRON states to homeassistant states/preset.
STE_TO_HA_HVAC = {
    "AUTOMATIC": HVACMode.AUTO,
    "MANUAL MODE": HVACMode.HEAT,
    "STANDBY": HVACMode.AUTO,
    "DAY MODE": HVACMode.AUTO,
    "SETBACK MODE": HVACMode.AUTO,
    "DHW": HVACMode.OFF,
    "EMERGENCY OPERATION": HVACMode.AUTO,
}

STE_TO_HA_PRESET = {
    "STANDBY": PRESET_ECO,
    "DAY MODE": PRESET_DAY,
    "SETBACK MODE": PRESET_SETBACK,
    "EMERGENCY OPERATION": PRESET_EMERGENCY,
}

HA_TO_STE_HVAC = {
    HVACMode.AUTO: "AUTOMATIC",
    HVACMode.HEAT: "MANUAL MODE",
    HVACMode.OFF: "DHW",
}

HA_TO_STE_PRESET = {k: i for i, k in STE_TO_HA_PRESET.items()}



async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][config_entry.entry_id]
    _LOGGER.debug('async_setup_entry %r %r', data, config_entry)

    # Load CAN bus. Must be operational already (done by external network tool).
    # Setting bitrate might work, but ideally that should also be set already.
    # We only care about messages related to feedback from a SET command or the reply from a GET command.
    bus = can.Bus(bustype=data[CONF_INTERFACE], channel=data[CONF_CHANNEL], bitrate=125000, receive_own_messages=True, can_filters=[
        {"can_id": 0x0002FF01, "can_mask": 0x1FFFFFFF, "extended": True},  # Reply to SET
        {"can_id": 0x01FDFF01, "can_mask": 0x1FFFFFFF, "extended": True},  # Reply to GET
    ])

    # Global CAN bus lock, required since the reply to a GET does not include any differentiator.
    # This means we must lock, then send out a GET request.
    # The reply will then only be acked by the entity that holds the lock.
    # I don't like this, it smells, but it works and IDK how to do it better.
    lock = asyncio.Lock()

    entities = [StiebelEltron(bus, e, lock, config_entry.entry_id) for e in data[CONF_LIGHTS]]
    notifier = can.Notifier(bus, [e.on_can_message_received for e in entities], loop=asyncio.get_running_loop())
    async_add_entities(entities)

    @callback
    def stop(event):
        notifier.stop()
        bus.shutdown()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop)

class StiebelEltron(ClimateEntity):
    """Representation of a STIEBEL ELTRON heat pump."""
    _attr_has_entity_name = True
    _attr_name = None
    _attr_hvac_modes = SUPPORT_HVAC
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, self.unique_id)
            },
            "name": self._name,
        }

    def __init__(self, bus: can.BusABC, o: dict, lock: asyncio.Lock, prefix: str):
        """Initialize the unit."""
        self._bus = bus
        self._lock = lock
        # Unpack some config values
        # Unpack some config values
        self._name: str = o[CONF_NAME]
        self._module = o[CONF_MODULE]
        self._relay = o[CONF_RELAY]
        self._outsideTemperatur = None
        self._target_temperature = None
        self._current_temperature = None
        self._current_humidity = None
        self._operation = None
        self._filter_alarm = None
        self._force_update = False
        # Prepare fixed ids & payloads
        self._set_id: int = 0x01FC0002 | (self._module << 8)
        self._bytes_off: bytes = bytes((self._module, self._relay, 0, 0xFF, 0xFF))
        self._bytes_on: bytes = bytes((self._module, self._relay, 1, 0xFF, 0xFF))
        self._bytes_status: bytes = bytes((self._module, self._relay))
        # Internals to do locking & support GET operation
        self._awaiting_update = False
        self._event_update = asyncio.Event()
        # Logger
        self._log = _LOGGER.getChild(self._name)
        self._attr_unique_id = f"stiebel_eltron_can.{prefix}.{self._module}.{self._relay}"
    
    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {"filter_alarm": self._filter_alarm}

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name


    @property
    def outside_temperature(self) -> float:
        return self._outsideTemperatur

    # Handle ClimateEntityFeature.TARGET_TEMPERATURE


    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 0.1

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 10.0

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 30.0

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return float(f"{self._current_humidity:.1f}")

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current operation ie. heat, cool, idle."""
        return STE_TO_HA_HVAC.get(self._operation)

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., home, away, temp."""
        return STE_TO_HA_PRESET.get(self._operation)

    @property
    def preset_modes(self):
        """Return a list of available preset modes."""
        return SUPPORT_PRESET

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new operation mode."""
        if self.preset_mode:
            return
        new_mode = HA_TO_STE_HVAC.get(hvac_mode)
        _LOGGER.debug("set_hvac_mode: %s -> %s", self._operation, new_mode)
        #self._ste_data.api.set_operation(new_mode)
        self._force_update = True

    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        target_temperature = kwargs.get(ATTR_TEMPERATURE)
        if target_temperature is not None:
            _LOGGER.debug("set_temperature: %s", target_temperature)
            #self._ste_data.api.set_target_temp(target_temperature)
            self._force_update = True

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        new_mode = HA_TO_STE_PRESET.get(preset_mode)
        _LOGGER.debug("set_hvac_mode: %s -> %s", self._operation, new_mode)
        #self._ste_data.api.set_operation(new_mode)
        self._force_update = True

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._bus.send(can.Message(arbitration_id=self._set_id, data=self._bytes_on, is_extended_id=True), timeout=.1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._bus.send(can.Message(arbitration_id=self._set_id, data=self._bytes_off, is_extended_id=True), timeout=.1)

    def on_can_message_received(self, msg: can.Message):
        #FIXME must be multiply with 0.1
        if msg.data[2] == 0x0C:
            self.outside_temperature = ctypes.c_int16(((msg.data[3] & 0xFF) << 8) | (msg.data[4] & 0xFF)).value

        # Reply to SET, this we can filter because data contains data from.
        if msg.arbitration_id == 0x0002FF01 and msg.data[0] == self._module and msg.data[1] == self._relay:
            self.is_on = msg.data[2] == 1
        # Reply to GET, this we can only filter by _knowing_ that we are waiting on an update.
        if msg.arbitration_id == 0x01FDFF01 and self._awaiting_update:
            self.is_on = msg.data[0] == 1
            self._event_update.set()

    async def async_update(self):
        # The update cycle must be blocked on the CAN bus lock.
        async with self._lock:
            try:
                # Inform handler that we expect an update.
                self._awaiting_update = True
                # Small delay, otherwise we overload the CAN module.
                await asyncio.sleep(.01)
                # Ask CAN module for an update
                self._bus.send(can.Message(arbitration_id=0x01FCFF01, data=self._bytes_status, is_extended_id=True), timeout=.1)
                # Wait for reply to come
                await asyncio.wait_for(self._event_update.wait(), 0.5)
                # Small delay, otherwise we overload the CAN module.
                await asyncio.sleep(.01)
            finally:
                # In all cases, no matter how we get out of this, we must unset the _awaiting_update flag.
                self._awaiting_update = False