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

import spidev

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
# decoupling delay test
test = 1.65;

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
    delay_time = 0
    while run:
        # retrieve delay time from pipe - blocking statement
        if delay_time < -0.5:
            break
        delay_time = child_conn.recv()
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(seconds=delay_time)
        # while the delay is urnning, check to see if a new delay has been inputed, if so, update the end time.
        while datetime.datetime.now() < end_time:
            events = epoll.poll(0)
            for fd, event in events:
                delay_time = child_conn.recv()
                end_time = datetime.datetime.now() + datetime.timedelta(seconds=delay_time)
        child_conn.send("done")
    print("delay terminated")


bay_speed_clockwise = {
        0: 0.25, # untested
        22: 0.15, # untested
        35: 0.25, # untested
        48: 0.25, # untested
        61: 0.25, # untested
        74: 0.45, # untested      
        87: 0.25, # untested   
        100: 0.25, # untested                    
}

bay_speed_counterclockwise = {
        0: 0.40, # untested
        22: 0.15, # good
        35: 0.05, # untested
        48: 0.35, # untested
        61: 0.35, # untested
        74: 0.85, # untested      
        87: 0.65, # untested   
        100: 0.25, # untested                    
}
    
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
    goal_bay = forwardpos;
    
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
            
    first_step = 3;
    if pos < goal_bay:
        print("Rotating bay counter clockwise to:", goal_bay)
        while pos < goal_bay:
            print("pos =", pos)
            kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
            pos+=1
            if first_step > 0:
                sleep(0.08)
                first_step = first_step - 1
            elif pos > goal_bay - 2:
                sleep(bay_speed_counterclockwise[goal_bay])
            else:
                sleep(0.065)
    else:
        print("Rotating bay clockwise to:", goal_bay)
        while pos > goal_bay:
            print("pos =", pos)
            kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
            pos-=1
            if first_step > 0:
                sleep(0.08)
                first_step = first_step - 1
            elif pos < goal_bay + 2:
                sleep(bay_speed_clockwise[goal_bay])
            else:
                sleep(0.056)

sorting_dict = {}
queue = []

