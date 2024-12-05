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
#clock
import datetime

# RFID Modules
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

import fcntl

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
        delay_time = child_conn.recv()
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(seconds=delay_time)
        if delay_time < 0:
            break
        while datetime.datetime.now() < end_time:
            #print("end_time: ", end_time - datetime.datetime.now())
            events = epoll.poll(0)
            for fd, event in events:
                start_time = datetime.datetime.now()
                end_time = start_time + datetime.timedelta(seconds=child_conn.recv())
        #print("AAAHH")
        delay_time = 0
        child_conn.send("done")

def main(parent_conn):
    pygame.init()
    window = pygame.display.set_mode((300, 300))
    pygame.display.set_caption("Train Controller")
    delay_conn, child_conn = mp.Pipe()
    process = mp.Process(target=delay, args=(child_conn,))
    process.start()
    
    epoll = select.epoll()
    epoll.register(delay_conn, select.EPOLLIN)
    
    reader = SimpleMFRC522()


    # main loop
    run = 1
    stageone=1
    while(run):
        keys = pygame.key.get_pressed()
        
        id, text = reader.read_no_block()
        events = epoll.poll(0)
        for fd,event in events:
            print("Done Waiting")
            stageone = 1
            delay_conn.recv()
        if text:
            if "GREEN" in text:
                print(text)
                os.write(parent_conn, b"function")
                delay_conn.send(5)
            elif "ITOLERATETRAINS" in text:
                os.write(parent_conn, b"forward")
                delay_conn.send(2)
        elif keys[pygame.K_UP] and stageone:
            os.write(parent_conn, b"forward")
            stageone=0
            delay_conn.send(2)
        elif keys[pygame.K_DOWN]:
            os.write(parent_conn, b"backward")
        elif keys[pygame.K_1]:
            os.write(parent_conn, b"flip")
        else:
            os.write(parent_conn, b"stop")
        for event in pygame.event.get():
            if event.type == pygame. QUIT:
                os.write(parent_conn, b"term")
                delay_conn.send(-1)
                run = False
                
    # clean up
    pygame.quit()
    GPIO.cleanup()
    
    return 0

if __name__ == '__main__':
    child_conn, parent_conn = os.pipe() # connection pipe between this program, and the subprocess on the multiprocess
    agent = mp.Process(target=work, args = (child_conn,), daemon=True).start() # start multiprocess on other core for subprocess
    sys.exit(main(parent_conn))
