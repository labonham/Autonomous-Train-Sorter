from cffi import FFI
ffibuilder = FFI()
ffibuilder.cdef("""
void forward(int n);
void backward(int n);
void stop(int n);
void idle(int n);
void function(int n, int type);
void flip(int forward);
int initialize();
int terminate();
""")
ffibuilder.set_source("pkt_send","""
#include "packet_sender.h"
#include <pigpio.h>
#include <stdio.h>
#include <unistd.h>
""", sources=["packet_sender.c"], library_dirs = [], libraries =['pigpio'])
ffibuilder.compile()