def main(parent_conn):
    global bay_i, rfid_i, sorting_dict, queue, test
    
    screen = ui_command_station.init()
    
    spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz = 1000000
    
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
    sleep(0.01)
    kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
    sleep(0.01)

    # if nothing in the sorting dictionary, immediately terminate
    run = True
    operating = False
    lastPin = 0;
    queue_i = 0;
    mute = False
    speed_edge = True
    speed_toggle = False
    button_edge = False
    
    start_switch = False
    switch_count = 0
    switch_needed = 10000

    try:
        while (run):
                
            # run ui to get sorting dictionary or assemble array
            op, op_store, op_queue = ui_command_station.ui_loop(screen, sorting_dict.copy(), queue.copy())
            next_operation.stage = 0;
            print("UI sent:", op, op_store, op_queue)
            print("sortin_dictionary:", sorting_dict)
            print("queue:", queue)
            if op == "store" and op_store:
                os.write(parent_conn, b"speed0") # make fast
                sorting_dict = op_store
                queue = op_queue
                if len(op_queue) == 0:
                    num_to_sort = len(sorting_dict)
                else:
                    num_to_sort = len(op_queue)
                num_sorted = 0
                operating = True
                next_operation.current_operation = 300 # operation STORE START
                next_operation.repeat = 300
                print("number to store", num_to_sort)
                delay_conn.send(0.1) # start it up!
            elif op == "assemble" and op_queue:
                queue = op_queue
                num_to_sort = len(queue)
                print("Number to retrieve:", num_to_sort)
                num_sorted = 0
                operating = True
                next_operation.current_operation = 600 # operation RETRIEVAL START
                next_operation.repeat = 600
                queue_i = 0
                next_operation.held_car = queue[queue_i] # get first car
                delay_conn.send(0.1) # start it up!
            elif op == "manual":
                os.write(parent_conn, b"speed2") # make fast
                operating = True    
                next_operation.current_operation = -7000
            elif op == "control":
                num_to_sort = 0
                print("Number to retrieve:", num_to_sort)
                num_sorted = 0
                os.write(parent_conn, b"speed2") # make fast
                operating = True    
                next_operation.current_operation = -8000
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
                        if op == "assemble" and num_sorted < num_to_sort:
                            next_operation.held_car = queue[num_sorted] # get next car
                        if num_sorted >= num_to_sort:
                                next_operation.repeat = None # repeat operation set to NONE, ending sorting sequence
                                print("next_operation.repeat set to NONE")
                                operating = False
                        print("OPERATION COMPLETE: num sorted =", num_sorted)
 
                    
                # get keys
                
                keys = pygame.key.get_pressed()
                if op == "manual" or op == "store" or op == "assemble":
                    if keys[pygame.K_UP]:
                        cancel_op()
                        os.write(parent_conn, b"forward")
                    elif keys[pygame.K_DOWN]:
                        cancel_op()
                        os.write(parent_conn, b"backward")
                    elif keys[pygame.K_SPACE]:
                        cancel_op()
                        os.write(parent_conn, b"stop")
                    elif keys[pygame.K_e]:
                        cancel_op()
                        os.write(parent_conn, b"stop")
                        operating = False
                    elif not keys[pygame.K_m] and mute:
                        mute = False
                        os.write(parent_conn, b"mute")
                    elif keys[pygame.K_m]:
                        mute = True
                    elif not keys[pygame.K_n] and not speed_edge:
                        speed_edge = False
                        speed_toggle = ~speed_toggle
                        if speed_toggle:
                            os.write(parent_conn, b"speed1")
                        else:
                            os.write(parent_conn, b"speed0")
                    elif keys[pygame.K_n]:
                        speed_edge = True
                elif op == "control":
                    if keys[pygame.K_UP]:
                        if button_edge:
                            os.write(parent_conn, b"forward")
                        button_edge = False
                    elif keys[pygame.K_DOWN]:
                        if button_edge:
                            os.write(parent_conn, b"backward")
                        button_edge = False
                    elif keys[pygame.K_SPACE]:
                        os.write(parent_conn, b"stop")
                    elif keys[pygame.K_e]:
                        os.write(parent_conn, b"stop")
                        operating = False
                    elif not keys[pygame.K_m] and mute:
                        mute = False
                        os.write(parent_conn, b"mute")
                    elif keys[pygame.K_m]:
                        mute = True
                    elif keys[pygame.K_h]:
                        if button_edge:
                            os.write(parent_conn, b"horn")
                        button_edge = False 
                    elif keys[pygame.K_l]:
                        if button_edge:
                            os.write(parent_conn, b"lights")
                        button_edge = False 
                    elif keys[pygame.K_b]:
                        if button_edge:
                            os.write(parent_conn, b"bell")
                        button_edge = False 
                    elif keys[pygame.K_o]:
                        if button_edge:
                            os.write(parent_conn, b"longhorn")
                        button_edge = False 
                    else:
                        button_edge = True
                        
                    if keys[pygame.K_a] and start_switch == False: 
                        print("Track Switch Left")
                        GPIO.output(26,0)
                        GPIO.output(16,1)
                        start_switch = True
                    elif keys[pygame.K_z] and start_switch == False:
                        print("Track Switch Right")
                        GPIO.output(16,0)
                        GPIO.output(26,1)
                        start_switch = True
                    if start_switch:
                        switch_count += 1
                        if switch_count >= switch_needed:
                            print("GPIO shutoff")
                            switch_count = 0
                            GPIO.output(26,0)
                            GPIO.output(16,0)
                            start_switch = False

                # interrupts
                if bay_i:
                    if GPIO.input(24) and lastPin >= 4:
                        print("bay interrupt")
                        delay_conn.send(0.0)
                        bay_i = False
                    if GPIO.input(24) == 0:
                        lastPin = 0
                    else:
                        lastPin = lastPin + GPIO.input(24);
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
                    
                elif keys[pygame.K_1]:
                    os.write(parent_conn, b"flip1")
                    turnTable(0)
                        
                elif keys[pygame.K_8]:
                    turnTable(7)
                    os.write(parent_conn, b"flip2") # reverse turntable polarity
                        

                elif keys[pygame.K_2]: #bay1
                    os.write(parent_conn, b"flip1")
                    turnTable(1)
                        
                elif keys[pygame.K_3]: #bay2
                    os.write(parent_conn, b"flip1")
                    turnTable(2)
                        
                elif keys[pygame.K_4]: #bay3
                    os.write(parent_conn, b"flip1")
                    turnTable(3)
                        
                elif keys[pygame.K_5]: #bay4
                    os.write(parent_conn, b"flip1")
                    turnTable(4)
                        
                elif keys[pygame.K_6]: #bay5
                    os.write(parent_conn, b"flip1")
                    turnTable(5)
                        
                elif keys[pygame.K_7]: #bay6
                    turnTable(6)
                
                elif keys[pygame.K_s]:
                    next_operation.current_operation = 1400 # operation STORE TEST
                    delay_conn.send(0.1) # start it up!
                elif keys[pygame.K_w]:
                    test += 0.01
                    sleep(0.1)
                    print("test decouple delay =", test)
                elif keys[pygame.K_x]:
                    test -= 0.01
                    sleep(0.1)
                    print("test decouple delay =", test)
                
                for event in pygame.event.get():
                    if event.type == pygame. QUIT:
                        run = False
                        operating = False
    except Exception as e:
        print(e)
        pass
    # clean up
    delay_conn.send(-1)
    kit.stepper1.release()
    pygame.quit()
    GPIO.cleanup()
    os.write(parent_conn, b"term")
    spi.close()
    
    return 0

