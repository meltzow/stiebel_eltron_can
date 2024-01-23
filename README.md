# Stiebel Eltron CAN for Home Assistant

## Installation

## theory

0x000c = Außentemperatur float temperature

"HERSTELLER_KENNUNG"                               , 0x0147, 0
"GERAETE_KENNUNG"                                  , 0x0148, 0


### links 
  https://github.com/Andy2003/heat-pump-api
  
  https://github.com/fkwp/heat-pump-api/blob/master/doc/ElsterTable.inc
  
  https://python-can.readthedocs.io/en/stable/interfaces/gs_usb.html
  https://elinux.org/Bringing_CAN_interface_up
  
  
## setup: 
0.) richtiger ssh benötigt!!!
1.) apk add iproute2 
2.) pip install python-can
pip install python-can --break-system-packages


ip link set can0 type can bitrate 125000
ip link set dev can0 up type can bitrate 500000
