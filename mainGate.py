# mainGate.py
# See more program details in mainHouse.py
#
# <TODO>
# Include report to mainHouse of freespace using diskFree.py
# Done * Include gate angle in lora message 
#        Actually not much point as the message can trigger while the gate is moving.
#        Interesting anyway :)
# Update
# 19/03/2023  Added sx.standby(True) to save power when no messages are being sent or received
# ===========================================================================

# Keep the SX1262 import at the top to avoid memory fragmentation problem
from sx1262 import SX1262   #Lora library
import _sx126x
import constants            # Constants used on all devices
from machine import ADC, Pin
from time import mktime, sleep, localtime
from json import loads
from machine import Pin, RTC, lightsleep
from gc import mem_free, collect
from micropython import mem_info

# Home baked imports
import debug                  # My Debug Routine
import loraMessage            # My standard encoding of json formatted Lora Gate message
import dateTime               # My Date time formatting routine
import secrets                # Security information required by remote device
import encryption             # Encrypt and Decrypt routines
import picoTemp               # Return local pico internal tempreature
from diskFree import diskFree # Reports on the amount of free files system storage in KB.

DEBUG = constants.DEBUG
LOGTOFILE = constants.LOGTOFILE
LOGFILENAME = constants.LOGFILENAME
CLEARDEBUG = constants.CLEARDEBUG
CLEARDEBUGPAUSE = constants.CLEARDEBUGPAUSE
ENCRYPTION = constants.ENCRYPTION
LORASTANDBY = constants.LORASTANDBY
GATEANGLETHRESHOLD = constants.GATEANGLETHRESHOLD
LOWPOWERMODE = constants.LOWPOWERMODE

SRCDEVICE="MainGate"
DSTDEVICE="MainHouse"
GATESENSOR=constants.GATESENSOR

# Used by Magnetometer
# https://core-electronics.com.au/guides/piicodev-magnetometer-qmc6310-guide-for-raspberry-pi-pico/
if (GATESENSOR=="Magnetometer"):
    from PiicoDev_QMC6310 import PiicoDev_QMC6310
    from PiicoDev_Unified import sleep_ms          # Cross-platform compatible sleep function
    compass = PiicoDev_QMC6310(range=800)          # Initialise the sensor with 800uT range. Valid ranges: 200, 800, 1200, 3000 uT

TIMEUPDATE = "False"                # mainGate never updates time at mainHouse
FULLBATTERY = 4.1                   # these are our reference voltages for a full/empty battery, in volts (Determined using battery.py)
#                                   # The values could vary by battery size/manufacturer so you might need to adjust them depending on your battery
# EMPTYBATTERY = 2.5                # 46.0% when execution stopped
# EMPTYBATTERY = 2.41               # 41.4% when execution stopped    
# EMPTYBATTERY = 1.00               # 56.5% and 55.4% when execution stopped
EMPTYBATTERY = 2.5
SLEEPTIME = 10                      # Sleep time waiting for gate open on GPIO

# led = Pin(LED, Pin.OUT)              # Pico Wifi Board
led = Pin(25, Pin.OUT)                 # Pico Non Wifi Board

# NOTE: Connect a momentary switch to the RUN pin (#30) and to any GND pin
# This will restart the Pico when the button is pressed and and record the current gate position as the closed position.

vsys = ADC(26)                         # reads the system input voltage from Pico Lora Module
charging = Pin(24, Pin.IN)             # reading GP24 tells us whether or not USB power is connected
conversion_factor = 3 * 3.3 / 65535    # Converts the returned value to Volts

messageNumber=0                        # Sequential LoRa message number.  (mainHouse.py starts at 10000)
startUp = True                         # Send start up message immidately to mainHouse
led.off()                              # Make sure the led is off
mainGateHeartBeat = localtime()        # Counts the number of seconds since last heartbeat sent

# Pin Definitions
gateSwitch =  Pin(14, Pin.IN, Pin.PULL_UP)  # Physical Pin 19 Gnd = 18

# Clear Debug Log if constants CLEARDEBUG set to True
debug.clearDebug()

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
        if(DEBUG >=2):
            debug.debug(DEBUG, "cb(events()", "TX Done", LOGTOFILE)

#def temperature():
#    temperature_value = sensor_temp.read_u16() * conversion_factor 
#    temperature_Celcius = 27 - (temperature_value - 0.706)/0.00172169/ 8 
#    if(DEBUG >=1):
#        debug.debug(DEBUG, "mainGate.temperature()        ", "Temp="+str(temperature_Celcius),LOGTOFILE)
#    sleep(1)
#    return temperature_Celcius

