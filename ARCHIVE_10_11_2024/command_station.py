#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  command_station.py
#  
import sys
import subprocess
import multiprocessing as mp
import pygame
import os
from time import sleep
import select
from enum import Enum
#clock
import datetime

# RFID Modules
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

import fcntl


# Stepper Motor Pi Hat modules
import board
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit

import ui_command_station

# globals
pos = 0;
# stepper motor
kit = MotorKit(i2c=board.I2C())
command = ["sudo","python3","/home/traingroup/CPythonExtension/packet_wrapper.py"]

def work(conn):
    # set up file descriptor in NON-BLOCKING for the os.pipe
    file_conn = os.fdopen(conn)                 # make file object from connection pipe
    fd = file_conn.fileno()                     # get file descriptor
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)      # Get flags from descriptor
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)   # set O_NONBLOCK to make it not block the subprocess when trying to read
    process = subprocess.Popen(command, stdin = file_conn)  # run subproccess as a root .py with connection pipe as stdin


def delay(child_conn):
    epoll = select.epoll()
    epoll.register(child_conn, select.EPOLLIN)
    
    while True:
        # retrieve delay time from pipe - blocking statement
        delay_time = child_conn.recv()
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(seconds=delay_time)
        if delay_time < 0:
            break
        # while the delay is urnning, check to see if a new delay has been inputed, if so, update the end time.
        while datetime.datetime.now() < end_time:
            events = epoll.poll(0)
            for fd, event in events:
                end_time = datetime.datetime.now() + datetime.timedelta(seconds=child_conn.recv())
        #print("AAAHH")
        delay_time = 0
        child_conn.send("done")

def turnTable(bay):
    global pos;
    global kit;
    forwardpos = 0;
    reversepos = 100;
    bay1 = 22;
    bay2 = 35;
    bay3 = 48;
    bay4 = 61;
    bay5 = 74;
    bay6 = 87;
    goal_bay = 22;
    
    match bay:
        case 0:
            goal_bay = forwardpos;
        case 1:
            goal_bay = bay1;
        case 2:            
            goal_bay = bay2;
        case 3:
            goal_bay = bay3;
        case 4:
            goal_bay = bay4;
        case 5:
            goal_bay = bay5;
        case 6:
            goal_bay = bay6;
        case 7:
            goal_bay = reversepos;
            
    if pos < goal_bay:
        print("Rotating bay counter clockwise to:", goal_bay)
        while pos < goal_bay:
            print("pos =", pos)
            kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
            pos+=1
            sleep(0.05)
    else:
        print("Rotating bay clockwise to:", goal_bay)
        while pos > goal_bay:
            print("pos =", pos)
            kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
            pos-=1
            sleep(0.05)
            
''' 
sorting_dict = {
    "GREEN" : Bay.BAY_1, 
    "RED"   : Bay.BAY_2, 
}
'''

