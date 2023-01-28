# Lora-Gate-Alarm
Receive a door bell style tone when a gate is opened over 300 meters away using Raspberry Pi Pico modules
This project uses the follwoing hardware 
1x Raspberry Pi Pico W
1x Raspberry Pi Pico (non wifi)
2x SX1262 LoRa Node Module for Raspberry Pi Pico, LoRaWAN Brand: Waveshare
    The LoRa modules above included a battery and external antenna (when I bought them)
Small Speaker (salvaged from an old telephone) 
Microswitch to sense the open gate (salvaged from a broken angle grinder)
LED with resistor (200 ohm?) to indicate open gate count and error messages
`
Installation
===============
<TODO>

Debugging
===============
<TODO>

Third Party Software 
=====================
(Used as is or modified)

Lora Messages
    https://github.com/ehong-tl/micropySX126X
Encryption
    https://github.com/iyassou/mpyaes
WIFI Network and NTP Time updates
    https://gist.github.com/aallan/581ecf4dc92cd53e3a415b7c33a1147c
Web Server
    https://how2electronics.com/raspberry-pi-pico-w-web-server-tutorial-with-micropython/
