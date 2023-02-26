# Serve a Simple HTML page
# Web server based on an example found here
# https://how2electronics.com/raspberry-pi-pico-w-web-server-tutorial-with-micropython/

import machine
import socket
import math
import network
import time
# import secretsHouse

# Home baked imports
import debug        # My debuging routine
import constants
import counters
import dateTime

# Constants
DEBUG = constants.DEBUG
LOGTOFILE =  constants.LOGTOFILE
mainGateFileName="batteryLevel.txt"

# Temperature Sensor
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

# Pin Definitions
ledPin = 5                                   # Physical Pin 7  Gnd = 8
led = machine.Pin(ledPin, machine.Pin.OUT)   # Define pin as output 


def main(sta_if,ip):
    if(DEBUG >=1):
        debug.debug(DEBUG, "webServer.main()    ", "webServer start",LOGTOFILE)
    try:
        if ip is not None:
            connection=open_socket(ip)
            serve(connection)
    except KeyboardInterrupt:
        machine.reset()

def temperature():
    temperature_value = sensor_temp.read_u16() * conversion_factor 
    temperature_Celcius = 27 - (temperature_value - 0.706)/0.00172169/ 8 
    if(DEBUG >=1):
        debug.debug(DEBUG, "webServer.tempreature()        ", "Temp="+str(temperature_Celcius),LOGTOFILE)
    time.sleep(1)
    return temperature_Celcius
 
def webpage(tempValue, batteryPercentage, batteryUpdateTime):
    html = f"""
            <!DOCTYPE html>
            <html>
            <body>
            <form action="./led">
            <input type="submit" value="Led On" />
            </form>
            <form action="./off">
            <input type="submit" value="Led Off" />
            </form>
            <p>House Pico Temperature is {tempValue} degrees Celsius</p>
            <p>Gate Battery Percentage is {batteryPercentage}</p>
            <p>Gate Battery Update Time is {batteryUpdateTime}</p>
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
                debug.debug(DEBUG, "webServer.serve(connection)", "set led off",LOGTOFILE)

        elif request == '/led?':
            led.high()
            if(DEBUG >=1):
                debug.debug(DEBUG, "webServer.serve(connection)", "set led on",LOGTOFILE)
        #Get the Temperature
        tempValue='%.2f'%temperature()

        # Read the most recent Main Gate Battery values from a file
        fileHandle=open(mainGateFileName,"r")
        batteryPercentage=fileHandle.readline()
        batteryUpdateTimeTuple=eval(str(fileHandle.readline()))
        if(DEBUG >=1):
            debug.debug(DEBUG, "webServer.serve(connection)", "batteryUpdateTimeTuple="+ str(batteryUpdateTimeTuple),LOGTOFILE)

        batteryUpdateTime=str(dateTime.formattedTimeString(batteryUpdateTimeTuple))
        if(DEBUG >=1):
            debug.debug(DEBUG, "webServer.serve(connection)", "batteryUpdateTime="+ batteryUpdateTime,LOGTOFILE)

        batteryUpdateDate=str(dateTime.formattedDateString(batteryUpdateTimeTuple))
        if(DEBUG >=1):
            debug.debug(DEBUG, "webServer.serve(connection)", "batteryUpdateDate="+ batteryUpdateDate,LOGTOFILE)

        fileHandle.close()
        
        html=webpage(tempValue, batteryPercentage, batteryUpdateDate + " " + batteryUpdateTime)
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
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    if(DEBUG >=2):
        debug.debug(DEBUG, "webServer.open_socket(ip) ", "connection="+str(connection),LOGTOFILE)
    return(connection)
 
# main()
