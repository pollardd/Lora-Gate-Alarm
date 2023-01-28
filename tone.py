from machine import Pin, PWM
from utime import sleep

# Set GPIO pin for audio output
buzzer = PWM(Pin(13))    # Physical Pin 17  Gnd 18
buttonPin = 14           # Physical Pin 19  Gnd 13

# The button pin uses a pull up resistor so that it's value is 1
# when it is not pressed and 0 when it is pressed
button = Pin(buttonPin, Pin.IN,Pin.PULL_UP)

def play_tone(frequency):
    # Set maximum volume
    buzzer.duty_u16(40000) #40000 seems to be maximum volume
    # Play tone
    buzzer.freq(frequency)

def stop_tone():
    # Set minimum volume
    buzzer.duty_u16(0)

def get_button():
    # Invert the 1-0 so that 1=button pressed
    return not button.value()

def button_press_function():
    play_tone(900)
    #time.sleep(1)
    
def button_press_release_function():
    stop_tone()
    
# Loop
# count=1
# while True:
#    if get_button() == 1:
#        print(str(count) +" Button Pressed")
#        button_press_function()
#    else:
#        #print(str(count) +" Button Not Pressed")
#        button_press_release_function()
#    count=count+1