def getHeadingDiff(init, final):
    if(DEBUG >=2):
        debug.debug(DEBUG, "getHeadingDiff(init, final)", "Start", LOGTOFILE)

    if init > 360 or init < 0 or final > 360 or final < 0:
        raise Exception("out of range")
    diff = final - init
    absDiff = abs(diff)

    if absDiff == 180:
        result = absDiff
    elif absDiff < 180:
        result = diff
    elif final > init:
        result = absDiff - 360
    else:
        result = 360 - absDiff
        
    return abs(result)

def getBatteryPercentage(voltage):
    if(DEBUG >=2):
        debug.debug(DEBUG, "getBatteryPercentage()", "Start", LOGTOFILE)

    batteryPercentage = 100 * ((voltage - EMPTYBATTERY) / (FULLBATTERY - EMPTYBATTERY))
    #if batteryPercentage > 100:  #If it's more than 100% then make it 100%
    #    batteryPercentage = 100.00
    return round(batteryPercentage,1)  # Just leave one decimal place

def getGateSwitch():
    # Invert the 1-0 so that 1=button pressed 0=not pressed
    return not gateSwitch.value()

def magnetoOpen(baseGateAngle):
    if(DEBUG >=2):
        debug.debug(DEBUG, "magnetoOpen(baseGateAngle)    ", "Start", LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "magnetoOpen(baseGateAngle)    ", str(baseGateAnble), LOGTOFILE)
        
    returnValue=0
    currentGateAngle=readMagnetometer()
    if(DEBUG >=2):
        debug.debug(DEBUG, "magnetoOpen()    ", "currentGateAngle="+str(currentGateAngle), LOGTOFILE)

    angleDifference = getHeadingDiff(baseGateAngle,currentGateAngle)
    if(DEBUG >=2):
        debug.debug(DEBUG, "magnetoOpen()    ", "angleDifference="+str(angleDifference), LOGTOFILE)

    if (angleDifference > GATEANGLETHRESHOLD):
        returnValue=angleDifference
    return returnValue

def readMagnetometer():
    if(DEBUG >=2):
        debug.debug(DEBUG, "readMagnetometer()    ", "Start", LOGTOFILE)
    validData=False
    magReadCount=5    # Have 5 goes to read the Magnetometer
    heading=-1        # Set an invalid initial reading
    while(magReadCount > 0) and (validData == False):
        magReadCount=magReadCount-1
        heading = compass.readHeading()   # get the heading from the sensor
        if compass.dataValid():           # Rejects invalid data
            heading = round(heading)      # round to the nearest degree
            validData=True
            #print( str(heading) + "°")    # print the data with a degree symbol
        sleep_ms(100)

    if(DEBUG >=2):
        debug.debug(DEBUG, "readMagnetometer()    ", "Heading="+ str(heading), LOGTOFILE)
    return heading

def processMessage(message,err):
    # Process the incoming message
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage()    ", "Start", LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(message,err)    ", "Message Received=" + str(message), LOGTOFILE)
        debug.debug(DEBUG, "processMessage(message,err)    ", "message type="+ str(type(message)), LOGTOFILE)
        debug.debug(DEBUG, "processMessage(message,err)    ", "err="+ str(err), LOGTOFILE)

    if(ENCRYPTION == True):
        message=encryption.decryptMessage(message)             # Decrypt the message

    message=message.decode()                                   # Decode the byte string into a string
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(message,err)    ", "Decoded Message="+ str(message), LOGTOFILE)
    if(DEBUG >=2):    
        debug.debug(DEBUG, "processMessage(message,err)    ", "Decodded Message type="+ str(type(message)), LOGTOFILE)   
    
    # Load incoming message into a json object
    jsonDict=loads(message)
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(message,err)    ", "jsonDict=" + str(jsonDict), LOGTOFILE)

    # Check destination of this message = this device
    # LoRa messages are broadcast and any device can pick them up

    destination = jsonDict["DstDevice"]
    
    if(DEBUG >=2):
        debug.debug(DEBUG, "processMessage(message,err)", "destination="+destination, LOGTOFILE)
        debug.debug(DEBUG, "processMessage(message,err)", "DSTDEVICE="+DSTDEVICE, LOGTOFILE)

    # Don't forget the device SRCDEVICE is the name of this machine (receiving the message)
    if(destination == SRCDEVICE): 
        if(jsonDict["TimeUpdate"] == "True"):
            updateTime(jsonDict)

