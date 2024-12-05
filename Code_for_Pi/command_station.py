#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  command_station.py
#  
####################################### STEPPER MOTOR WIRING Letter is coil, number is direction
#Blue A2, Yellow B2, Green A1, Red B1
#
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

GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.OUT) #  
GPIO.setup(16, GPIO.OUT) #
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # bay button

from mfrc522 import SimpleMFRC522

import fcntl


# Stepper Motor Pi Hat modules
import board
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit

import ui_command_station

# globals
pos = 0;
bay_i = 0;
rfid_i = 0;
# stepper motor
kit = MotorKit(address=0x61)
command = ["sudo","python3","/home/traingroup/train/packet_wrapper.py"]

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
    
    run = True
    while run:
        # retrieve delay time from pipe - blocking statement
        delay_time = child_conn.recv()
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(seconds=delay_time)
        if delay_time < 0:
            run = False
        # while the delay is urnning, check to see if a new delay has been inputed, if so, update the end time.
        while datetime.datetime.now() < end_time:
            events = epoll.poll(0)
            for fd, event in events:
                end_time = datetime.datetime.now() + datetime.timedelta(seconds=child_conn.recv())
        delay_time = 0
        child_conn.send("done")
    print("delay terminated")

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
            sleep(0.262)
    else:
        print("Rotating bay clockwise to:", goal_bay)
        while pos > goal_bay:
            print("pos =", pos)
            kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
            pos-=1
            sleep(0.262)

