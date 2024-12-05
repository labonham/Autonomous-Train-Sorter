import sys
import subprocess
import multiprocessing as mp
import pygame
import os
import time
import select
from enum import Enum
#clock
import datetime

# RFID Modules
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

import fcntl
import board
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit
import pygame


def main():
    kit = MotorKit(i2c=board.I2C())

    pygame.init()
    pygame.display.init()
    window = pygame.display.set_mode((300, 300))
    pygame.display.set_caption("Stepper Controller")

    print("use arrow keys to tune starting position, press 1 to start rotation")
    run = True
    while run:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.INTERLEAVE)
            time.sleep(0.05)
        elif keys[pygame.K_DOWN]:
            kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.INTERLEAVE)
            time.sleep(0.05)
        elif keys[pygame.K_1]:
            run=False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
	# clean up
	pygame.quit()
    print("beginning 180 rotation sequence")
    time.sleep(0.5)
    try:

        for j in range(200):
            kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.INTERLEAVE)
            time.sleep(.05)
        while True:
			
            pass
        '''for j in range(20):
            print("j = ", j)
            for i in range(100):
                kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.INTERLEAVE)
                time.sleep(0.05)
            time.sleep(2.5)
            for i in range(100):
                kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.INTERLEAVE)
                time.sleep(0.05)
            time.sleep(2.5)

        kit.stepper1.release()'''

    except KeyboardInterrupt:


        kit.stepper1.release()

if __name__ == '__main__':
    sys.exit(main())
