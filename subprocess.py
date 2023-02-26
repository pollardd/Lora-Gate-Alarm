# Sub Procss runs in a Seperate Thread on Processor Core II
# Keep the SX1262 import at the top to avoid suspected
# memory fragmentation problems

import gc
print("subprocess() mem before gc="+ str(gc.mem_free()))
gc.collect()
print("subprocess() mem after gc="+ str(gc.mem_free()))

from sx1262 import SX1262    #Lora Library
import _sx126x
from machine import Pin, PWM
import time
import utime
import machine
import json
import _thread
sLock = _thread.allocate_lock()

# Home baked imports
import debug        # My debuging routine
import constants    # Constants used on all devices
import counters     # Counter variables shared between modules
import dateTime     # My Date Time formatting routine
import blink        # Reuseable code to flash the LED error messages or open gate count
import loraMessage  # Standard encoding of json formatted message
import encryption   # Encrypt and Decrypt routines

# Constants
DEBUG = constants.DEBUG
LOGTOFILE =  constants.LOGTOFILE
ENCRYPTION = constants.ENCRYPTION

SRCDEVICE="MainHouse"              # Names used in Debug Output
DSTDEVICE="MainGate"               #  

messageNumber=10000     # Sequential message number.  (mainGate.py starts at 1)
gateOpen="False"        # mainHouse device does not monitor the gate
batteryPercent=0        # mainHouse device is always connected to mains power supply
mainGateHeartBeat=0     # Used to chech how long since the last Heart Beat was received
mainGateFileName="batteryLevel.txt"    # Holds the Battery level percentage and last update time

# Pin Definitions
ledPin = 5                               # Physical Pin 7  Gnd = 8
led = Pin(ledPin, Pin.OUT)               # Define pin as output 
#button =  Pin(14, Pin.IN, Pin.PULL_UP)  # Physical Pin 19 Gnd = 13
buzzer = PWM(Pin(13))                    # Physical pin 17 Gnd = 18

if(DEBUG >=1):
    debug.debug(DEBUG, "Subprocess Init", "Pre Method Definitions" , LOGTOFILE)

# Method Definitions
# =========================================

def playTone(volume, lowFrequency, highFrequency, delay, repeat):
    if(DEBUG >=1):
        debug.debug(DEBUG, "playTone()", "", LOGTOFILE)

    #  These values set in constants.py work on a speaker salvaged out of a telephone handset
    #  You may need to play around with it to suit your requirements

    if(DEBUG >=1):
        debug.debug(DEBUG, "playTone()", "volume="+str(volume), LOGTOFILE)
        debug.debug(DEBUG, "playTone()", "lowFrequency="+str(lowFrequency), LOGTOFILE)
        debug.debug(DEBUG, "playTone()", "highFrequency="+str(highFrequency), LOGTOFILE)
        debug.debug(DEBUG, "playTone()", "delay="+str(delay), LOGTOFILE)
        debug.debug(DEBUG, "playTone()", "repeat="+str(repeat), LOGTOFILE)

    # Play tone
    while(repeat >= 1):
        if(DEBUG >=1):
            debug.debug(DEBUG, "playTone()", "Repeat="+str(repeat), LOGTOFILE)

        # Set volume
        buzzer.duty_u16(volume) 
        # Make a sound
        buzzer.freq(highFrequency)
        time.sleep(delay)
        # Set minimum volume
        buzzer.duty_u16(0)
        # Pause between two tones
        time.sleep(delay/4)

        # Make another sound

        # Set volume
        buzzer.duty_u16(volume)
        # Make a sound
        buzzer.freq(lowFrequency)
        time.sleep(delay)
        # Set minimum volume
        buzzer.duty_u16(0)
        
        # Pause between sound pairs
        time.sleep(delay)
        repeat=repeat-1
    
# This method handles incoming messages
# It is also triggered on outgoing messages
def cb(events):
    if(DEBUG >=1):
        debug.debug(DEBUG, "cb(events()", "Lora Event Initiated", LOGTOFILE)

    if events & SX1262.RX_DONE:
        message, err = loraMessage.sx.recv()
        error = SX1262.STATUS[err]
        processMessage(message, err)
    elif events & SX1262.TX_DONE:  # Local Transmit has been performed
        if(DEBUG >=1):
            debug.debug(DEBUG, "cb(events()", "TX Done", LOGTOFILE)

