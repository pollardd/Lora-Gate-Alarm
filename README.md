# Lora-Gate-Alarm
```
Receive a door bell style tone when a gate is opened a long distance away using Raspberry Pi Pico and LoRa modules
This project uses the follwoing hardware 
1x Raspberry Pi Pico W
1x Raspberry Pi Pico (non wifi)
2x SX1262 LoRa Node Module for Raspberry Pi Pico, LoRaWAN Brand: Waveshare
    The LoRa modules above included a battery and external antenna (when I bought them)
1x Small Speaker (salvaged from an old telephone) 
1x Microswitch to sense the open gate (salvaged from a broken angle grinder)
1x LED with resistor (200 ohm?) to indicate open gate count and error messages
Mounting boxes etc.

## Installation
The file listing below describes which files are required on the main (house) device and which are required on the remote (gate) device(s)
FileName                    Location Device     Description
=============================================================================================
blink.py                    Main                Display Errors and Remote gate open events on the LED
constants.py                Both                Debug and encryption settings
counters.py                 Main                Stores the gate open count
dateTime.py                 Main                Formats date time to your prefferences / location.
debug.py                    Both                Debug Routines
debugCounter.txt            Both                Shared location for debug counter / ID
encryption.py               Both                Shared calls to encrypt decrypt routines
GenerateEncryptionKey.py    Main                Generate secret encryption key to be saved on all devices (secrets.py)
loraMessage.py              Both                Format message into Json format 
mainGate.py                 Remote              Main entry point for remote devices.  Save as main.py to auto start
mainHouse.py                Main                Main entry point for main device.  Save as main.py to auto start
mpyaes.py                   Both                Encrypt and Decrypt routines
ntpClientTZ.py              Main                Update time from network using sntp with time zone parameters.
secrets.py                  Remote              Contains Encryption and Decryption keys
secretsHouse.py             Main                Contains Encryptions keys and WIFI creds.
subprocess.py               Main                Run second thread to receive and transmit lora messages
sx1262.py                   Both                Third Party Lora Module code 
sx126x.py                   Both                Third Party Lora Module code
tone.py                     Main                Play the alert sound
webServer.py                Main                User web interface for monitoring and counter reset
_sx126x.py                  Both                Third Party Lora Module code

## Debugging
<TODO>

## Third Party Software 
Modules and examples used as is or modified as required
Original source and modified code included in the repository

##### Lora Messages
    https://github.com/ehong-tl/micropySX126X

##### Encryption
    https://github.com/iyassou/mpyaes

##### WIFI Network and NTP Time updates
    https://gist.github.com/aallan/581ecf4dc92cd53e3a415b7c33a1147c

##### Web Server
    https://how2electronics.com/raspberry-pi-pico-w-web-server-tutorial-with-micropython/
