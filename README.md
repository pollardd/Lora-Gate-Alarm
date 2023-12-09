# Lora-Gate-Alarm

Receive a door bell style tone wirelessly when a gate is opened a long distance away using 2x Raspberry Pi Pico's and LoRa modules.

This project uses the follwoing hardware

- 1x Raspberry Pi Pico W 2022 (wifi model) 
- 1x Raspberry Pi Pico 2020 (non wifi)
- 2x SX1262 LoRa Node Module for Raspberry Pi Pico, Brand: Waveshare
      <BR>NOTE: The LoRa modules above included a battery and external antenna (when I bought them)
- 1x Small Speaker (salvaged from an old telephone) 
- 1x Microswitch to sense the open gate (salvaged from a broken angle grinder)
- or
- 1x PiicoDev Magnetometer (way easier than mounting the above switch)
- 1x Button (on while pressed) connect pin 30 to Gnd to reset the device
- 1x LED with resistor (200 ohm?) to indicate open gate count and error messages
- Mounting boxes etc.

NOTE: PiicoDev Magnetometer not listed in my parts list.  You can find it here.
https://core-electronics.com.au/piicodev-magnetometer-qmc6310.html

## Software Version
- MicroPython v1.19.1-850-gfe2a8332f on 2023-02-01
<BR>NOTE: I had mixed and inconsistent results with different Micropython versions around early February 2023.  The one above worked consistently.
- Thony Version 4.01

## Installation
- Modify secrets.py with generated encryption keys using GenerateEncryptionKey.py
  Note: In Version 2.0, Encryption disabled in constants.py.  (Needs more testing).
- Modify secretsHouse.py with your Wifi SSID and password
- Set a time zone in hours plus or minus UTC in constants.py  (no automatic daylight savings adjustments are made)
- Set a NTP time pool server local to you in constants.py 
- Save the files to the required devices as listed below.
- Configure FULLBATTERY= and EMPTYBATTERY= IN mainGate.py to contain the maximum and minumum voltage levels for your battery. These will be converted and displeyed as a percentage. Trial and error may be required.  Percentage displayed on the internal web page.
- Disable debugging in constants.py by setting it to 0 once things are running smoothly

NOTE: While testing set LOWPOWERMODE to False (constants.py) on remote device while connected to Thonny.  It mucks up the USB connection and confuse the shit out of you.

The file listing below describes which files are required on the main (house) device and which are required on the remote (gate) device and Both if it is req1uired on both devices.

| FileName                   | Location | Device  | Description |
| ---------------------------|----------|---------|-------------|
| BatteryLevel.txt           | Main     |         | Stores the last know battery level and update time |
| compass.py                 | Remote   |         | Used to calibrate the Magnetometer.  (only run once manually) |
| blink.py                   | Main     |         | Display Errors and Remote gate open events on the LED |
| constants.py               | Both     |         | Debug and encryption settings |
| counters.py                | Main     |         | Stores the gate open count |
| dateTime.py                | Main     |         | Formats date time to your prefferences / location. |
| debug.py                   | Both     |         | Debug Routines |
| debugCounter.txt           | Both     |         | Shared location for debug counter / ID |
| diskFree.py                | Both     |         | Returns amount of free storage space |
| encryption.py              | Both     |         | Shared calls to encrypt decrypt routines |
| fileTail.py                | Main     |         | Returns the specified number of lines from the end of a file. |
| GenerateEncryptionKey.py   | Main     |         | Generate secret encryption key to be saved on all devices (secrets.py) |
| getHeadingDiff.py          | Remote   |         | Returns the current heading (gate angle) compared to the starting heading|
| loraMessage.py             | Both     |         | Format message into Json format |
| mainGate.py <BR>(Rename to main.py)| Remote   |         | Main entry point for remote devices.  Save as main.py to auto start |
| mainHouse.py <BR>(Rename to main.py)| Main     |         | Main entry point for main device.  Save as main.py to auto start |
| mpyaes.py                  | Both     |         | Encrypt and Decrypt routines |
| ntpClientTZ.py             | Main     |         | Update time from network using sntp with time zone parameters. |
| secrets.py                 | Remote   |         | Contains Encryption and Decryption keys |
| secretsHouse.py            | Main     |         | Contains Encryptions keys and WIFI creds. |
| subprocess.py              | Main     |         | Run second thread to receive and transmit lora messages |
| sx1262.py                  | Both     |         | Third Party Lora Communications Module code |
| sx126x.py                  | Both     |         | Third Party Lora Communications Module code |
| tone.py                    | Main     |         | Play
| webServer.py               | Main     |         | User web interface for monitoring |
| _sx126x.py                 | Both     |         |  Third Party Lora Communications Module code |

## Debugging
Debugging output commands are throughout the code. The level of output can be controlled from settings within constants.py. `DEBUG=0` is off. Available levels are 0-3. Output is to the console and to a file. File output can be disabled in `constants.py`. `LOGTOFILE = False`. Disable logging to file when testing is complete to avoid running out of storage space in the small file system. Output is to a file on the Pico named `debugLog.csv`. This file can be deleted and it will automatically recreated as required.
Version 2.0 includes an option to automatically delete the log file at start up.  A Ten second countdown is displayed on the console.  Exit the program in Thonny if you wish to retain and examin the log.

## Third Party Software 
Modules and examples from the code below are used as is or modified as required. Original source and modified code is included in this repository.

##### Lora Messages
- https://github.com/ehong-tl/micropySX126X

##### Encryption
- https://github.com/iyassou/mpyaes

##### WIFI Network and NTP Time updates
- https://gist.github.com/aallan/581ecf4dc92cd53e3a415b7c33a1147c

##### Web Server 
- https://how2electronics.com/raspberry-pi-pico-w-web-server-tutorial-with-micropython/

## How it works
For a full description see my project page on Core Electronics where I sourced most of the hardware.
https://core-electronics.com.au/projects/lora-p2p-wireless-gate-alarm/
