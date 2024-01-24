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
  * https://github.com/fkwp/heat-pump-api/blob/master/doc/ElsterTable.inc

  
## setup the can bus on homeassistant OS: 
1. richtiger ssh benötigt!!!
2. apk add iproute2 
3. ip link set can0 txqueuelen 1000
4. ip link set dev can0 up type can bitrate 50000
5. ip -details link show can0

### links
* https://elinux.org/Bringing_CAN_interface_up
* https://python-can.readthedocs.io/en/stable/interfaces/socketcan.html

## Development
* pip3 install homeassistant --break-system-packages
* pip install python-can
* apk add can-utils
* candump can0
