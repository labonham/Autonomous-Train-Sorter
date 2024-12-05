# RFID Modules
import RPi.GPIO as GPIO
from time import sleep
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.OUT) #  
GPIO.setup(16, GPIO.OUT) #


print("Track Switch Left")
GPIO.output(26,1)
sleep(0.5)
GPIO.output(26,0)
sleep(0.5)
GPIO.output(16,1)
sleep(0.5)
GPIO.output(16,0)

GPIO.cleanup()
