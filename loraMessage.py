# Standard json format for Lora messages used in this project
import constants
import debug

DEBUG = constants.DEBUG
LOGTOFILE = constants.LOGTOFILE

# Build the json string and send the message.
def buildLoraMessage(messageNumber,srcDevice,dstDevice,timeStamp,timeUpdate,batteryPercent,gateOpen,textMessage):

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
