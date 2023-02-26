import debug
import time
import constants

# Constants
DEBUG = constants.DEBUG
LOGTOFILE =  constants.LOGTOFILE
ENCRYPTION = constants.ENCRYPTION


# Return time in HH:MM:SS format
def formattedTime():
    if(DEBUG >=2):
        debug.debug(DEBUG, "dateTime.formattedTime()", " ", LOGTOFILE)

    now=time.localtime()
    timeString=zfl(str(now[3]),2) + ":" + zfl(str(now[4]),2) + ":" + zfl(str(now[5]),2)
    return timeString

def formattedTimeString(inputTuple):
    if(DEBUG >=2):
        debug.debug(DEBUG, "dateTime.formattedTimeString()", " ", LOGTOFILE)

    timeString=zfl(str(inputTuple[3]),2) + ":" + zfl(str(inputTuple[4]),2) + ":" + zfl(str(inputTuple[5]),2)
    return timeString

# Return Date in DD/MM/YYYY format
def formattedDate():
    if(DEBUG >=2):
        debug.debug(DEBUG, "dateTime.formattedDate()", " ", LOGTOFILE)

    now=time.localtime()
    dateString=zfl(str(now[2]),2) + "/" + zfl(str(now[1]),2) + "/" + zfl(str(now[0]),2)
    return dateString

def formattedDateString(inputTuple):
    if(DEBUG >=2):
        debug.debug(DEBUG, "dateTime.formattedDateString()", " ", LOGTOFILE)

    dateString=zfl(str(inputTuple[2]),2) + "/" + zfl(str(inputTuple[1]),2) + "/" + zfl(str(inputTuple[0]),2)
    return dateString

# Zero pad the "imputString" with zeroes up to "width" for readability
def zfl(inputString, width):
    # Zero padd the specified number of digits
    if(DEBUG >=2):
        debug.debug(DEBUG, "dateTime.zfl()", " ", LOGTOFILE)

    padded = '{:0>{w}}'.format(inputString, w=width)
    return padded
