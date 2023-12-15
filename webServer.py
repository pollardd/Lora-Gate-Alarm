# Serve a Simple HTML page
# Web server based on an example found here
# https://how2electronics.com/raspberry-pi-pico-w-web-server-tutorial-with-micropython/

from machine import Pin, ADC, reset
from socket import socket
from time import sleep

# Home baked imports
import debug        # My debuging routine
import constants
import counters
import dateTime
import fileTail
import diskFree
import picoTemp
from subprocess import playTone
import counters

# Constants
VERSION = constants.VERSION
DEBUG = constants.DEBUG
LOGTOFILE =  constants.LOGTOFILE
EVENTDISPLAYLINES = constants.EVENTDISPLAYLINES
MAINGATEEVENTLOG = constants.MAINGATEEVENTLOG
EVENTDISPLAYLINES = constants.EVENTDISPLAYLINES
VOLUME =  constants.VOLUME
LOWFREQUENCY = constants.LOWFREQUENCY
HIGHFREQUENCY = constants.HIGHFREQUENCY
DELAY = constants.DELAY
REPEAT = constants.REPEAT

GATEBATTERYLEVEL = "batteryLevel.txt"
HTMLLINEBREAK = "<BR>"


# Temperature Sensor
# sensor_temp = ADC(4)
# conversion_factor = 3.3 / (65535)

# Pin Definitions
ledPin = 5                        # Physical Pin 7  Gnd = 8
led = Pin(ledPin, Pin.OUT)        # Define pin as output 

def main(sta_if,ip):
    if(DEBUG >=1):
        debug.debug(DEBUG, "webServer.main()    ", "webServer start",LOGTOFILE)
    try:
        if ip is not None:
            connection=open_socket(ip)
            serve(connection)
    except KeyboardInterrupt:
        reset()

#def temperature():
#    temperature_value = sensor_temp.read_u16() * conversion_factor 
#    temperature_Celcius = 27 - (temperature_value - 0.706)/0.00172169/ 8 
#    if(DEBUG >=2):
#        debug.debug(DEBUG, "webServer.temperature()        ", "Temp="+str(temperature_Celcius),LOGTOFILE)
#    sleep(1)
#    return temperature_Celcius
 
def webpage(VERSION,houseTempValue,gateTempValue, batteryPercentage, batteryUpdateTime, eventDetails, freeBytesHouse, dateTimeHouse):
    html = f"""
            <!DOCTYPE html>
            <html>
            <body>
            <H2>Gate Monitor</H2>
            <p>Version={VERSION}</p>
            <HR>
            <LI>House Local Time is {dateTimeHouse}</LI>
            <LI>House Pico Temperature is {houseTempValue} degrees Celsius</LI>
            <LI>Gate Pico Temperature is {gateTempValue} degrees Celsius</LI>
            <LI>House Free Disk Space is {freeBytesHouse} of 2048000 Bytes</LI>
            <LI>Gate Battery Percentage is {batteryPercentage}</LI>
            <LI>Gate Battery Update Time is {batteryUpdateTime}</LI>
            <HR>
            <p><H3>Gate Events Log Tail</H3></p>
            <p>{eventDetails}</p>
            <HR>
            <p><h3>House Device LED Error Messages</h3></p>\
            <li>1 long, 0 short = Device successfully started and running</li>\
            <li>1 long, 1 short = Low voltage at mainGate.py (Less than value set in constants.py)</li>\
            <li>1 long, 2 short = Unable to connect to Wifi at mainHouse.py</li>\
            <li>1 long, 3 short = Unable to set system clock at mainHouse.py</li>\
            <li>1 long, 4 short = Unable to open socket for inbound web page connection</li>\
            <li>1 long, 5 short = Heartbeat message timed out</li>\
            <HR>
            <P><H3>Test</H3></p>
            <form action="./led">
            <input type="submit" value="Led On" />
            </form>
            <form action="./off">
            <input type="submit" value="Led Off" />
            </form>
            <form action="./beep">
            <input type="submit" value="Play Sound" />
            </form>
            <form action="./resetCounter">
            <input type="submit" value="Reset Counter" />
            </form>

            </body>
            </html>
            """
    return html
 