def updateTime(jsonDict):
    if(DEBUG >=2):
        debug.debug(DEBUG, "updateTime()", "Start ", LOGTOFILE)

    newTimeStamp = jsonDict["TimeStamp"] # Return just the time stamp from the remote communication string  

    if(DEBUG >=2):
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "TimeStamp from mainGate=" + str(newTimeStamp), LOGTOFILE)

    # Time Before
    if(DEBUG >=2):
        debug.debug(DEBUG, "updateTime(jsonDict)    ", "Local Time Before=" + str(localtime()), LOGTOFILE)

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
    RTC().datetime((newTime[0], newTime[1], newTime[2], newTime[6], newTime[3], newTime[4], newTime[5], 0))

    # Time After
    if(DEBUG >=2):
        debug.debug(DEBUG, "setTime()    ", "Local Time After=" + str(localtime()), LOGTOFILE)

def sendJson(textMessage):
    global messageNumber
    global gateOpen

    if(DEBUG >=2):
        debug.debug(DEBUG, "sendJson()    ", "Start", LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "sendJson()", " " + str(localtime()), LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "sendJson(textMessage)", "Send Json Text String="+ textMessage, LOGTOFILE)

    messageNumber = messageNumber+1
    timeStamp = localtime()
    voltage = vsys.read_u16() * conversion_factor
    batteryPercentage=getBatteryPercentage(voltage)
    tempValue = '%.2f'%picoTemp.readTemperature()
    message = loraMessage.buildLoraMessage(messageNumber,SRCDEVICE,DSTDEVICE,timeStamp,TIMEUPDATE,batteryPercentage,voltage,gateOpen,tempValue,textMessage)
    if(DEBUG >=2):
        debug.debug(DEBUG, "sendJson(textMessage)", "Message=" + str(message), LOGTOFILE)

    message=bytes((message).encode())
    
    if(ENCRYPTION == True):
        if(DEBUG >=2):
            debug.debug(DEBUG, "sendJson(textMessage)", "Encryption=" + "True", LOGTOFILE)

        message=encryption.encryptMessage(message)
    
    # Turn off LoRa Standby Mode (Standby Saves Power)
    if(LORASTANDBY == True):   # This variable indicates we are using standby mode
        if(DEBUG >=2):
            debug.debug(DEBUG, "sendJson(textMessage)", "Turn OFF Lora Standby Mode", LOGTOFILE)
        loraMessage.sx.standby(False)
    loraMessage.sx.send(message)
    
    # Wait for incoming messages like a time update before re-enabling StandBy Mode
    if(LORASTANDBY == True):
        sleep(15)
        if(DEBUG >=2):
            debug.debug(DEBUG, "sendJson(textMessage)", "Turn ON Lora Standby Mode", LOGTOFILE)
        loraMessage.sx.standby(True)
    
def startUpMessage():
    if(DEBUG >=1):
        debug.debug(DEBUG, "startUpMessage()    ", "Start", LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "startUpMessage()", " " + str(localtime()), LOGTOFILE)
        
    # Send Status message to mainHouse
    global gateOpen
    if(DEBUG >=2):
        debug.debug(DEBUG, "startUpMessage()", "Send Startup Message", LOGTOFILE)
    
    textMessage="StartUp Message"

    # Assume gate is closed for startup message.
    gateOpen="False"
    
    # Send the initial message to MainHouse
    sendJson(textMessage)
    
    # This delay following the sendJson command solves a weird
    # problem with the transmittion of the message to the remote device.
    # It only occures on the startup message when not running through Thonny.
    # Makes no sense to me.
    sleep(2)
    
    if(DEBUG >=1):
        debug.debug(DEBUG, "main()    ", "Startup Message Sent", LOGTOFILE)

def heartBeatMessage():
    if(DEBUG >=2):
        debug.debug(DEBUG, "heartBeatMessage()", "Start", LOGTOFILE)

    global mainGateHeartBeat
    
    # Get current time from the local clock
    now=localtime()
        
    # get the number of seconds between the two time tupples
    seconds=mktime(now)- mktime(mainGateHeartBeat)
    if(DEBUG >=2):
        debug.debug(DEBUG, "heartBeatMessage()", "Seconds="+str(seconds), LOGTOFILE)

    if(seconds >= constants.MAXHEARTBEAT / 2):
        # Send the meassage if 50% of the time has passed
        if(DEBUG >=2):
            debug.debug(DEBUG, "heartBeatMessage()", "Send The Heartbeat", LOGTOFILE)

        sendJson("Heart Beat")
        sleep(2)
        
        #Reset the Heartbeat timmer
        mainGateHeartBeat = localtime()        

