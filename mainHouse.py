# This file (mainHouse.py) is executed on the HOUSE Device
# Rename to main.py so it executes at startup
# Intended to run on a Raspberry Pi Pico W (wifi)
# ==========================================
# <TODO>
# # Lora Message fails to send when Encrpytion=True
# I suspect this is a memory/resource problem

# Notes
# The Lora Connection and configuration is based on an this example.
# https://github.com/ehong-tl/micropySX126X
#
# Save the following files to the root folder of the pico same location as main.py
# sx1262.py, sx126x.py, _sx126x.py

# Network Connection and sntp time settings modified from example found here
# https://gist.github.com/aallan/581ecf4dc92cd53e3a415b7c33a1147c
# Threading implementation is based on this example
# https://circuitdigest.com/microcontroller-projects/dual-core-programming-on-raspberry-pi-pico-using-micropython
# =========================================================================
# Asked a question re Recursion Limit Error
# https://stackoverflow.com/questions/75257342/micropython-runtimeerror-maximum-recursion-depth-exceeded

from gc import mem_free, collect

#print("main() mem before gc="+ str(mem_free()))
collect()
#print("main() mem after gc="+ str(mem_free()))

from network import WLAN, STA_IF
from time import sleep
from _thread import start_new_thread, stack_size
from machine import Pin, PWM, #ADC

# Home baked imports
import ntpClientTZ  # Modified ntpClient to include Time Zone adjustment.
import subprocess   # Methods that are run in Thread 2
import debug        # My debuging routine
import secrets      # file Encryption key and IV values
import secretsHouse # file containing wifi ssid and password 
import dateTime     # My Date Time formatting routine
import blink        # Flash and Flash reset routine
import constants    # Constants used on all devices
import counters     # Counter variables shared between modules
import webServer    # Publish the web page and listen for connections

# Constants
DEBUG = constants.DEBUG
LOGTOFILE =  constants.LOGTOFILE
LOGFILENAME = constants.LOGFILENAME
CLEARDEBUG = constants.CLEARDEBUG
CLEARDEBUGPAUSE = constants.CLEARDEBUGPAUSE
ENCRYPTION = constants.ENCRYPTION
TIMEZONE = constants.TIMEZONE      # Set to your time zone +or- hours from UTC  (No Summertime)
NTPSERVER = constants.NTPSERVER    # change to a time server pool in your local area
TIMESETHALT = constants.TIMESETHALT
# Network Variables
ip=""                   # Global variable to hold the wifi connection IP address
sta_if = WLAN(STA_IF)  # Set the network interface name

# Pin Definitions
ledPin = 5                              # Physical Pin 7  Gnd = 8
led = Pin(ledPin, Pin.OUT)              # Define pin as output 
#button =  Pin(14, Pin.IN, Pin.PULL_UP)  # Physical Pin 19 Gnd = 13
buzzer = PWM(Pin(13))                   # Physical pin 17 Gnd = 18

debug.clearDebug()  # Clear debug file if CLEARDEBUG is True

# Start a new counter each time the program starts
if(DEBUG >=2):
    debug.debug(DEBUG, "Init", "Pre Reset Debug Counter" , LOGTOFILE)
debug.resetCounter()
if(DEBUG >=2):
    debug.debug(DEBUG, "Init", "Pre Method Defintions" , LOGTOFILE)

# Method Definitions
# =========================================
def connectToWifi():
    global ip
    global sta_if
    
    if(DEBUG >=1):
        debug.debug(DEBUG, "connectToWifi()", "Connecting to WIFI " + secretsHouse.ssid, LOGTOFILE)

    connectCount=0
    sta_if = WLAN(STA_IF)
    # Set your SSID and Password in secrets<Device>.py
    sta_if.active(True)                               # Activate the interface

    while connectCount<=5:
        try:
            sta_if.connect(secretsHouse.ssid, secretsHouse.password)    # Connect
        except Exception as errorMsg:
           if(DEBUG >=0):
               debug.debug(DEBUG, "connectToWifi()", "Unable to connect to WIFI: Error=" + str(errorMsg), LOGTOFILE)
        sleep(10)
        # Test if network is connected
        if not(sta_if.isconnected()):
            connectCount=connectCount+1
            if(DEBUG >=1):
                debug.debug(DEBUG, "connectToWifi()", "Connecting to WIFI, Fail Count=" + str(connectCount) , LOGTOFILE)
        else:
            connectCount=6

    if not(sta_if.isconnected()):
        if(DEBUG >=0):
            debug.debug(DEBUG, "connectToWifi()", "Connect to Network: Failed:" + str(connectCount), LOGTOFILE)
        # Error indication on LED
        flash(1,2)  # Fatal error, no return from this

    if(DEBUG >=1):
        ip=sta_if.ifconfig()[0]
        debug.debug(DEBUG, "connectToWifi()", "Connected to WIFI, IP="+str(ip), LOGTOFILE)
        sleep(5)

