import socket
import time
import struct
import dateTime
import sys
import machine
import debug


def setTime(TimeZoneOffset, host, DEBUG, LOGTOFILE):
    if(DEBUG >=2):
        debug.debug(DEBUG, "setTime()", "TimeZoneOffset="+str(TimeZoneOffset), LOGTOFILE)
    if(DEBUG >=2):
        debug.debug(DEBUG, "setTime()", "NTP Server="+str(host), LOGTOFILE)

    NTP_TIMEOUT = 8
    NTP_DELTA = 2208988800
    NTP_DELTA =  NTP_DELTA - (TimeZoneOffset * 3600)
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(NTP_TIMEOUT)
    res = s.sendto(NTP_QUERY, addr)
    msg = s.recv(48)
    s.close()

    val = struct.unpack("!I", msg[40:44])[0]
    t = val - NTP_DELTA    
    tm = time.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

    if(DEBUG >=3):
        timeStamp=str(dateTime.formattedTime())
        debug.debug(DEBUG, "setTime()    ", "Time After=" + str(timeStamp), LOGTOFILE)

