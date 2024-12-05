import RPi.GPIO as GPIO
import time
import keyboard
def servo_control(start, position):

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(37, GPIO.OUT)

    try:
        while True:
            if keyboard.is_pressed("a"):
                print("PRESSED UP")
                GPIO.output(26,1)
                sleep(0.5)
                PIO.output(26,0)
        servoPWM.stop()
        GPIO.cleanup()
        return position



    except KeyboardInterrupt:
        servoPWM.stop()
        GPIO.cleanup()



	