def setLocalClock():
    # Retrieve Time from smtp and set local clock
    if(DEBUG >=1):
        debug.debug(DEBUG, "setLocalClock()", " ", LOGTOFILE)
        timeStamp=str(dateTime.formattedTime())
        debug.debug(DEBUG, "setLocalClock()", "Time before ntp update=" + str(timeStamp), LOGTOFILE)
        dateStamp=str(dateTime.formattedDate())
        debug.debug(DEBUG, "setLocalClock()", "Date before ntp update=" + str(dateStamp), LOGTOFILE)

    if(DEBUG >=1):
        debug.debug(DEBUG, "setLocalClock()", "TIMEZONE="+str(TIMEZONE), LOGTOFILE)
        debug.debug(DEBUG, "setLocalClock()", "NTPSERVER="+str(NTPSERVER), LOGTOFILE)

    timeSetCount=0
    while (timeSetCount <=10):
        try:     
            ntpClientTZ.setTime(TIMEZONE, NTPSERVER, DEBUG, LOGTOFILE)
            timeSetCount=11  #Exit while loop

        except Exception as errorMsg:
            timeSetCount = timeSetCount +1
            if(DEBUG >=0):
                debug.debug(DEBUG, "setLocalClock()", "Unable to Set Time From Network: Try=" + str(timeSetCount) +" Error=" + str(errorMsg), LOGTOFILE)
 
            if(timeSetCount >=10):
                if(TIMESETHALT == True):
                    flash(1,3)  # Fatal error, no return from this

    if(DEBUG >=1):
        timeStamp=str(dateTime.formattedTime())
        debug.debug(DEBUG, "setLocalClock()", "Time after ntp update=" + str(timeStamp), LOGTOFILE)
        dateStamp=str(dateTime.formattedDate())
        debug.debug(DEBUG, "setLocalClock()", "Date after ntp update=" + str(dateStamp), LOGTOFILE)

def flash(long, short):
    # Flash the LED to indicate a gate open event or error
    #=====================================================
    # short flash only, indicates the number of gate openes since
    # the last reset (Manual button to reset).

    # Flash the LED to Indicate an error Long flash then Short flashe(s).
    # 1 long, 1 short = Low voltage at mainGate.py (Less than value set in constants.py)
    # 1 long, 2 short = Unable to connect to Wifi at mainHouse.py
    # 1 long, 3 short = Unable to set system clock at mainHouse.py
    # 1 long, 4 short = Unable to open socket for inbound web page connection
    # 1 long, 5 short = Heartbeat message timed out
    
    if(DEBUG >=2):
        debug.debug(DEBUG, "flash(long,short )"+ str(long) +" "+ str(short) +"   " , "Flash Message", LOGTOFILE)

    if(long>0):
        # This indicates a fatal error and the program must be restarted
        # to recover from this type of error

        while True:
            blink.flash(ledPin,long,short)
    else:
        blink.flash(ledPin,long,short)
        
if(DEBUG >=2):
    debug.debug(DEBUG, "Init", "End of Method Definition" , LOGTOFILE)

# End of method Definitions.

# Start a new sub thread for Lora Communications and button monitoring
# The main thread runs the Web Server.
stack_size(6*1024)   # Default stack size for thread two is only 4k

if(DEBUG >=1):
    debug.debug(DEBUG, "Init", "Pre Main" , LOGTOFILE)
#print("Init Pre Main mem before gc="+ str(mem_free()))
collect()
#print("Init Pre Main mem after gc="+ str(mem_free()))

if(DEBUG >=1):
    debug.debug(DEBUG, "Init", "Post Start Thread Two" , LOGTOFILE)

# Main Program Loop
def mainLoop():
    if(DEBUG >=2):
        debug.debug(DEBUG, "mainLoop()", " ", LOGTOFILE)

    loopCount=0
    counters.openCount=0

    # Make sure LED is off.
    led.off()

    # Connect to the wifi access point specified in secerts.py
    connectToWifi()

    # Set the local clock from the internet using the ntp protocol. 
    setLocalClock()

    # Start thread two
    start_new_thread(subprocess.subMain,())

    while True:
        # Incoming Messages Events handeled in "subprocess.cb(events)"
        # Event Reset button monitored in checkButtonPress()
    
        loopCount=loopCount+1

        if(DEBUG >=2):
            debug.debug(DEBUG, "mainLoop()", "Main While Loop Count="+str(loopCount), LOGTOFILE)
        
        # Listen for connections on port 80
        webServer.main(sta_if,ip)

mainLoop()
    
