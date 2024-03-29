# Stiebel Eltron CAN for Home Assistant
This custom integration for Home Assistant allows users to monitor the status of their Stiebel Eltron heat pump directly from their Home Assistant instance. The integration fetches the status by CAN Bus and presents it as sensor entities in Home Assistant.

## Installation
### Via HACS (Home Assistant Community Store)
1. Navigate to the HACS page on your Home Assistant instance.
2. Go to the "Integrations" tab and click the "Explore & Add Repositories" button.
3. Search for "Stiebel Eltron CAN" and select it.
4. Click on "Install this repository in HACS".
5. Restart your Home Assistant instance.

### Manual Installation
1. Clone this repository or download the zip file.
2. Copy the stiebel_eltron_can directory from the custom_components directory in this repository to the custom_components directory on your Home Assistant instance
3. Restart your Home Assistant instance.


## links 
  * https://github.com/Andy2003/heat-pump-api
  * https://python-can.readthedocs.io/en/stable/index.html
  * https://pypi.org/project/cantools/

  
## setup the can bus on homeassistant OS: 
1. use add-on "Advanced SSH & Web Terminal" (see https://github.com/hassio-addons/addon-ssh)
2. apk add iproute2 
3. ip link set can0 txqueuelen 1000
4. ip link set dev can0 up type can bitrate 50000
5. ip -details link show can0

### links
* https://elinux.org/Bringing_CAN_interface_up
* https://python-can.readthedocs.io/en/stable/interfaces/socketcan.html
* https://github.com/andig/goelster
* https://github.com/Andy2003/heat-pump-api
* https://github.com/kr0ner/OneESP32ToRuleThemAll
* https://github.com/bullitt186/ha-stiebel-control
* https://github.com/roberreiter/StiebelEltron-heatpump-over-esphome-can-bus

## Development
* pip3 install homeassistant --break-system-packages
* pip install python-can
* apk add can-utils
* candump can0

* alternative framework for using: https://pypi.org/project/cantools/
* https://www.csselectronics.com/pages/dbc-editor-can-bus-database
* https://github.com/danielbayerlein/sepicker
* https://developers.home-assistant.io/docs/integration_fetching_data/
* https://github.com/home-assistant/example-custom-config/tree/master/custom_components/example_sensor/


## found positive log entries

topicheatpump/HSBC 300 cool/outside/environment/temperature value: 0.0 unit:°C
topicheatpump/HSBC 300 cool/outside/environment/temperature value: 1.9000000000000001 unit:°C
topicheatpump/HSBC 300 cool/inverter/environment/temperature value: 1.9000000000000001 unit:°C
topicheatpump/HSBC 300 cool/boiler/hotwater/temperature value: 0.0 unit:°C
topicheatpump/HSBC 300 cool/boiler/hotwater/temperature value: 45.400000000000006 unit:°C