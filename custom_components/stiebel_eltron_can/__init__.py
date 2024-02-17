"""
Stiebel Eltron CAN Bus Integration
"""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    Platform,
)

from .const import *


_LOGGER = logging.getLogger(DOMAIN)
_LOGGER.setLevel(logging.DEBUG)


PLATFORMS: list[Platform] = [
    #Platform.BINARY_SENSOR,
    #Platform.BUTTON,
    #Platform.CLIMATE,
    #Platform.NUMBER,
    #Platform.SELECT,
    Platform.SENSOR,
    #Platform.SWITCH,
    #Platform.WATER_HEATER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug("async_setup_entry2 %r %r", entry, entry.data)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward the setup to the sensor platform.
    await hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, PLATFORMS))
    return True
