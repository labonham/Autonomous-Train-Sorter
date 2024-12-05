#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  command_station.py
#  
import sys
import pkt_send.lib as pkt
import select
    
def forward():
    pkt.forward(5);
    
def backward():
    pkt.backward(5);

def stop():
    pkt.stop(5);
    
def function():
    pkt.function(5, 3)#Changed from 5,0

def function1():
    pkt.function(5, 1)

def flip():
    pkt.flip(1);
    
def idle():
    pkt.idle(1);

def main(args):
    if (pkt.initialize() == -1):
        return -1
    print("**************GPIO INITIALIZED***************")
    # initalize space
    text_input = None
    toggle = 1
    
    epoll = select.epoll()
    epoll.register(sys.stdin, select.EPOLLIN)
    while(1):
        events = epoll.poll(0)
        for fd, event in events:
            text_input = sys.stdin.read()
            print(text_input)
            if 'term' in text_input:
                print("**************GPIO TERMINATED***************")
                pkt.terminate();
                return 0
            elif 'forward' in text_input:
                forward()
            elif 'backward' in text_input:
                backward()
            elif 'function' in text_input:
                function1()
            elif 'stop' in text_input:
                stop()
                function()#added to end long horn
            continue
        idle()

    
    pkt.terminate();
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