def serve(connection):
    while True:
        if(DEBUG >=1):
            debug.debug(DEBUG, "webServer.serve(connection)", "Wait for web request",LOGTOFILE)
        client = connection.accept()[0]
        if(DEBUG >=2):
            debug.debug(DEBUG, "webServer.serve(connection)", "client="+str(client),LOGTOFILE)
        request = client.recv(1024)
        if(DEBUG >=2):
            debug.debug(DEBUG, "webServer.serve(connection)", "request="+str(request),LOGTOFILE)
        request = str(request)
        try:
            request = request.split()[1]
            if(DEBUG >=1):
                debug.debug(DEBUG, "webServer.serve(connection)", "request.split()[1]="+str(request),LOGTOFILE)

        except IndexError:
            if(DEBUG >=1):
                debug.debug(DEBUG, "webServer.serve(connection)", "IndexError",LOGTOFILE)
            pass
        
        if request == '/off?':
            led.low()
            if(DEBUG >=1):
                debug.debug(DEBUG, "webServer.serve(connection)", "Test set led off",LOGTOFILE)

        elif request == '/led?':
            led.high()
            if(DEBUG >=1):
                debug.debug(DEBUG, "webServer.serve(connection)", "Test set led on",LOGTOFILE)

        elif request == '/beep?':
            # Play the sound
            playTone(VOLUME, LOWFREQUENCY, HIGHFREQUENCY, DELAY, REPEAT)
            
            if(DEBUG >=1):
                debug.debug(DEBUG, "webServer.serve(connection)", "Test play the sound",LOGTOFILE)

        elif request == '/resetCounter?':
            # Reset the counter
            counters.openCount=0
            if(DEBUG >=1):
                debug.debug(DEBUG, "webServer.serve(connection)", "Test reset the counter LED to 0",LOGTOFILE)

        #Get the Temperature
        temperature=(picoTemp.readTemperature())

        if(DEBUG >=2):
            debug.debug(DEBUG, "webServer.serve(connection)", "temperature="+temperature,LOGTOFILE)

        houseTempValue='%.2f'%(temperature)

        # Read the most recent Main Gate Battery values from a file
        fileHandle=open(GATEBATTERYLEVEL,"r")
        batteryPercentage=fileHandle.readline()
        batteryUpdateTimeTuple=eval(str(fileHandle.readline()))
        gateTempValue=fileHandle.readline()

        if(DEBUG >=2):
            debug.debug(DEBUG, "webServer.serve(connection)", "batteryUpdateTimeTuple="+ str(batteryUpdateTimeTuple),LOGTOFILE)

        batteryUpdateTime=str(dateTime.formattedTimeString(batteryUpdateTimeTuple))
        if(DEBUG >=2):
            debug.debug(DEBUG, "webServer.serve(connection)", "batteryUpdateTime="+ batteryUpdateTime,LOGTOFILE)

        batteryUpdateDate=str(dateTime.formattedDateString(batteryUpdateTimeTuple))
        if(DEBUG >=2):
            debug.debug(DEBUG, "webServer.serve(connection)", "batteryUpdateDate="+ batteryUpdateDate,LOGTOFILE)

        if(DEBUG >=2):
            debug.debug(DEBUG, "webServer.serve(connection)", "gateTemp="+ str(gateTemp),LOGTOFILE)


        fileHandle.close()

        # Read the tail of the MaingGate Event Log
        rawEventDetails = fileTail.tail(MAINGATEEVENTLOG,EVENTDISPLAYLINES)
        if(DEBUG >=2):
            debug.debug(DEBUG, "webServer.serve(connection)", "rawEventDetails="+rawEventDetails, LOGTOFILE)

        eventDetails = rawEventDetails.replace('\n', HTMLLINEBREAK + '\n')
        if(DEBUG >=2):
            debug.debug(DEBUG, "webServer.serve(connection)", "eventDetails="+ eventDetails, LOGTOFILE)

        freeBytesHouse = diskFree.diskFree()
        timeHouse = dateTime.formattedTime()
        dateHouse = dateTime.formattedDate()

        if(DEBUG >=2):
            debug.debug(DEBUG, "webServer.serve(connection)", "timeHouse="+ timeHouse, LOGTOFILE)
            debug.debug(DEBUG, "webServer.serve(connection)", "dateHouse="+ dateHouse, LOGTOFILE)

        dateTimeHouse=str(dateHouse + " " + timeHouse)
        if(DEBUG >=2):
            debug.debug(DEBUG, "webServer.serve(connection)", "dateTimeHouse="+ dateTimeHouse, LOGTOFILE)

        html=webpage(VERSION,houseTempValue, gateTempValue, batteryPercentage, batteryUpdateDate + " " + batteryUpdateTime, eventDetails, freeBytesHouse, dateTimeHouse)
        client.send(html)
        client.close()
 
def open_socket(ip):
    #<TODO> Add a try catch block here
    # Received this error "OSError: [Errno 98] EADDRINUSE"
    # On the connection.bind(address) line below
    
    # Open a socket
    if(DEBUG >=1):
        debug.debug(DEBUG, "webServer.open_socket(ip) ", "Open a socket",LOGTOFILE)
    address = (ip, 80)
    connection = socket()
    connection.bind(address)
    connection.listen(1)
    if(DEBUG >=2):
        debug.debug(DEBUG, "webServer.open_socket(ip) ", "connection="+str(connection),LOGTOFILE)
    return(connection)