def main(parent_conn):
    pygame.init()

    ui_command_station.init()
    
    # start delay subprocess
    delay_conn, child_conn = mp.Pipe()
    process = mp.Process(target=delay, args=(child_conn,))
    process.start()
    
    # initialze event for delay
    epoll = select.epoll()
    epoll.register(delay_conn, select.EPOLLIN)
    
    # run ui to get sorting dictionary or assemble array
    sorting_dict = ui_command_station.ui_loop()
    
    if sorting_dict:
        num_to_sort = len(sorting_dict)
    num_sorted = 0
    
    # initalize reader
    reader = SimpleMFRC522()
    
        
    # initialze the next_operation function
    if not hasattr(next_operation, 'current_operation'):
        next_operation.current_operation = 0 # start operation cycle with inital delay of 100 ms
    if not hasattr(next_operation, 'stage'):
        next_operation.stage = 0
    if not hasattr(next_operation, 'repeat'): # what operation to loop back to, 0 is default forward, None is stopped
        next_operation.repeat = 0
        
    # main loop ####################################################
    delay_conn.send(0.1) # delay first operation by 100 ms
    
    # recenter the turntable
    kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
    sleep(0.5)

    # if nothing in the sorting dictionary, immediately terminate
    if not sorting_dict:
        run = 0
    else:
        run = 1
    while(run):
       
        # check delay conn
        events = epoll.poll(0)
        for fd,event in events:
            print("Done Waiting")
            # clear the delay pipe
            delay_conn.recv()
            next_operation(parent_conn, delay_conn)
                    
        # get the text from the RF ID reader

        if next_operation.current_operation == 0: # DO NOT SCAN UNLESS THERE IS NO OPERATION CURRENTLY HAPPENING
            id, text = reader.read_no_block()
            if text:
                text = text.strip()
                print(text)
                if text in sorting_dict:
                    next_operation.current_operation = sorting_dict[text]
                    print("storing in BAY", sorting_dict[text])
                    num_sorted += 1
                    print("num sorted =", num_sorted)
                    print("num to sort =", num_to_sort)
                    if num_sorted >= num_to_sort:
                        next_operation.repeat = None # repeat operation set to NONE, ending sorting sequence
                else:
                    print("No operation for car")
                delay_conn.send(0.1)
            
        # get keys
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            cancel_op()
            os.write(parent_conn, b"forward")
        elif keys[pygame.K_DOWN]:
            cancel_op()
            os.write(parent_conn, b"backward")
        elif keys[pygame.K_1]:
            os.write(parent_conn, b"flip1")
        elif keys[pygame.K_2]:
            os.write(parent_conn, b"flip2")
        elif next_operation.current_operation == 0 and keys[pygame.K_SPACE]:
            os.write(parent_conn, b"stop")
        if keys[pygame.K_RIGHT]:
            kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
            sleep(0.5)
        elif keys[pygame.K_LEFT]:
            kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
            sleep(0.5)
            
        elif keys[pygame.K_3]:
            os.write(parent_conn, b"flip1")
            turnTable(0)
                
        elif keys[pygame.K_4]:
            turnTable(7)
            os.write(parent_conn, b"flip2") # reverse turntable polarity
                

        elif keys[pygame.K_5]: #bay1
            os.write(parent_conn, b"flip1")
            turnTable(1)
                
        elif keys[pygame.K_6]: #bay2
            os.write(parent_conn, b"flip1")
            turnTable(2)
                
        elif keys[pygame.K_7]: #bay3
            os.write(parent_conn, b"flip1")
            turnTable(3)
                
        elif keys[pygame.K_8]: #bay4
            os.write(parent_conn, b"flip1")
            turnTable(4)
                
        elif keys[pygame.K_9]: #bay5
            os.write(parent_conn, b"flip1")
            turnTable(5)
                
        elif keys[pygame.K_0]: #bay6
            turnTable(6)
                    
        elif keys[pygame.K_a]:
            print("Track Switch Left")
            GPIO.output(26,1)
            sleep(0.5)
            GPIO.output(26,0)
                
        
        for event in pygame.event.get():
            if event.type == pygame. QUIT:
                run = False
                
    # clean up
    kit.stepper1.release()
    pygame.quit()
    GPIO.cleanup()
    delay_conn.send(-1)
    os.write(parent_conn, b"term")
    
    return 0

def cancel_op():
    next_operation.current_operation = None
    next_operation.stage = 0

def next_operation(parent_conn, delay_conn):
    print("stage: ",next_operation.stage)
    match next_operation.current_operation: # which operation are we on? case_0 is default forward | case 1-6 = Bay storage | case_ = nothing
        case 0: # No Operation
            print("default forward operation")
            os.write(parent_conn, b"forward")
            next_operation.current_operation = 0 # reset to NONE
        case b if b in [1,2,3,4,5,6]: # Sorting into bay 1-6
            match abs(next_operation.stage): # which stage of operation?
                case 0:
                    print("****starting BAY", b, "SEQUENCE****")
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 1:
                    os.write(parent_conn, b"function0")
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                case 2:
                    os.write(parent_conn, b"function1")
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                case 3:
                    os.write(parent_conn, b"forward")
                    delay_conn.send(5)
                    next_operation.stage += 1
                case 4:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 5:
                    os.write(parent_conn, b"speed1")
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                case 6:
                    delay_conn.send(2)
                    turnTable(b) # rotate into the corresponding bay
                    next_operation.stage += 1
                case 7:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 8:
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.9)
                    next_operation.stage += 1
                case 9:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(5)
                    next_operation.stage += 1
                case 10:
                    os.write(parent_conn, b"forward")
                    delay_conn.send(1.6)
                    next_operation.stage += 1
                case 11:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 12:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(2)
                    turnTable(0) # rotate back to straight
                    next_operation.stage += 1
                case 13:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 14:
                    os.write(parent_conn, b"backward")
                    delay_conn.send(3.5)
                    next_operation.stage += 1
                case 15:
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                case 16:
                    os.write(parent_conn, b"backward")
                    delay_conn.send(5)
                    next_operation.stage += 1
                case _:
                    os.write(parent_conn, b"stop")
                    next_operation.stage = 0
                    # end operation
                    next_operation.current_operation = next_operation.repeat
                    delay_conn.send(4) # start going forward again after 4 second
        case 2: # retrieval sequence here
            pass
        case _:
            print("Current operation is NONE, stopping train")
            os.write(parent_conn, b"stop")
            next_operation.current_operation = None # continue doing nothing

if __name__ == '__main__':
    child_conn, parent_conn = os.pipe() # connection pipe between this program, and the subprocess on the multiprocess
    agent = mp.Process(target=work, args = (child_conn,), daemon=True).start() # start multiprocess on other core for subprocess
    sys.exit(main(parent_conn))
