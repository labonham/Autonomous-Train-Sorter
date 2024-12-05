import RPi.GPIO as GPIO
import time
import keyboard
def servo_control(start, position):
    
    servoPIN = 33
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(servoPIN, GPIO.OUT)


    servoPWM = GPIO.PWM(servoPIN, 50) 
    servoPWM.start(start)
    try:
        while True:
            if keyboard.is_pressed("up"):
                print("PRESSED UP")
        while start<position:
            servoPWM.ChangeDutyCycle(start)
            time.sleep(.2)
            start = start+.15;
            print(start)
        while start>position:
            servoPWM.ChangeDutyCycle(start)
            time.sleep(.2)
            start=start-.15;
        servoPWM.stop()
        GPIO.cleanup()
        return position



    except KeyboardInterrupt:
        servoPWM.stop()
        GPIO.cleanup()


valid = False;
start = 0.0;
while True:
    try:
        while valid == False:
            position = float(input("Please input a position to go to between 1 and 12. "));
            if position<=12 and position>=1:
                valid = True;
        start = servo_control(start,position);
        print("Finished");
        valid = False;
    except KeyboardInterrupt:
        servoPWM.stop()
        GPIO.cleanup()

	
