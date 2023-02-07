# Standard json format for Lora messages used in this project
import constants
import debug
from sx1262 import SX1262   #Lora library
import _sx126x

DEBUG = constants.DEBUG
LOGTOFILE = constants.LOGTOFILE

sx = SX1262(spi_bus=1, clk=10, mosi=11, miso=12, cs=3, irq=20, rst=15, gpio=2)

sx.begin(freq=923, bw=500.0, sf=12, cr=8, syncWord=0x12,
         power=-5, currentLimit=60.0, preambleLength=8,
         implicit=False, implicitLen=0xFF,
         crcOn=True, txIq=False, rxIq=False,
         tcxoVoltage=1.7, useRegulatorLDO=False, blocking=True)


# Build the json string and send the message.
def buildLoraMessage(messageNumber,srcDevice,dstDevice,timeStamp,timeUpdate,batteryPercent,gateOpen,textMessage):
    if(DEBUG >=1):
        debug.debug(DEBUG, "loraMessage.buildLoraMessage()", " ", LOGTOFILE)

    loraMessage = '{'
    loraMessage = loraMessage + '"MessageNumber":"' +  str(messageNumber) +'"'
    loraMessage = loraMessage + ',' + '"SrcDevice":"' + srcDevice +'"'
    loraMessage = loraMessage + ',' + '"DstDevice":"' + dstDevice +'"'
    loraMessage = loraMessage + ',' + '"TimeStamp":"' + str(timeStamp) +'"'
    loraMessage = loraMessage + ',' + '"TimeUpdate":"' + timeUpdate +'"'
    loraMessage = loraMessage + ',' + '"BatteryPercent":"' + str(batteryPercent) +'"'
    loraMessage = loraMessage + ',' + '"GateOpen":"' + gateOpen +'"'
    loraMessage = loraMessage + ',' + '"TextMessage":"' + textMessage + '"'
    loraMessage = loraMessage +'}'

    if(DEBUG >=2):
        debug.debug(DEBUG, "loraMessage.buildLoraMessage()    ", "loraMessage=" + loraMessage, LOGTOFILE)

    if(DEBUG >=2):
        debug.debug(DEBUG, "loraMessage.buildLoraMessage()    ", "loraMessage type=" + str(type(loraMessage)), LOGTOFILE)

    if(DEBUG >=2):
        debug.debug(DEBUG, "loraMessage.buildLoraMessage()    ", "jsonLoraMessage type=" + str(type(loraMessage)), LOGTOFILE)

    return loraMessage

