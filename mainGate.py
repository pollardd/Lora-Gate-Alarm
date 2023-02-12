# mainGate.py
#  See more program details in mainHouse.py
#
# ===========================================================================
# Keep the SX1262 import at the top to avoid memory fragmentation problem
from sx1262 import SX1262   #Lora library
import _sx126x
from machine import ADC, Pin
import time
import dateTime
import json

# Home baked imports
import debug                # My Debug Routine
import loraMessage          # My standard encoding of json formatted Lora Gate message
import constants            # Constants used on all devices
import dateTime             # My Date time formatting routine
import secrets              # Security information required by remote device
import encryption           # Encrypt and Decrypt routines

DEBUG = constants.DEBUG
LOGTOFILE = constants.LOGTOFILE
ENCRYPTION = constants.ENCRYPTION

SRCDEVICE="MainGate"
DSTDEVICE="MainHouse"

TIMEUPDATE = "False"                # mainGate never updates time at mainHouse
FULLBATTERY = 4.05                  # these are our reference voltages for a full/empty battery, in volts (Determined using battery.py)
EMPTYBATTERY = 2.41                 # the values could vary by battery size/manufacturer so you might need to adjust them

# led = machine.Pin(LED, machine.Pin.OUT)    # Pico Wifi Board
led = machine.Pin(25, machine.Pin.OUT)       # Pico Non Wifi Board

vsys = ADC(26)                      # reads the system input voltage from Pico Lora Module
charging = Pin(24, Pin.IN)          # reading GP24 tells us whether or not USB power is connected
conversion_factor = 3 * 3.3 / 65535 # Converts the returned value to Volts

messageNumber=0             # Sequential LoRa message number.  (mainHouse.py starts at 10000)
startUp = True              # Send start up message immidately to mainHouse
led.off()                   # Make sure the led is off

# Pin Definitions
gateSwitch =  Pin(14, Pin.IN, Pin.PULL_UP)  # Physical Pin 19 Gnd = 18

# Start a new counter each time the program starts
debug.resetCounter()

# Method Defintions

# This method handles incoming messages
# It is also triggered on outgoing messages
def cb(events):
    if(DEBUG >=1):
        debug.debug(DEBUG, "cb(events()", "Lora Event Initiated", LOGTOFILE)

    # If Lora message received
    if events & SX1262.RX_DONE:
        message, err = loraMessage.sx.recv()
        error = SX1262.STATUS[err]
        if(DEBUG >=2):
            debug.debug(DEBUG, "cb(events()", "Message Rec.="+ str(message), LOGTOFILE)
            #print('Receive: {}, {}'.format(message, error))
        processMessage(message,err)

    # If Lora message sent
    elif events & SX1262.TX_DONE:
        if(DEBUG >=1):
            debug.debug(DEBUG, "cb(events()", "TX Done", LOGTOFILE)

def getBatteryPercentage():
    if(DEBUG >=1):
        debug.debug(DEBUG, "getBatteryPercentage()", "Retrieve battery power level", LOGTOFILE)

    voltage = vsys.read_u16() * conversion_factor
    batteryPercentage = 100 * ((voltage - EMPTYBATTERY) / (FULLBATTERY - EMPTYBATTERY))
    #if batteryPercentage > 100:  #If it's more than 100 then the empty full values are wrong
    #    batteryPercentage = 100.00
    return round(batteryPercentage,1)  # Just leave one decimal place

def getGateSwitch():
    # Invert the 1-0 so that 1=button pressed 0=not pressed
    return not gateSwitch.value()

def processMessage(message,err):
    # Process the incoming message
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(message,err)    ", "Message Received=" + str(message), LOGTOFILE)
        debug.debug(DEBUG, "processMessage(message,err)    ", "message type="+ str(type(message)), LOGTOFILE)
        debug.debug(DEBUG, "processMessage(message,err)    ", "err="+ str(err), LOGTOFILE)

    if(ENCRYPTION == True):
        message=encryption.decryptMessage(message)             # Decrypt the message

    message=message.decode()                                   # Decode the byte string into a string
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(message,err)    ", "Decoded Message="+ str(message), LOGTOFILE)
    if(DEBUG >=1):    
        debug.debug(DEBUG, "processMessage(message,err)    ", "Decodded Message type="+ str(type(message)), LOGTOFILE)   
    
    # Load incoming message into a json object
    jsonDict=json.loads(message)
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(message,err)    ", "jsonDict=" + str(jsonDict), LOGTOFILE)

    # Check destination of this message = this device
    # LoRa messages are broadcast and any device can pick them up

    destination = jsonDict["DstDevice"]
    
    if(DEBUG >=1):
        debug.debug(DEBUG, "processMessage(message,err)", "destination="+destination, LOGTOFILE)
        debug.debug(DEBUG, "processMessage(message,err)", "DSTDEVICE="+DSTDEVICE, LOGTOFILE)

    # Don't forget the device SRCDEVICE is the name of this machine (receiving the message)
    if(destination == SRCDEVICE): 
        if(jsonDict["TimeUpdate"] == "True"):
            updateTime(jsonDict)

