# RFID Modules
import RPi.GPIO as GPIO

from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setup(3, GPIO.OUT)

GPIO.output(3, 1)
sleep(5)
GPIO.output(3, 0)
sleep(5)
GPIO.output(3, 1)
sleep(5)
GPIO.output(3, 0)
sleep(5)
GPIO.output(3, 1)

GPIO.cleanup()
