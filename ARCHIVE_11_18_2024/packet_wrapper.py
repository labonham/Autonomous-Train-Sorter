#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  command_station.py
#  
import sys
import pkt_send.lib as pkt
import select
    
def forward():
    pkt.forward(16);
    
def backward():
    pkt.backward(16);

def stop():
    pkt.stop(14);
    
def function():
    pkt.function(5, 2, 1)#Activate bell

def function1():
    pkt.function(5, 2, 0)#Deactivate bell
    
def bell(n):
    pkt.function(5,0,n)
    
def mute(n):
    pkt.function(5,8,n)
    
def speed0():
    pkt.speed(0);

def speed1():
    pkt.speed(1);
    
def speed2():
    pkt.speed(2);
    
def speed3():
    pkt.speed(3);

def flip1():
    pkt.flip(1);
    
def flip2():
    pkt.flip(0);
    
def horn(n):
    pkt.function(5,2,n)
    
def long_horn(n):
    pkt.function(5,1,n)

def light(n):
    pkt.function(5,4,n)
    
def idle():
    pkt.idle(1);

def main(args):
    if (pkt.initialize() == -1):
        return -1
    print("**************GPIO INITIALIZED***************")
    # initalize space
    text_input = None
    
    n = 0
    m = 0
    h = 0
    l = 0
    o = 0
    
    epoll = select.epoll()
    epoll.register(sys.stdin, select.EPOLLIN)
    while(1):
        events = epoll.poll(0)
        if not events:
            idle()
        for fd, event in events:
            text_input = sys.stdin.read()
            print("wrapper: ", text_input)
            if 'term' in text_input:
                print("**************GPIO TERMINATED***************")
                pkt.terminate();
                return 0
            elif 'forward' in text_input:
                forward()
            elif 'backward' in text_input:
                backward()
            elif 'bell' in text_input:
                n = 1-n
                bell(n)
            elif 'mute' in text_input:
                m = ~m
                mute(m)
            elif 'function0' in text_input:
                function()
            elif 'function1' in text_input:
                function1()
            elif 'speed0' in text_input:
                speed0()
            elif 'speed1' in text_input:
                speed1()
            elif 'speed2' in text_input:
                speed1() # intentional
            elif 'speed3' in text_input:
                speed3()
            elif 'flip1' in text_input:
                flip1()
            elif 'flip2' in text_input:
                flip2()
            elif 'longhorn' in text_input:
                o = ~o
                long_horn(o)
            elif 'horn' in text_input:
                h = ~h
                horn(h)
            elif 'lights' in text_input:
                l = ~l
                light(l)
            elif 'stop' in text_input:
                stop()

    
    pkt.terminate();
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