def cancel_op():
    global bay_i, rfid_i
    bay_i = False
    rfid_i = False
    next_operation.current_operation = -7000
    next_operation.stage = 0


# how long to go forward after hitting bay switch in bay storage area to line up with decoupler

#status of bays
decouple_delay = {
    "GREEN": {
        1: 1.52, # good
        2: 1.6,  # good
        3: 1.62,  # good
        4: 1.84, # good
        5: 1.67, # untested
        6: 2.11, # good                 
    },
    "RED": {
        1: 1.56, # good
        2: 1.6,  # good
        3: 1.73, # good
        4: 1.78, # good
        5: 1.67, # good
        6: 2.11, # good     
    },
    "BROWN": {
        1: 1.56, # untested
        2: 1.6,  # untested
        3: 1.73, # untested
        4: 1.78, # untested
        5: 1.8, # untested
        6: 1.94, # untested           
    },
    "BLACK": {
        1: 1.56, # good
        2: 1.58, # good
        3: 1.73, # good
        4: 1.78, # good
        5: 1.67, # good
        6: 2.11, # good              
    },
}

queue_adjust = -0.2

def next_operation(parent_conn, delay_conn):
    global bay_i, rfid_i, sorting_dict, test
    print("stage: ",next_operation.stage)
    match next_operation.current_operation: # which operation are we on? case_0 is default forward | case 1-6 = Bay storage | case_ = nothing
        case -8000: # when manually controlled, hitting the bay switch ends the controling
            match next_operation.stage: # which stage of operation?   
                case 0:
                    print("****starting CONTROL****")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                    os.write(parent_conn, b"forward")
                case 1:
                    delay_conn.send(0.3)
                    next_operation.stage += 1
                    os.write(parent_conn, b"stop")
                case 2:
                    bay_i = True
                    delay_conn.send(10000)
                    next_operation.stage += 1
                    os.write(parent_conn, b"speed2")
                case 3:
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.2)
                    next_operation.stage += 1
                case _:
                    os.write(parent_conn, b"stop")
                    next_operation.stage = 0
                    # end operation
                    next_operation.current_operation = -7000
                    delay_conn.send(0.5) # start going forward again after 4 second
                    return True # finished a full sequence
        case -7000: # literally nothing
            #os.write(parent_conn, b"stop")
            print("no operation")
        case -6000: # backup till bay switch then do default forward again
            match next_operation.stage: # which stage of operation?
                case 0:
                    print("****starting RETRY", "SEQUENCE****")
                    rfid_i = False
                    os.write(parent_conn, b"speed3") # not fast
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                case 1:
                    bay_i = True
                    os.write(parent_conn, b"backward") # backup
                    delay_conn.send(20)
                    next_operation.stage += 1
                case 2:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                case 3:
                    os.write(parent_conn, b"forward")
                    delay_conn.send(0.65)
                    next_operation.stage += 1
                case 4:
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.5)
                    next_operation.stage += 1
                case 6:
                    os.write(parent_conn, b"speed1")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                case 7:
                    os.write(parent_conn, b"forward")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                case _:
                    os.write(parent_conn, b"speed0") # reset speed to slow
                    delay_conn.send(0.1)
                    next_operation.stage = 0
                    next_operation.current_operation  = 600 # default forward
        case -5000: # backup till bay switch then do default forward again
            match next_operation.stage: # which stage of operation?
                case 0:
                    print("****starting RETRY", "SEQUENCE****")
                    rfid_i = False
                    os.write(parent_conn, b"speed3") # not fast
                    delay_conn.send(0.3)
                    next_operation.stage += 1
                case 1:
                    bay_i = True
                    os.write(parent_conn, b"backward") # backup
                    delay_conn.send(20)
                    next_operation.stage += 1
                case 2:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                case 3:
                    os.write(parent_conn, b"forward")
                    delay_conn.send(0.65)
                    next_operation.stage += 1
                case 4:
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.5)
                    next_operation.stage += 1
                case 6:
                    os.write(parent_conn, b"speed1")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                case 7:
                    os.write(parent_conn, b"forward")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                case _:
                    os.write(parent_conn, b"speed0") # reset speed to slow
                    delay_conn.send(0.3)
                    next_operation.stage = 0
                    next_operation.current_operation  = 300 # default forward
        case 600: # store forward to scan for retrieval
            match next_operation.stage: # which stage of operation?
                case 0:
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.4)
                    next_operation.stage += 1
                case 1:
                    rfid_i = True
                    print("retrieval forward operation")
                    os.write(parent_conn, b"forward")
                    delay_conn.send(10.0)
                    next_operation.stage += 1 # reset to NONE
                case 2:
                    if next_operation.rfid == "ENGINE":
                        print("Engine scanned, go forward on to turntable")
                        os.write(parent_conn, b"stop")
                        delay_conn.send(0.8)
                        next_operation.stage += 1
                    else:
                        print("Nothing is working, engine not scanned")
                        delay_conn.send(0.1)
                        next_operation.current_operation = -7000
                case 3:                                   ################### just engine decouple
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.4)
                    next_operation.stage += 1                   
                case 4:
                    os.write(parent_conn, b"backward") # tune this value for decoupling a single car from the train
                    delay_conn.send(3.75)
                    next_operation.stage += 1   
                case 5:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.5)
                    next_operation.stage += 1   
                case 6:                                   ##################### check to see if another car is scanned
                    os.write(parent_conn, b"forward")
                    delay_conn.send(0.9)
                    next_operation.stage += 1
                case 7:
                    os.write(parent_conn, b"backward") # tune this value for decoupling a single car from the train
                    delay_conn.send(1.3 + queue_adjust)
                    next_operation.stage += 1   
                case 8:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.5)
                    next_operation.stage += 1   
                case 9:                                   ##################### check to see if another car is scanned
                    os.write(parent_conn, b"forward")
                    delay_conn.send(2)
                    next_operation.stage += 1   
                case 10:                                   ##################### check to see if another car is scanned
                    rfid_i = True
                    os.write(parent_conn, b"forward")
                    delay_conn.send(4)
                    next_operation.stage += 1                                           
                case 11:
                    if next_operation.rfid == "ENGINE": # this is correct
                        next_operation.stage -= 1
                        delay_conn.send(0.1)
                        next_operation.rfid = ""
                    elif next_operation.rfid != "": # car scanned
                        os.write(parent_conn, b"stop") #  SOMETHING WAS SCANNED, RETRY decouple
                        delay_conn.send(0.1)
                        next_operation.current_operation = -6000 # retry sequence
                        next_operation.stage = 0
                    else: # the 5 second delay finished
                        delay_conn.send(0.1)
                        next_operation.stage += 1
                case 12:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage = -2
                    rfid_i = False
                    print("Currently Stored:", sorting_dict)
                    print("Retrieving:", next_operation.held_car)
                    next_operation.current_operation = -sorting_dict[next_operation.held_car] # start sorting
        case 300: # store forward to scan for storage
            match next_operation.stage: # which stage of operation?
                case 0:
                    rfid_i = True
                    print("retrieval forward operation")
                    next_operation.held_car = None
                    os.write(parent_conn, b"forward")
                    delay_conn.send(10.0)
                    next_operation.stage += 1 # reset to NONE
                case 1:
                    if next_operation.rfid == "ENGINE":
                        print("Engine scanned, do decoupling actions")
                        os.write(parent_conn, b"stop")
                        delay_conn.send(0.1)
                        next_operation.stage += 1
                    else:
                        print("Nothing is working")
                        delay_conn.send(0.1)
                        next_operation.current_operation = -7000
                case 2:                                   ################### single car + engine decouple
                    os.write(parent_conn, b"forward")
                    delay_conn.send(0.15)
                    next_operation.stage += 1                   
                case 3:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                case 4:
                    os.write(parent_conn, b"backward") # tune this for decoupler
                    delay_conn.send(0.70 + queue_adjust)
                    next_operation.stage += 1   
                case 5:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1.0)
                    next_operation.stage += 1   
                case 6:                                   ################### single car + engine decouple
                    os.write(parent_conn, b"forward")
                    delay_conn.send(0.52)
                    next_operation.stage += 1                   
                case 7:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                case 8:
                    os.write(parent_conn, b"backward") # tune this for decoupler
                    delay_conn.send(0.56)
                    next_operation.stage += 1   
                case 9:                                   ##################### check to see if another car is scanned
                    rfid_i = True
                    next_operation.rfid = ""
                    os.write(parent_conn, b"forward")
                    delay_conn.send(4)
                    next_operation.stage += 1                                           
                case 10:
                    if next_operation.rfid == "ENGINE": # this is correct
                        next_operation.stage -= 1
                        delay_conn.send(0.1)
                    elif next_operation.rfid != "": # car scanned
                        if next_operation.held_car == None or next_operation.held_car == next_operation.rfid:
                            next_operation.held_car = next_operation.rfid
                            next_operation.stage -= 1
                            delay_conn.send(0.1)
                            next_operation.rfid = ""
                        else:
                            os.write(parent_conn, b"stop") #  SOMETHING WAS SCANNED, RETRY decouple
                            delay_conn.send(0.1)
                            next_operation.current_operation = -5000 # retry sequence
                            next_operation.stage = 0
                    else: # the 5 second delay finished
                        print("Held car = ", next_operation.held_car)
                        delay_conn.send(0.1)
                        if next_operation.held_car != None: # an actual car was scanned, go sort
                            next_operation.stage += 1
                        else:
                            next_operation.stage = 0
                            next_operation.current_operation = -5000 # only the engine was scanned!!!  Go back and pick up car
                case 11:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    rfid_i = False
                    next_operation.stage = 0 # extra forward on start
                    next_operation.current_operation = sorting_dict[next_operation.held_car] # start sorting
        case b if b in [1,2,3,4,5,6]: # Sorting into bay 1-6
            match next_operation.stage: # which stage of operation?  
                case -2: # extra forward for start
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.1)
                    next_operation.stage += 1  
                case -1: # extra forward for restart
                    os.write(parent_conn, b"forward")
                    delay_conn.send(5.5)
                    next_operation.stage += 1                    
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
                    delay_conn.send(2)
                    turnTable(b) # rotate into the corresponding bay
                    next_operation.stage += 1
                case 4:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 5:
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.5)
                    next_operation.stage += 1
                case 6:
                    os.write(parent_conn, b"speed1")
                    delay_conn.send(0.3)
                    next_operation.stage += 1
                case 7:
                    bay_i = True # be interrupted when backing into bay
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.9)
                    next_operation.stage += 1
                case 8:
                    bay_i = False
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 9:
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                    #################################
                    # DECOUPLING OPERATION
                    ################################
                case 10:
                    os.write(parent_conn, b"forward") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(decouple_delay[next_operation.held_car][b])
                    next_operation.stage += 1
                    print("****delay chosen:", decouple_delay[next_operation.held_car][b])
                case 11:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 12: # repeat
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.25) # just changed for testing
                    next_operation.stage += 1
                case 13:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 14:
                    os.write(parent_conn, b"forward") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(1.2)
                    next_operation.stage += 1
                case 15:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 16: # repeat
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.1)
                    next_operation.stage += 1
                case 17:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 18:
                    os.write(parent_conn, b"forward") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(4.6)
                    next_operation.stage += 1
                case 19:
                    os.write(parent_conn, b"stop") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(1.0)
                    next_operation.stage += 1
                case 20:
                    delay_conn.send(2)
                    turnTable(0) # rotate back to straight
                    next_operation.stage += 1
                case 21:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 22:
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.2)
                    next_operation.stage += 1
                case 23:
                    rfid_i = True 
                    next_operation.rfid = ""
                    os.write(parent_conn, b"backward")
                    delay_conn.send(14)
                    next_operation.stage += 1
                case 24:
                    if next_operation.rfid == "ENGINE": # scanned the engine, ignore
                        os.write(parent_conn, b"speed3")
                        next_operation.stage += 1 # go back and continue
                    elif next_operation.rfid != "": # it scanned a car RESTART
                        next_operation.stage = -2 # extra forward time
                    else: # bay interrupt
                        rfid_i = False 
                        os.write(parent_conn, b"speed3")
                        next_operation.stage += 1
                    delay_conn.send(0.2)
                case 25:
                    bay_i = True
                    os.write(parent_conn, b"backward")
                    delay_conn.send(20)
                    next_operation.stage += 1
                case 26:  
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.2)
                    next_operation.stage += 1
                case 27:  
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.2)
                    next_operation.stage += 1
                case 28: # success
                    os.write(parent_conn, b"forward")
                    delay_conn.send(0.8)
                    next_operation.stage += 1
                case 29: # success
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.0)
                    next_operation.stage += 1
                case _:
                    os.write(parent_conn, b"speed0")
                    next_operation.stage = 0
                    # end operation
                    next_operation.current_operation = next_operation.repeat
                    delay_conn.send(2.5) # start going forward again after 4 second
                    return True # finished a full sequence
        case b if b in [-1,-2,-3,-4,-5,-6]: # retrieval sequence here
            match next_operation.stage:
                case -3: # extra extra forward for restart
                    os.write(parent_conn, b"forward")
                    delay_conn.send(4.1)
                    next_operation.stage += 1
                case -2: # extra forward for restart
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.1)
                    next_operation.stage += 1  
                case -1: # extra forward for restart
                    os.write(parent_conn, b"forward")
                    delay_conn.send(1.5)
                    next_operation.stage += 1                    
                case 0:
                    print("****starting BAY", b, "RETRIEVAL****")
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 1:
                    os.write(parent_conn, b"bell")
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                case 2:
                    os.write(parent_conn, b"bell")
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                case 3:
                    delay_conn.send(2)
                    turnTable(-b) # rotate into the corresponding bay
                    next_operation.stage += 1
                case 4:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 5:
                    os.write(parent_conn, b"backward")
                    delay_conn.send(2.5)
                    next_operation.stage += 1
                case 6:
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.2)
                    next_operation.stage += 1
                case 7:
                    bay_i = True # be interrupted when backing into bay
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.4)
                    next_operation.stage += 1
                case 8:
                    bay_i = False
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.5)
                    next_operation.stage += 1
                case 9:
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                    #################################
                    # DECOUPLING OPERATION
                    ################################
                case 10:
                    os.write(parent_conn, b"forward") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 11:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 12: # repeat
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 13:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 14:
                    os.write(parent_conn, b"forward") # go forward on to turn table
                    delay_conn.send(4.55)
                    next_operation.stage += 1
                case 15:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1.0)
                    next_operation.stage += 1
                case 16:
                    delay_conn.send(2)
                    turnTable(0) # rotate back to straight
                    next_operation.stage += 1
                case 17:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 18:
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.2)
                    next_operation.stage += 1
                case 19:
                    rfid_i = True 
                    next_operation.rfid = ""
                    os.write(parent_conn, b"backward")
                    delay_conn.send(14)
                    next_operation.stage += 1
                case 20:
                    if next_operation.rfid == "ENGINE" and next_operation.held_car == "": # scanned the engine, if held car is not NONE, restart, otherwise continue
                        os.write(parent_conn, b"speed2")
                        next_operation.stage += 1 # go continue
                    elif next_operation.rfid == "ENGINE" and next_operation.held_car != "": # scanned the engine, if held car not none, RESTART
                        rfid_i = False 
                        next_operation.stage = -3 # extra forward time
                    elif next_operation.rfid != "" and next_operation.rfid != "ENGINE": # it scanned a car
                        next_operation.held_car = ""
                        next_operation.stage -= 1 # go back up one stage
                    else: # ran out of time, no scan
                        rfid_i = False 
                        os.write(parent_conn, b"speed2")
                        next_operation.stage += 1
                    delay_conn.send(0.2)
                case 21: # success
                    bay_i = True
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 22: # success
                    bay_i = True
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.25)
                    next_operation.stage += 1
                case 23: # success
                    bay_i = True
                    os.write(parent_conn, b"backward")
                    delay_conn.send(20)
                    next_operation.stage += 1
                case 24: # success
                    os.write(parent_conn, b"stop")
                    delay_conn.send(0.2)
                    next_operation.stage += 1
                case 25: # success
                    os.write(parent_conn, b"forward")
                    delay_conn.send(0.8)
                    next_operation.stage += 1
                case 26: # success
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.0)
                    next_operation.stage += 1
                case _:
                    os.write(parent_conn, b"stop")
                    next_operation.stage = 0
                    # end operation
                    next_operation.current_operation = next_operation.repeat
                    delay_conn.send(3) # start going forward again after 4 second
                    return True # finished a full sequence
        case 1400: # test decoupling
            match next_operation.stage:
                case 0: 
                    print("****starting BAY STORAGE TEST****")
                    os.write(parent_conn, b"speed1")
                    delay_conn.send(0.2)
                    next_operation.stage += 1
                case 1:
                    bay_i = True # be interrupted when backing into bay
                    os.write(parent_conn, b"backward")
                    delay_conn.send(2.9)
                    next_operation.stage += 1
                case 2:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 3:
                    os.write(parent_conn, b"speed0")
                    delay_conn.send(0.1)
                    next_operation.stage += 1
                    #################################
                    # DECOUPLING OPERATION
                    ################################
                case 4:
                    os.write(parent_conn, b"forward") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(test)
                    next_operation.stage += 1
                    print("****delay chosen:", test)
                case 5:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 6: # repeat
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.2)
                    next_operation.stage += 1
                case 7:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 8:
                    os.write(parent_conn, b"forward") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(1.2)
                    next_operation.stage += 1
                case 9:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 10: # repeat
                    os.write(parent_conn, b"backward")
                    delay_conn.send(1.1)
                    next_operation.stage += 1
                case 11:
                    os.write(parent_conn, b"stop")
                    delay_conn.send(1)
                    next_operation.stage += 1
                case 12:
                    os.write(parent_conn, b"forward") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(4.9)
                    next_operation.stage += 1
                case 13:
                    os.write(parent_conn, b"stop") # go forward on top of the decoupler, but slightly past
                    delay_conn.send(1.0)
                    next_operation.stage += 1
                case _:   # done
                    cancel_op()
                    delay_conn.send(0.1) 
        case _:
            print("Current operation is NONE, stopping train")
            os.write(parent_conn, b"stop")
            next_operation.current_operation = None # continue doing nothing
    return False # still going

if __name__ == '__main__':
    child_conn, parent_conn = os.pipe() # connection pipe between this program, and the subprocess on the multiprocess
    agent = mp.Process(target=work, args = (child_conn,), daemon=True).start() # start multiprocess on other core for subprocess
    sys.exit(main(parent_conn))