def updateTime(jsonDict):
    if(DEBUG >=1):
        debug.debug(DEBUG, "updateTime()", " ", LOGTOFILE)

    newTimeStamp = jsonDict["TimeStamp"] # Return just the time stamp from the remote communication string  

    if(DEBUG >=2):
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "TimeStamp from mainGate=" + str(newTimeStamp), LOGTOFILE)

    # Time Before
    if(DEBUG >=2):
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "Local Time Before=" + str(time.localtime()), LOGTOFILE)

    newTime=(eval(newTimeStamp))   # Eval converts string to tuple
    if(DEBUG >=3):
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "NewTime=" + str(newTime), LOGTOFILE)
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "Year=" + str(newTime[0]), LOGTOFILE)
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "Month=" + str(newTime[1]), LOGTOFILE)
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "Day=" + str(newTime[2]), LOGTOFILE)
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "Hour=" + str(newTime[3]), LOGTOFILE)
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "Min=" + str(newTime[4]), LOGTOFILE)
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "Sec=" + str(newTime[5]), LOGTOFILE)
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "Week of Year=" + str(newTime[6]), LOGTOFILE)
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "Day Of Week=" + str(newTime[7]), LOGTOFILE)
        
    # Update Local Time
    machine.RTC().datetime((newTime[0], newTime[1], newTime[2], newTime[6], newTime[3], newTime[4], newTime[5], 0))

    # Time After
    if(DEBUG >=2):
        debug.debug(DEBUG, "setTime()    ", "Local Time After=" + str(time.localtime()), LOGTOFILE)

def sendJson(textMessage):
    if(DEBUG >=1):
        debug.debug(DEBUG, "sendJson()", " " + str(time.localtime()), LOGTOFILE)

    global messageNumber
    global gateOpen
    
    if(DEBUG >=2):
        debug.debug(DEBUG, "sendJson(textMessage)", "Send Json Text String="+ textMessage, LOGTOFILE)

    messageNumber = messageNumber+1
    timeStamp = time.localtime()
    batteryPercentage=getBatteryPercentage()
    
    message = loraMessage.buildLoraMessage(messageNumber,SRCDEVICE,DSTDEVICE,timeStamp,TIMEUPDATE,batteryPercentage,gateOpen,textMessage)
    if(DEBUG >=2):
        debug.debug(DEBUG, "sendJson(textMessage)", "Message=" + str(message), LOGTOFILE)

    message=bytes((message).encode())
    
    if(ENCRYPTION == True):
        message=encryption.encryptMessage(message)
        
    loraMessage.sx.send(message)

def startUpMessage():
    # Send Status message to mainHouse
    global gateOpen
    if(DEBUG >=1):
        debug.debug(DEBUG, "startUpMessage()", "Sent status message", LOGTOFILE)
    
    textMessage="StartUp Message"

    if(gateSwitch()==1):
        gateOpen="True"
    else:
        gateOpen="False"
    
    # Send the initial message to MainHouse
    sendJson(textMessage)
    
    # This delay following the sendJson command solves a weird
    # problem with the transmittion of the message to the remote device.
    # It only occures on the startup message when not running through Thonny.
    # Makes no sense to me.
    time.sleep(2)
    
    if(DEBUG >=1):
        debug.debug(DEBUG, "main()    ", "Startup Message Sent", LOGTOFILE)


# End of method Defintions.

# This is the line that enables the Lora routine to listen for incoming messages. cb(events)
# DP Not sure how it works.  Seems to run on a seperate process
loraMessage.sx.setBlockingCallback(False, cb)

if(DEBUG >=1):
    led.toggle()    #Turn on board LED on

if(DEBUG >=1):
    debug.debug(DEBUG, "mainloop()", " Local Time=" + str(time.localtime()), LOGTOFILE)

# Defind variable to avoid multiple messages in an hour
previousHour=""

while True:
    # Send initial startup message
    if(startUp):
        startUpMessage()
        startUp=False
    
    # Send heart beat message if the minutes are 00
    # i.e. once per hour on the hour.
    now=time.localtime()
    # Get the current hour in two digit format
    hour=dateTime.zfl(str(now[3]),2)
    # Get the current minute in two digit format
    minute=dateTime.zfl(str(now[4]),2)
    if(DEBUG >=2):
        debug.debug(DEBUG, "mainloop()", "Minute=" + str(minute), LOGTOFILE)

    if(minute == "00"):
        if(hour != previousHour):
            # Send Heart Beat Message
            if(DEBUG >=1):
                debug.debug(DEBUG, "main()", "Send Heart Beat Message " + str(now), LOGTOFILE)

            sendJson("Heart Beat")
            previousHour=hour

    # Only send a message if the gate status has changed
    # Look for gate open signal
    if(gateSwitch()==1 and gateOpen=="False"):
        gateOpen="True"
        # Send Gate Open Message
        if(DEBUG >=1):
            debug.debug(DEBUG, "main()    ", "The Gate is Open", LOGTOFILE)
        sendJson("Gate is Open")

    # If gate status has changed from open to closed
    if(gateSwitch()==0 and gateOpen=="True"):
        gateOpen="False"
        # Send Gate Closed Message 
        if(DEBUG >=1):
            debug.debug(DEBUG, "main()    ", "The Gate is Closed", LOGTOFILE)
        sendJson("Gate is Closed")
    
    # Don't loop to fast and waste power
    # How fast can a car get through with someone else opening and closing the gate?
    time.sleep(10)
    
    # Toggle the LED so we know the program is running
    # We see 10 seconds on and 10 seconds off
    if(DEBUG >=1):
        led.toggle()
    
