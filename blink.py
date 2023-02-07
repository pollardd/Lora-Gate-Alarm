from machine import Pin
import time
import constants
import counters
import debug

# Constants
DEBUG = constants.DEBUG
LOGTOFILE =  constants.LOGTOFILE
ENCRYPTION = constants.ENCRYPTION

button =  Pin(14, Pin.IN, Pin.PULL_UP)  # Physical Pin 19 Gnd = 13

def flash(ledPin, long, short):
    if(DEBUG >=2):
        debug.debug(DEBUG, "blink.flash()", " ", LOGTOFILE)

    led = Pin(ledPin, Pin.OUT)

    # Long
    count=0
    while(count < long):
        led.on()
        #print("LED ON")
        time.sleep(1.5)
        led.off()
        #print("LED OFF")
        time.sleep(1)
        count = count+1
    # Short
    count=0
    while(count < short):
        led.on()
        # time.sleep(0.5)
        checkButtonPress(.5)  # Check the button while holding the flash on
        led.off()
        # time.sleep(0.5)
        checkButtonPress(.5)  # Check the button while holding the flash off
        count = count+1

    #time.sleep(1.5)
    checkButtonPress(1.5)  # Check the button while waiting between flash groups

def checkButtonPress(seconds):
    # If Button pressed clear the flash count
    # This method also acts as a timer for the main program loop
    
    if(DEBUG >=2):
        debug.debug(DEBUG, "blink.checkButtonPress()", " ", LOGTOFILE)

    while seconds>0:
        if(DEBUG >=3):
            debug.debug(DEBUG, "checkButtonPress(seconds)", "seconds="+str(seconds), LOGTOFILE)

        if(getButton()==1):
            if(DEBUG >=1):
                debug.debug(DEBUG, "checkButtonPress(seconds)    ", "Reset Count Button Pressed, openCount=0", LOGTOFILE)
                counters.openCount=0
        time.sleep(0.125)   
        seconds=seconds - 0.125

def getButton():
    # Invert button value so 1=button pressed and 0=not pressed
    if(DEBUG >=2):
        debug.debug(DEBUG, "blink.getButton()", " ", LOGTOFILE)


    buttonPressed= not button.value()
    if(DEBUG >=3):
        debug.debug(DEBUG, "getButton()    ", "buttonPressed="+ str(buttonPressed), LOGTOFILE)
    return buttonPressed
