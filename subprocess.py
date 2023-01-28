# Sub Procss runs in a Seperate Thread on Processor Core II
# Keep the SX1262 import at the top to avoid suspected
# memory fragmentation problems

from sx1262 import SX1262    #Lora Library
import _sx126x
from machine import Pin, PWM
import time
import machine
import json
import _thread

# Receiving error
# RuntimeError: maximum recursion depth exceeded
# Tried this
# _thread.stack_size(16 * 1024)

# Home baked imports
import debug        # My debuging routine
import constants    # Constants used on all devices
import counters     # Counter variables shared between modules
import dateTime     # My Date Time formatting routine
import blink        # Reuseable code to flash the LED error messages or open gate count
import loraMessage  # Standard encoding of json formatted message

# Constants
DEBUG = constants.DEBUG
LOGTOFILE =  constants.LOGTOFILE
ENCRYPTION = constants.ENCRYPTION

SRCDEVICE="MainHouse"              # Names used in Debug Output
DSTDEVICE="MainGate"               #  

messageNumber=10000     # Sequential message number.  (mainGate.py starts at 1)
gateOpen="False"        # mainHouse device does not monitor the gate
batteryPercent=0        # mainHouse device is always connected to mains power supply

# Pin Definitions
ledPin = 5                              # Physical Pin 7  Gnd = 8
led = Pin(ledPin, Pin.OUT)              # Define pin as output 
#button =  Pin(14, Pin.IN, Pin.PULL_UP)  # Physical Pin 19 Gnd = 13
buzzer = PWM(Pin(13))                   # Physical pin 17 Gnd = 18

# Method Definitions
# =========================================

def playTone(frequency):
    if(DEBUG >=1):
        debug.debug(DEBUG, "playTone(frequency)    ", "frequency=" + str(frequency), LOGTOFILE)

    #  These values work on a speaker stolen out of a telephone handset
    #  You may need to play around with it to suit your requirements

    # Set maximum volume
    buzzer.duty_u16(40000) #40000 seems to be maximum volume
    # Play tone
    buzzer.freq(frequency)

def stopTone():
    if(DEBUG >=1):
        debug.debug(DEBUG, "stopTone()    ", "Lora Event Initiated", LOGTOFILE)

    # Set minimum volume
    buzzer.duty_u16(0)

# This method handles incoming messages
# It is also triggered on outgoing messages
def cb(events):
    if(DEBUG >=1):
        debug.debug(DEBUG, "cb(events()    ", "Lora Event Initiated", LOGTOFILE)

    if events & SX1262.RX_DONE:
        msg, err = loraMessage.sx.recv()
        error = SX1262.STATUS[err]
        processMessage(msg, err)
    elif events & SX1262.TX_DONE:  # Local Transmit has been performed
        if(DEBUG >=1):
            debug.debug(DEBUG, "cb(events()    ", "TX Done", LOGTOFILE)

def processMessage(msg,err):
    # Process the incoming message
    if(DEBUG >=1):
        debug.debug(DEBUG, "processMessage(msg,err)    ", "msg="+ str(msg), LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(msg,err)    ", "msg type="+ str(type(msg)), LOGTOFILE)
        debug.debug(DEBUG, "processMessage(msg,err)    ", "err="+ str(err), LOGTOFILE)

    decryptedMessage=encryption.decryptMessage(msg)  # Decrypt the message 
    decodedMsg=decryptedMessage.decode()              # Decode the byte string into a string

    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(msg,err)    ", "decodedMsg="+ str(decodeMsg), LOGTOFILE)
        debug.debug(DEBUG, "processMessage(msg,err)    ", "decodedMsg type="+ str(type(decodedMsg)), LOGTOFILE)

    jsonDict=json.loads(decodedMsg)  # Load string into a json object
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(msg,err)    ", "jsonDict=" + str(jsonDict), LOGTOFILE)
        debug.debug(DEBUG, "processMessage(msg,err)    ", "jsonDict type=" + str(type(jsonDict)), LOGTOFILE)

    compareTimeStamps(jsonDict)
    checkGateStatus(jsonDict)

def compareTimeStamps(jsonDict):
    if(DEBUG >=1):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)    ", "jsonDict="+ str(jsonDict), LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)    ", "jsonDict type=" + str(type(jsonDict)), LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)   ", "jsonDict="+ str(jsonDict), LOGTOFILE)

    remoteTimeStamp = jsonDict["TimeStamp"] # Return just the time field from the remote communication string  
    if(DEBUG >=1):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)   ", "remoteTimeStamp="+ str(remoteTimeStamp), LOGTOFILE)

    localTimeStamp = time.localtime()[:5]  # Return local system time (YYYY,MM,DD,HH,MM)
    if(DEBUG >=1):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)   ", "localTimeStamp="+ str(localTimeStamp), LOGTOFILE)
    
    remoteTimeStampShort= eval(remoteTimeStamp)[:5]  # Convert String to tuple
    if(DEBUG >=1):
        debug.debug(DEBUG, "compareTimeStamps(jsonDict)   ", "remoteTimeStampShort="+ str(remoteTimeStampShort), LOGTOFILE)

    if(localTimeStamp!=remoteTimeStampShort):
        if(DEBUG >=1):
            debug.debug(DEBUG, "compareTimeStamps(jsonDict)   ", "Time out by more than one minute", LOGTOFILE)
        
        sendTimeUpdate()
        
def checkGateStatus(jsonDict):
    if(DEBUG >=1):
        debug.debug(DEBUG, "checkGateStatus(jsonDict)    ", "jsonDict="+ str(jsonDict), LOGTOFILE)

    gateOpen=jsonDict["GateOpen"]    # Read the GateOpen: string out of the json message
    if(DEBUG >=2):
        debug.debug(DEBUG, "checkGateStatus(jsonDict)    ", "gateOpen="+ str(gateOpen), LOGTOFILE)

    # If open play tone
    if(gateOpen=="True"):
        playTone(HZ)
        stopTone()
        # Count the number of gate open events
        counters.openCount = counters.openCount+1
        if(DEBUG >=1):
            debug.debug(DEBUG, "checkGateStatus(jsonDict)    ", "counters.openCount="+ str(counters.openCount), LOGTOFILE)
        
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
        debug.debug(DEBUG, "sendTimeUpdate() " + str(timeStamp), "Send Json text string to " + DSTDEVICE , LOGTOFILE)
    
    message = loraMessage.buildLoraMessage(messageNumber,SRCDEVICE,DSTDEVICE,timeStamp,timeUpdate,batteryPercent,gateOpen,textMessage)
    if(DEBUG >=2):
        debug.debug(DEBUG, "sendTimeUpdate()    ", "Message=" + str(message), LOGTOFILE)

    encodedMessage=bytes((message).encode())
    encryptedMessage=encryption.encryptMessage(encodedMessage)
    loraMessage.sx.send(encryptedMessage)
 
# End of method Definitions.

def subMain():
    if(DEBUG >=1):
        debug.debug(DEBUG, "subprocess.subMain()", "Start....", LOGTOFILE)

    loraMessage.sx.setBlockingCallback(False, cb)
    while True:
        if(counters.openCount>0):        # Show the number of gate open events
            flash(0,counters.openCount)
        if(DEBUG >=1):
            debug.debug(DEBUG, "subprocess.subMain()", "openCount="+ str(counters.openCount) , LOGTOFILE)

        blink.checkButtonPress(2)