def main(parent_conn):
    global bay_i, rfid_i
    
    screen = ui_command_station.init()
    
    # start delay subprocess
    delay_conn, child_conn = mp.Pipe()
    process = mp.Process(target=delay, args=(child_conn,), daemon=True)
    process.start()
    
    # initialze event for delay
    epoll = select.epoll()
    epoll.register(delay_conn, select.EPOLLIN)
    
    # initalize reader
    reader = SimpleMFRC522()
    
        
    # initialze the next_operation function
    if not hasattr(next_operation, 'current_operation'):
        next_operation.current_operation = 0 # start operation cycle with inital delay of 100 ms
    if not hasattr(next_operation, 'stage'):
        next_operation.stage = 0
    if not hasattr(next_operation, 'repeat'): # what operation to loop back to, 0 is default forward, None is stopped
        next_operation.repeat = 0
    if not hasattr(next_operation, 'rfid'): # what operation to loop back to, 0 is default forward, None is stopped
        next_operation.rfid = ""
    if not hasattr(next_operation, 'held_car'): # what operation to loop back to, 0 is default forward, None is stopped
        next_operation.held_car = ""
        
    # main loop ####################################################
    delay_conn.send(0.1) # delay first operation by 100 ms
    
    # recenter the turntable
    kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
    sleep(0.1)
    kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
    sleep(0.1)

    # if nothing in the sorting dictionary, immediately terminate
    run = True
    operating = False
    sorting_dict = {}
    queue = []
    while (run):
            
        # run ui to get sorting dictionary or assemble array
        op, op_list = ui_command_station.ui_loop(screen, sorting_dict, None)
        
        if op == "store" and op_list:
            sorting_dict = op_list.copy()
            num_to_sort = len(sorting_dict)
            num_sorted = 0
            operating = True
            next_operation.current_operation = 0
            delay_conn.send(0.1) # start it up!
        if op == "assemble" and op_list:
            queue = op_list.copy()
            num_to_sort = len(queue)
            num_sorted = 0
            operating = True
            next_operation.current_operation = 0
            delay_conn.send(0.1) # start it up!
        elif op == "manual":
            operating = True    
            next_operation.current_operation = -7000
        elif op == "term":
            run = False
            operating = False

        while(operating):
        
            # check delay conn
            events = epoll.poll(0)
            for fd,event in events:
                print("Done Waiting")
                # clear the delay pipe
                delay_conn.recv()
                finished = next_operation(parent_conn, delay_conn)
                if finished:
                    num_sorted += 1
                    print("OPERATION COMPLETE: num sorted =", num_sorted)
                        
            # get the text from the RF ID reader
            if op == "store" and next_operation.current_operation == 0: # DO NOT SCAN UNLESS DEFAULT FORWARD CURRENTLY HAPPENING
                id, text = reader.read_no_block()
                if text:
                    text = text.strip()
                    print(text)
                    if text in sorting_dict:
                        next_operation.current_operation = sorting_dict[text]
                        next_operation.held_car = text
                        print("storing in BAY", sorting_dict[text])
                        print("num to sort =", num_to_sort)
                        if num_sorted >= num_to_sort:
                            next_operation.repeat = None # repeat operation set to NONE, ending sorting sequence
                    else:
                        print("No operation for car")
                    delay_conn.send(0.1)
                                    
            # get the text from the RF ID reader
            elif op == "assemble" and next_operation.current_operation == 0: # DO NOT SCAN UNLESS DEFAULT FORWARD CURRENTLY HAPPENING
                id, text = reader.read_no_block()
                if text:
                    text = text.strip()
                    print(text)
                    if text in sorting_dict:
                        next_operation.current_operation = sorting_dict[text]
                        next_operation.rfid = text
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
            elif keys[pygame.K_SPACE]:
                cancel_op()
                os.write(parent_conn, b"stop")
            elif keys[pygame.K_e]:
                cancel_op()
                operating = False
                delay_conn.send(0.1)

            # interrupts
            if bay_i and (keys[pygame.K_i] or GPIO.input(24)):
                print("bay interrupt")
                delay_conn.send(0.0)
                bay_i = False
            if rfid_i:
                id, text = reader.read_no_block() # start scanning and interrupt when triggered
                if text:
                    print("RFID interrupt")
                    text = text.strip()
                    print(text)
                    next_operation.rfid = text
                    delay_conn.send(0.0)
                    rfid_i = False


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
                GPIO.output(26,0)
                GPIO.output(16,1)
                sleep(0.5)
                GPIO.output(16,0)
            elif keys[pygame.K_z]:
                print("Track Switch Right")
                GPIO.output(16,0)
                GPIO.output(26,1)
                sleep(0.5)
                GPIO.output(26,0)
                    
            
            for event in pygame.event.get():
                if event.type == pygame. QUIT:
                    run = False
                    operating = False
                
    # clean up
    kit.stepper1.release()
    pygame.quit()
    GPIO.cleanup()
    delay_conn.send(-1)
    os.write(parent_conn, b"term")
    
    return 0

def cancel_op():
    next_operation.current_operation = -7000
    next_operation.stage = 0


# how long to go forward after hitting bay switch in bay storage area to line up with decoupler
decouple_delay = {
    "GREEN": {
        1: 2.4,
        2: 2.52,
        3: 2.52,
        4: 2.52,
        5: 2.52,
        6: 2.52,                        
    },
    "RED": {
        1: 2.4,
        2: 2.52,
        3: 2.52,
        4: 2.52,
        5: 2.52,
        6: 2.52,                        
    },
}

