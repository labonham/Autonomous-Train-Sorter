import RPi.GPIO as GPIO
import time

servoPIN = 33
GPIO.setmode(GPIO.BOARD)
GPIO.setup(servoPIN, GPIO.OUT)

servoPWM = GPIO.PWM(servoPIN, 50) 
servoPWM.start(0) 
try:
  while True:
    servoPWM.ChangeDutyCycle(5)
    time.sleep(0.5)
    servoPWM.ChangeDutyCycle(7.5)
    time.sleep(0.5)
    servoPWM.ChangeDutyCycle(10)
    time.sleep(0.5)
    servoPWM.ChangeDutyCycle(12.5)
    time.sleep(0.5)
    servoPWM.ChangeDutyCycle(10)
    time.sleep(0.5)
    servoPWM.ChangeDutyCycle(7.5)
    time.sleep(0.5)
    servoPWM.ChangeDutyCycle(5)
    time.sleep(0.5)
    servoPWM.ChangeDutyCycle(2.5)
    time.sleep(0.5)
except KeyboardInterrupt:
  servoPWM.stop()
  GPIO.cleanup()