def processMessage(message,err):
    # Process the incoming message
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(message,err)", "Message Received=" + str(message), LOGTOFILE)
        debug.debug(DEBUG, "processMessage(message,err)", "message type="+ str(type(message)), LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(message,err)", "err="+ str(err), LOGTOFILE)

    if(constants.ENCRYPTION == True): 
        message=encryption.decryptMessage(message)          # Decrypt the message 

    message=message.decode()                                # Decode the byte string into a string

    if(DEBUG >=1):
        debug.debug(DEBUG, "processMessage(message,err)", "Decoded Message="+ str(message), LOGTOFILE)
    if(DEBUG >=1):    
        debug.debug(DEBUG, "processMessage(message,err)", "Decoded Message type="+ str(type(message)), LOGTOFILE)   
    # Load incoming message into a json object
    jsonDict=json.loads(message)
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(message,err)", "jsonDict=" + str(jsonDict), LOGTOFILE)
        debug.debug(DEBUG, "processMessage(message,err)", "jsonDict type=" + str(type(jsonDict)), LOGTOFILE)

    # Check destination of this message = this device
    # LoRa messages are broadcast and any device can pick them up

    destination = jsonDict["DstDevice"]
    
    if(DEBUG >=1):
        debug.debug(DEBUG, "processMessage(message,err)", "destination="+destination, LOGTOFILE)

    # Don't forget the device constant SRCDEVICE is the name of this machine (receiving the message)
    if(destination == SRCDEVICE): 
        compareTimeStamps(jsonDict)
        checkGateStatus(jsonDict)
        saveHeartBeat(jsonDict)
        checkBatteryPercent(jsonDict)

def checkBatteryPercent(jsonDict):
    batteryPercent=float(jsonDict["BatteryPercent"])
    minBattery=float(constants.MINBATTERY)

    if(DEBUG >=1):
        debug.debug(DEBUG, "CheckBatteryPercent()", "batteryPercent="+str(batteryPercent), LOGTOFILE)
        debug.debug(DEBUG, "CheckBatteryPercent()", "minBattery="+str(minBattery), LOGTOFILE)

    # Save Battery Values to file to be read from the webserver (main thread)
    # First line = battery percentage and Second Line is the time stamp
    # No history is stored the previous values are simply overwritten
    sLock.acquire()
    fileHandle = open(mainGateFileName,"w")
    fileHandle.write(str(batteryPercent))
    fileHandle.write("\n")
    fileHandle.write(str(time.localtime()))
    fileHandle.close()
    sLock.release()

    if(batteryPercent <= minBattery):
        if(DEBUG >=1):
            debug.debug(DEBUG, "CheckBatteryPercent()", "LowBattery Warning="+str(minBattery)+"%", LOGTOFILE)
            debug.debug(DEBUG, "CheckBatteryPercent()", "Current Battery Level="+str(batteryPercent)+"%", LOGTOFILE)

        # Flash error message
        blink.flash(ledPin,1,1)

def saveHeartBeat(jsonDict):
    if(jsonDict["TextMessage"]=="Heart Beat"):
        global mainGateHeartBeat
        if(DEBUG >=1):
            debug.debug(DEBUG, "saveHeartBeat()", "Store Heartbeat", LOGTOFILE)

        if(jsonDict["SrcDevice"]=="MainGate"):
            if(DEBUG >=1):
                debug.debug(DEBUG, "saveHeartBeat()", "Old mainGateHeartBeat="+str(mainGateHeartBeat), LOGTOFILE)

            # Get current time
            mainGateHeartBeat=time.localtime()

            if(DEBUG >=1):
                debug.debug(DEBUG, "saveHeartBeat()", "New mainGateHeartBeat="+str(mainGateHeartBeat), LOGTOFILE)

    
def checkHeartBeat():
    if(DEBUG >=2):
        debug.debug(DEBUG, "checkHeartBeat()", "Check age of last heart beat", LOGTOFILE)

    global mainGateHeartBeat
    
    # Get current time from the local clock
    now=time.localtime()
        
    # get the number of seconds between the two time tupples
    seconds=utime.mktime(now)-utime.mktime(mainGateHeartBeat)
    if(DEBUG >=2):
        debug.debug(DEBUG, "checkHeartBeat()", "Heart beat age in seconds="+ str(seconds) , LOGTOFILE)
        debug.debug(DEBUG, "checkHeartBeat()", "Max Heart beat age in seconds="+ str(constants.MAXHEARTBEAT) , LOGTOFILE)

    #Check age of HeartBeart
    if(seconds > constants.MAXHEARTBEAT):
        # display error message
        # 1 long, 5 short = Heartbeat message timed out
        blink.flash(ledPin,1,5)
        # Note no return from errors with one long flash
    
def compareTimeStamps(jsonDict):
    if(DEBUG >=1):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)", "jsonDict="+ str(jsonDict), LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)", "jsonDict type=" + str(type(jsonDict)), LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)", "jsonDict="+ str(jsonDict), LOGTOFILE)

    remoteTimeStamp = jsonDict["TimeStamp"] # Return just the time field from the remote communication string  
    if(DEBUG >=1):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)", "remoteTimeStamp="+ str(remoteTimeStamp), LOGTOFILE)

    localTimeStamp = time.localtime()[:5]  # Return local system time (YYYY,MM,DD,HH,MM)
    if(DEBUG >=1):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)", "localTimeStamp="+ str(localTimeStamp), LOGTOFILE)
    
    remoteTimeStampShort= eval(remoteTimeStamp)[:5]  # Convert String to tuple
    if(DEBUG >=1):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)", "remoteTimeStampShort="+ str(remoteTimeStampShort), LOGTOFILE)

    if(localTimeStamp!=remoteTimeStampShort):
        if(DEBUG >=1):
            debug.debug(DEBUG, "compareTimeStamps(jsonDict)", "Time out by more than one minute", LOGTOFILE)
        
        sendTimeUpdate()
        