def next_operation(parent_conn, delay_conn):
    global bay_i, rfid_i
    print("stage: ",next_operation.stage)
    match next_operation.current_operation: # which operation are we on? case_0 is default forward | case 1-6 = Bay storage | case_ = nothing
        case -7000: # literally nothing
            os.write(parent_conn, b"stop")
            print("no operation")
        case -5000: # backup till bay switch then do default forward again
            match abs(next_operation.stage): # which stage of operation?
                case 0:
                    print("****starting RETRY", b, "SEQUENCE****")
                    os.write(parent_conn, b"speed1") # fast
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                case 1:
                    rfid_i = True
                    os.write(parent_conn, b"backward") # backup
                    delay_conn.send(10)
                    next_operation.stage += 1
                case 2:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                case _:
                    os.write(parent_conn, b"speed0") # reset speed to slow
                    delay_conn.send(0.1)
                    next_operation.stage = 0
                    next_operation.current_operation  = 0 # default forward
        case 0: # default foward
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
                case 3:                                   ################### single car + engine decouple
                    os.write(parent_conn, b"forward")
                    delay_conn.send(0.5)
                    next_operation.stage += 1                   
                case 4:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                case 5:
                    os.write(parent_conn, b"backward")
                    delay_conn.send(0.5)
                    next_operation.stage += 1   
                case 6:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.5)
                    next_operation.stage += 1   
                case 7:                                   ##################### check to see if another car is scanned
                    rfid_i = True
                    os.write(parent_conn, b"forward")
                    delay_conn.send(5)
                    next_operation.stage += 1                                           
                case 8:
                    if next_operation.rfid == "ENGINE" or next_operation.rfid == next_operation.held_car: # this is correct
                        next_operation.stage -= 1
                        delay_conn.send(0.1)
                    elif next_operation.rfid != "": # SOMETHING WAS SCANNED, RETRY decouple
                        os.write(parent_conn, b"stop")
                        delay_conn.send(0.1)
                        next_operation.current_operation = -5000 # retry sequence
                        next_operation.stage = 0
                    else: # the 5 second delay finished
                        delay_conn.send(0.1)
                        next_operation.stage += 1
                case 9:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 10:
                    os.write(parent_conn, b"speed1")
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                case 11:
                    delay_conn.send(2)
                    turnTable(b) # rotate into the corresponding bay
                    next_operation.stage += 1
                case 12:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 13:
                    bay_i = True # be interrupted when backing into bay
                    os.write(parent_conn, b"backward")
                    delay_conn.send(12.9)
                    next_operation.stage += 1
                case 14:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(2)
                    next_operation.stage += 1
                case 15:
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                    #################################
                    # DECOUPLING OPERATION
                    ################################
                case 16:
                    os.write(parent_conn, b"forward") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(decouple_delay[next_operation.held_car][b])
                    next_operation.stage += 1
                case 17:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 18: # repeat
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.2)
                    next_operation.stage += 1
                case 19:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 20:
                    os.write(parent_conn, b"forward") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(1.2)
                    next_operation.stage += 1
                case 21:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 22: # repeat
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.1)
                    next_operation.stage += 1
                case 23:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 24:
                    os.write(parent_conn, b"forward") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(4.5)
                    next_operation.stage += 1
                case 25:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(2)
                    turnTable(0) # rotate back to straight
                    next_operation.stage += 1
                case 26:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 27:
                    rfid_i = True 
                    bay_i = True
                    next_operation.rfid = ""
                    os.write(parent_conn, b"backward")
                    delay_conn.send(15)
                    next_operation.stage += 1
                case 28:
                    if next_operation.rfid == "ENGINE": # scanned the engine, ignore
                        next_operation.stage -= 1 # go back and continue
                    elif next_operation.rfid != "": # it scanned a car
                        next_operation.stage = 0
                    else: # bay interrupt
                        os.write(parent_conn, b"stop")
                        next_operation.stage += 1
                    delay_conn.send(0.1)
                case _:
                    os.write(parent_conn, b"stop")
                    next_operation.stage = 0
                    # end operation
                    next_operation.current_operation = next_operation.repeat
                    delay_conn.send(4) # start going forward again after 4 second
                    return True # finished a full sequence
        case b if b in [-1,-2,-3,-4,-5,-6]: # retrieval sequence here
            pass
        case _:
            print("Current operation is NONE, stopping train")
            os.write(parent_conn, b"stop")
            next_operation.current_operation = None # continue doing nothing
    return False # still going

if __name__ == '__main__':
    child_conn, parent_conn = os.pipe() # connection pipe between this program, and the subprocess on the multiprocess
    agent = mp.Process(target=work, args = (child_conn,), daemon=True).start() # start multiprocess on other core for subprocess
    sys.exit(main(parent_conn))
