import board
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit


kit = MotorKit(address=0x61)
kit.stepper1.release()

