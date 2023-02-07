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
import gc

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
previousHeartBeat=0     # Used to chech how long since the last Heart Beat was received

# Pin Definitions
ledPin = 5                              # Physical Pin 7  Gnd = 8
led = Pin(ledPin, Pin.OUT)              # Define pin as output 
#button =  Pin(14, Pin.IN, Pin.PULL_UP)  # Physical Pin 19 Gnd = 13
buzzer = PWM(Pin(13))                   # Physical pin 17 Gnd = 18

if(DEBUG >=1):
    debug.debug(DEBUG, "Subprocess Init", "Pre Method Definitions" , LOGTOFILE)

# Method Definitions
# =========================================

def playTone(frequency):
    if(DEBUG >=1):
        debug.debug(DEBUG, "playTone(frequency)", "frequency=" + str(frequency), LOGTOFILE)

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
	        debug.debug(DEBUG, "processMessage(msg,err)    ", "Message Received=" + str(msg), LOGTOFILE)
		debug.debug(DEBUG, "processMessage(msg,err)    ", "msg type="+ str(type(msg)), LOGTOFILE)
        if(DEBUG >=2):
	     debug.debug(DEBUG, "processMessage(msg,err)    ", "err="+ str(err), LOGTOFILE)

    decryptedMessage=encryption.decryptMessage(msg)     # Decrypt the message 
    decodedMsg=decryptedMessage.decode()                # Decode the byte string into a string
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(msg,err)    ", "decodedMsg="+ str(decodedMsg), LOGTOFILE)
    if(DEBUG >=1):    
        debug.debug(DEBUG, "processMessage(msg,err)    ", "decodedMsg type="+ str(type(decodedMsg)), LOGTOFILE)   
    # Load incoming message into a json object
    jsonDict=json.loads(decodedMsg)
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(msg,err)    ", "jsonDict=" + str(jsonDict), LOGTOFILE)
        debug.debug(DEBUG, "processMessage(msg,err)    ", "jsonDict type=" + str(type(jsonDict)), LOGTOFILE)

    # Check destination of this message = this device
    # LoRa messages are broadcast and any device can pick them up

    destination = jsonDict["DstDevice"]
    
    if(DEBUG >=1):
        debug.debug(DEBUG, "processMessage(msg,err)", "destination="+destination, LOGTOFILE)
        debug.debug(DEBUG, "processMessage(msg,err)", "DSTDEVICE="+DSTDEVICE, LOGTOFILE)

    # Don't forget the device SRCDEVICE is the name of this machine (receiving the message)
    if(destination == SRCSTDEVICE): 
        compareTimeStamps(jsonDict)
        checkGateStatus(jsonDict)
        checkHeartBeat(jsonDict)
        
def checkHeartBeat(jsonDict):
    if(DEBUG >=1):
        debug.debug(DEBUG, "cHeckHeartBeat(jsonDict)", " ", LOGTOFILE)

    # 'TextMessage': 'Heart Beat',

    textMessage = jsonDict["TextMessage"] 
    if(textMessage=="Heart Beat"):
        # Get current hour
        now=time.localtime()
        #  Get the current hour
        hour=int(now[3])

        # If Previous Hour = 0
            # Save current hour as previous hour
        # Else
            # if Current hour >= Previous hour +1
                # Save current hour as previous hour
            # esle
                # display error message
                # 1 long, 5 short = Heartbeat message timed out
                
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
    if(DEBUG >=1):
        debug.debug(DEBUG, "checkGateStatus(jsonDict)    ", "gateOpen="+ str(gateOpen), LOGTOFILE)

    # If open play tone
    if(gateOpen=="True"):
        playTone(constants.HZ)
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
    #print("main() Subprocess mem before gc="+ str(gc.mem_free()))
    gc.collect()
    #print("main() Subprocess mem after gc="+ str(gc.mem_free()))

    if(DEBUG >=1):
        debug.debug(DEBUG, "subprocess.subMain()", "Start....", LOGTOFILE)

    loraMessage.sx.setBlockingCallback(False, cb)
    while True:
        if(counters.openCount>0):        # Show the number of gate open events
            blink.flash(mainHouse.ledpin, 0,counters.openCount)
        if(DEBUG >=1):
            debug.debug(DEBUG, "subprocess.subMain()", "openCount="+ str(counters.openCount) , LOGTOFILE)

        blink.checkButtonPress(5)

if(DEBUG >=1):
    debug.debug(DEBUG, "Subprocess Init", "End Method Definitions" , LOGTOFILE)
