# This file (mainHouse.py) is executed on the HOUSE Device
# Rename to main.py so it executes at startup
# Intented to run on a Raspberry Pi Pico W (wifi)
# ==========================================
#
# The Lora Connection and configuration is based on an this example.
# https://github.com/ehong-tl/micropySX126X
#
# Save the following files to the root folder of the pico same as main.py
# sx1262.py, sx126x.py, _sx126x.py

# Network Connection and sntp time settings modified from example found here
# https://gist.github.com/aallan/581ecf4dc92cd53e3a415b7c33a1147c

# Threading implementation is based on this example
# https://circuitdigest.com/microcontroller-projects/dual-core-programming-on-raspberry-pi-pico-using-micropython
# =========================================================================
# Asked a question re Recursion Limit Error
# https://stackoverflow.com/questions/75257342/micropython-runtimeerror-maximum-recursion-depth-exceeded

# import micropython
# micropython.mem_info(1)

# Not sure why I need this
# Without the garbage collection, I get the following error message
# File "sx1262.py", line 2, in <module>
# MemoryError: memory allocation failed, allocating 4168 bytes
import gc
#print("main() mem before gc="+ str(gc.mem_free()))
gc.collect()
#print("main() mem after gc="+ str(gc.mem_free()))

import network      # module that handles connecting to WiFi
import socket       # module that handles tcp/ip connections
import urequests    # module handles making servicing and network requests
import time
import ntpClientTZ  # Modified ntpClient to include Time Zone adjustment.
import machine
import _thread      # We are running the Lora communication code in a seperate process

from machine import Pin, PWM

# Home baked imports
import subprocess   # Methods that are run in Thread 2
import debug        # My debuging routine
import secretsHouse # file containing wifi ssid and password plus Encryption key and IV values
import dateTime     # My Date Time formatting routine
import blink        # Reuseable code to flash the LED error messages or open gate count
import constants    # Constants used on all devices
import counters     # Counter variables shared between modules
import encryption   # Encrypt and Decrypt routines
import webServer    # Publish the web page and listen for connections

# Constants
DEBUG = constants.DEBUG
LOGTOFILE =  constants.LOGTOFILE
ENCRYPTION = constants.ENCRYPTION
TIMEZONE = constants.TIMEZONE      # Set to your time zone +or- hours from UTC  (No Summertime)
NTPSERVER = constants.NTPSERVER    # change to a time server pool in your local area
HZ=900                             # Tone of the sound

# Network Variables
ip=""                   # Global variable to hold the wifi connection IP address
sta_if = network.WLAN(network.STA_IF)

# Temperature Sensor
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

# Pin Definitions
ledPin = 5                              # Physical Pin 7  Gnd = 8
led = Pin(ledPin, Pin.OUT)              # Define pin as output 
#button =  Pin(14, Pin.IN, Pin.PULL_UP)  # Physical Pin 19 Gnd = 13
buzzer = PWM(Pin(13))                   # Physical pin 17 Gnd = 18

# Start a new counter each time the program starts
debug.resetCounter()

# Method Definitions
# =========================================

def connectToWifi():
    global ip
    global sta_if
    
    if(DEBUG >=1):
        debug.debug(DEBUG, "connectToWifi()    ", "Connecting to WIFI " + secretsHouse.ssid, LOGTOFILE)

    connectCount=0
    sta_if = network.WLAN(network.STA_IF)
    # Set your SSID and Password in secrets<Device>.py
    sta_if.active(True)                               # Activate the interface

    while connectCount<=5:
        sta_if.connect(secretsHouse.ssid, secretsHouse.password)    # Connect
        time.sleep(10)
        # Test if network is connected
        if not(sta_if.isconnected()):
            connectCount=connectCount+1
            if(DEBUG >=1):
                debug.debug(DEBUG, "connectToWifi()    ", "Connecting to WIFI  Count=" + str(connectCount) , LOGTOFILE)
        else:
            connectCount=6

    if not(sta_if.isconnected()):
        debug.debug(DEBUG, "connectToWifi()    ", "Connect to Network: Failed:" + str(connectCount), LOGTOFILE)
        # Error indication on LED
        flash(1,2)  # Fatal error, no return from this

    if(DEBUG >=1):
        ip=sta_if.ifconfig()[0]
        debug.debug(DEBUG, "connectToWifi()    ", "Connected to WIFI, IP="+str(ip), LOGTOFILE)
    time.sleep(5)

def setLocalClock():
    # Retrieve Time from smtp and set local clock
    try:    
        ntpClientTZ.setTime(TIMEZONE, NTPSERVER, DEBUG, LOGTOFILE)

    except Exception as errorMsg:
        # This message can not be disabled by DEBUG setting
        debug.debug(DEBUG, "setLocalClock()    ", "Set Time From Network: Error=" + str(errorMsg), LOGTOFILE)
        flash(1,3)  # Fatal error, no return from this

    if(DEBUG >=1):
        timeStamp=str(dateTime.formattedTime())
        debug.debug(DEBUG, "setLocalClock()    ", "Time after ntp update=" + str(timeStamp), LOGTOFILE)
        dateStamp=str(dateTime.formattedDate())
        debug.debug(DEBUG, "setLocalClock()    ", "Date after ntp update=" + str(dateStamp), LOGTOFILE)

def flash(long, short):
    # Flash the LED to indicate a gate open event or error
    #=====================================================
    # short flash only, number of gate openes since last reset (Manual button to reset).

    # Flash the LED to Indicate an error Long flash then Short flashe(s).
    # 1 long, 1 short = Low voltage at mainGate.py
    # 1 long, 2 short = Unable to connect to Wifi at mainHouse.py
    # 1 long, 3 short = Unable to set system clock at mainHouse.py
    # 1 long, 4 short = Unable to open socket for inbound web page connection
    # 1 long, 5 short = Heartbeat message timed out
    
    if(DEBUG >=2):
        debug.debug(DEBUG, "flash(long,short )"+ str(long) +" "+ str(short) +"   " , "Flash Message", LOGTOFILE)

    if(long>0):
        # This is a fatal error and the program must be restarted
        # to recover from this error

        while True:
            blink.flash(ledPin,long,short)
    else:
        blink.flash(ledPin,long,short)
        

# End of method Definitions.

# Start a new thread for Lora Communications and button monitoring
# mainHouse thread runs Web Server.
_thread.start_new_thread(subprocess.subMain,())

# Main Program Loop
def mainLoop():
    loopCount=0
    counters.openCount=0

    # Make sure LED is off.
    led.off()

    # Connect to the wifi access point specified in secerts.py
    connectToWifi()

    # Set the local clock from the internet using the ntp protocol. 
    setLocalClock()

    while True:
        # Incoming Messages Events handeled in "cb(events)"
        # Event Reset button monitored in checkButtonPress()
    
        loopCount=loopCount+1

        if(DEBUG >=1):
            debug.debug(DEBUG, "mainLoop()        ", "Main While Loop Count="+str(loopCount), LOGTOFILE)
        
        # Listen for connections on port 80
        webServer.main(sta_if,ip)

mainLoop()