###### End of method Defintions #####
if(DEBUG >=1):
        debug.debug(DEBUG, "main()", "Start", LOGTOFILE)

# Get initial gate angle from Magnetometer
# When a different angle is later detected the gate is open.
#print("mainGate.py (342) before gc="+ str(mem_free()))
collect()
#print("maingate.py (344) after gc="+ str(mem_free()))

if(DEBUG >=2):
    debug.debug(DEBUG, "main()", "before readMagnetometer()", LOGTOFILE)

if (GATESENSOR=="Magnetometer"):
    baseGateAngle = readMagnetometer()

if(DEBUG >=2):
    debug.debug(DEBUG, "main()", "after readMagnetometer()", LOGTOFILE)


# This is the line that enables the Lora routine to listen for incoming messages. cb(events)
# DP Not sure exactly how it works.  Seems to run when an intrupt is received
loraMessage.sx.setBlockingCallback(False, cb)

if(DEBUG >=0):
    led.toggle()    #Turn on board LED on or off

if(DEBUG >=2):
    debug.debug(DEBUG, "mainloop()", " Local Time=" + str(localtime()), LOGTOFILE)

while True:
    if(DEBUG >=2):
        debug.debug(DEBUG, "Main While Loop", "", LOGTOFILE)

    #print("mainGate.py (362) before gc="+ str(mem_free()))
    collect()
    #print("mainGate.py (364) after gc="+ str(mem_free()))
    
    # Send initial startup message once only
    if(startUp):
        startUpMessage()
        startUp=False
    
    # Send heart beat message
    heartBeatMessage()

    # The code below only sends a message if the gate status has changed
    # Look for gate open signal
    if(DEBUG >=2):
        debug.debug(DEBUG, "main()    ", "Check gate status", LOGTOFILE)
    
    # Select if gate sensor is a Microswitch or Magnetometer.
    if(GATESENSOR == "Switch"):
        if(DEBUG >=2):
            debug.debug(DEBUG, "main()    ", "MicroSwitch in Use", LOGTOFILE)
        gateStatus=gateSwitch()                    #Check the Microswitch position
    if(GATESENSOR =="Magnetometer"):
        if(DEBUG >=2):
           debug.debug(DEBUG, "main()    ", "Magnetometer in Use", LOGTOFILE)
        gateStatus=magnetoOpen(baseGateAngle)      #Check the Magnetometer position

    if(gateStatus != 0 and gateOpen == "False"):   #This allows the status to be reported only once after it changes
        # The Gate has changed from Closed to Open
        gateOpen="True"
        # Send Gate Open Message
        if(DEBUG >=1):
            debug.debug(DEBUG, "main()    ", "The Gate is now Open", LOGTOFILE)
        sendJson("Gate is Open, Status="+str(gateStatus))
        sleep(2)

    # If gate status has changed from open to closed
    if(gateStatus ==0 and gateOpen=="True"):
        gateOpen="False"
        # Send Gate Closed Message 
        if(DEBUG >=1):
            debug.debug(DEBUG, "main()    ", "The Gate is now Closed", LOGTOFILE)
        sendJson("Gate is Closed")
        sleep(2)
    
    # Don't loop to fast and waste power
    # How fast can a car get through with someone else opening and closing the gate?
    # This delay also allows for incoming messages like the time update before Lora is put into standby.
    if(DEBUG >=2):
        debug.debug(DEBUG, "main()    ", "Sleep Initiated", LOGTOFILE)

    # NOTE: It "appears" from the shell output that lightsleep does not work.
    #       However it only disrupts the connection through thonny and diconnects the console
    #       The process actually keeps running on the device and details are loged in the debuglog.csv output.
    #
    #       This also breaks Thonny's ability to halt the running process and requires
    #       unpluggin the power to regain control of the pico.
    #
    # Use lightSleep on pico to save power when running in headless mode
    if(LOWPOWERMODE == True):
        lightsleep(SLEEPTIME * 1000) # lightSleep is in milliseconds
    
    # Use regular sleep when degugging on a powered connection to avoid the above issues
    if(LOWPOWERMODE == False):
        sleep(SLEEPTIME)
    
    if(DEBUG >=2):
        debug.debug(DEBUG, "main()    ", "Main() Sleep Complete", LOGTOFILE)

    # Toggle the LED so we know the program is running
    # We see X seconds on and X seconds off
    if(DEBUG >=1):
        led.toggle()