def checkGateStatus(jsonDict):
    if(DEBUG >=1):
        debug.debug(DEBUG, "checkGateStatus(jsonDict)", "jsonDict="+ str(jsonDict), LOGTOFILE)

    gateOpen=jsonDict["GateOpen"]    # Read the GateOpen: string out of the json message
    if(DEBUG >=1):
        debug.debug(DEBUG, "checkGateStatus(jsonDict)", "gateOpen="+ str(gateOpen), LOGTOFILE)

    # If open play tone
    if(gateOpen=="True"):
        playTone(constants.VOLUME, constants.LOWFREQUENCY, constants.HIGHFREQUENCY, constants.DELAY, constants.REPEAT)

        # Count the number of gate open events
        counters.openCount = counters.openCount+1
        if(DEBUG >=1):
            debug.debug(DEBUG, "checkGateStatus(jsonDict)", "counters.openCount="+ str(counters.openCount), LOGTOFILE)
        
def sendTimeUpdate():
    global SRCDEVICE
    global DSTDEVICE
    global messageNumber
    messageNumber = messageNumber+1
    timeStamp = time.localtime()
    timeUpdate="True"
    textMessage="Time Update"
    gateOpen="NA"

    if(DEBUG >=1):
        debug.debug(DEBUG, "sendTimeUpdate()" + str(timeStamp), "Send Json text string to " + DSTDEVICE , LOGTOFILE)
    
    message = loraMessage.buildLoraMessage(messageNumber,SRCDEVICE,DSTDEVICE,timeStamp,timeUpdate,batteryPercent,gateOpen,textMessage)
    if(DEBUG >=2):
        debug.debug(DEBUG, "sendTimeUpdate()", "Message=" + str(message), LOGTOFILE)

    message=bytes((message).encode())
    if(ENCRYPTION == True):
        message=encryption.encryptMessage(message)
        
    loraMessage.sx.send(message)
 
# End of method Definitions.

def subMain():
    global mainGateHeartBeat

    print("subMain() Subprocess mem before gc="+ str(gc.mem_free()))
    gc.collect()
    print("subMain() Subprocess mem after gc="+ str(gc.mem_free()))

    if(DEBUG >=1):
        debug.debug(DEBUG, "subprocess.subMain()", "Start....", LOGTOFILE)
    
    # Set the initial heart beat time
    mainGateHeartBeat=time.localtime()
    
    loraMessage.sx.setBlockingCallback(False, cb)
    while True:
        if(counters.openCount>0):        # Show the number of gate open events
            blink.flash(ledPin, 0,counters.openCount)
        
        if(DEBUG >=2):
            debug.debug(DEBUG, "subprocess.subMain()", "openCount="+ str(counters.openCount) , LOGTOFILE)
        blink.checkButtonPress(3)
        
        # Check if the previous mainGateHeartBeat is not more than one hour old
        checkHeartBeat()

# This message is displayed after all the methods have been defined
# and before the main method is called
if(DEBUG >=1):
    debug.debug(DEBUG, "Subprocess Init", "End Method Definitions" , LOGTOFILE)
