#include "packet_sender.h"
#include <pigpio.h>
#include <stdio.h>
#include <unistd.h>

int outPin = 17;
int outPin2 = 27;

static int savedTurnout = 23;
static int savedTurnout2 = 22;

int turnoutPin = 23;
int turnoutPin2 = 22;

static char preamble 	= 	0b11111111;
static char start	 	= 	0b0;
static char end			= 	0b1;

struct Packet {
    char addr;
	char data;
	char error;
};

struct Packet forward_p;
struct Packet backward_p;

static char function1_array = 0b10000000;
static char function2_array = 0b10110000;

char speed_set 		= 0b01000011;
char forward_set	= 0b00100000;
char backward_set	= 0b00000000;

void sendByte(char bytes, int count) {
	char mask = 0b00000001 << (count-1);
	
	for (int i = 0; i < count; i++)
	{
		if (bytes & mask)
		{
			gpioWrite(outPin, 0);
			gpioWrite(savedTurnout, 0);
			gpioWrite(outPin2, 1);
			gpioWrite(savedTurnout2,1);
			gpioDelay(58);
			gpioWrite(outPin, 1);
			gpioWrite(savedTurnout, 1);
			gpioWrite(outPin2, 0);
			gpioWrite(savedTurnout2, 0);
			gpioDelay(58);
		} else
		{
			gpioWrite(outPin, 0);
			gpioWrite(savedTurnout, 0);
			gpioWrite(outPin2, 1);
			gpioWrite(savedTurnout2,1);
			gpioDelay(100);
			gpioWrite(outPin, 1);
			gpioWrite(savedTurnout, 1);
			gpioWrite(outPin2, 0);
			gpioWrite(savedTurnout2, 0);
			gpioDelay(100);
		}
		mask = mask >> 1;
	}
}

void forward(int n) {
	for (int i = 0; i < n; i++)
	{
		sendByte(preamble, 8);
		sendByte(preamble, 4);
		sendByte(start, 1);
		sendByte(forward_p.addr, 8);
		sendByte(start, 1);
		sendByte(speed_set | forward_set, 8);
		sendByte(start, 1);
		sendByte((speed_set | forward_set)^forward_p.addr, 8);
		sendByte(end, 1);
	}
}

void backward(int n) {
	for (int i = 0; i < n; i++)
	{
		sendByte(preamble, 8);
		sendByte(preamble, 4);
		sendByte(start, 1);
		sendByte(backward_p.addr, 8);
		sendByte(start, 1);
		sendByte(speed_set | backward_set, 8);
		sendByte(start, 1);
		sendByte((speed_set | backward_set)^forward_p.addr, 8);
		sendByte(end, 1);
	}
}

void stop(int n) {
	char addr 	= 3;
	char data 	= 0b01100000;
	char error 	= addr^data;
	for (int i = 0; i < n; i++)
	{
		sendByte(preamble, 8);
		sendByte(preamble, 4);
		sendByte(start, 1);
		sendByte(addr, 8);
		sendByte(start, 1);
		sendByte(data, 8);
		sendByte(start, 1);
		sendByte(error, 8);
		sendByte(end, 1);
	}
}

void idle(int n) {
	char addr 	= 0b11111111;
	char data 	= 0b00000000;
	char error 	= addr^data;
	for (int i = 0; i < n; i++)
	{
		sendByte(preamble, 8);
		sendByte(preamble, 4);
		sendByte(start, 1);
		sendByte(addr, 8);
		sendByte(start, 1);
		sendByte(data, 8);
		sendByte(start, 1);
		sendByte(error, 8);
		sendByte(end, 1);
	}
}

/*
 * Function group A activated as a group
 * 0 - bell
 * 1 - long horn
 * 2 - short horn (activates on toggle)
 * 3 - nothing
 * 4 - headlight
 * Function group B activated as a group
 * 5 - nothing
 * 6 - nothing
 * 7 - dimmer
 * 8 - mute
 * */

void function(int n, int type, int set) {
	char addr 	= 3;
	char mask;
	char data;
	char error;
	if (type < 5) {
		mask 	= 0b00000001 << (type);
		if (set) {
			function1_array = function1_array | mask;
		} else {
			function1_array = function1_array & (~mask);
		}
		data = function1_array;
	} else { // great than 5 use function group 2
		mask 	= 0b00000001 << (type-5);
		if (set) {
			function2_array = function2_array | mask;
		} else {
			function2_array = function2_array & (~mask);
		}
		data = function2_array;
	}
	error 	= addr^data;
	for (int i = 0; i < n; i++)
	{
		sendByte(preamble, 8);
		sendByte(preamble, 4);
		sendByte(start, 1);
		sendByte(addr, 8);
		sendByte(start, 1);
		sendByte(data, 8);
		sendByte(start, 1);
		sendByte(error, 8);
		sendByte(end, 1);
	}
}

void speed(int speed) {
	switch (speed) {
		case 0:
			speed_set 	= 0b01000011;
			break;
		case 1:
			speed_set 	= 0b01000101;
			break;
	}
}

void flip(int forward) {
	if (forward) {
		savedTurnout = turnoutPin;
		savedTurnout2 = turnoutPin2;
	} else {
		savedTurnout = turnoutPin2;
		savedTurnout2 = turnoutPin;	
	}	
}

int initialize()
{
	if (gpioInitialise() == -1) {
		return -1;
	}
	gpioSetMode(outPin, PI_OUTPUT);
	gpioSetMode(outPin2, PI_OUTPUT);
	gpioSetMode(turnoutPin, PI_OUTPUT);
	gpioSetMode(turnoutPin2, PI_OUTPUT);
	
	// set up the forward and backward packets and their addressess
	forward_p.addr 		= 	3; 
	forward_p.data	 	= 	0b01100101; 
	forward_p.error = forward_p.addr^forward_p.data;

	backward_p.addr 	= 	3; 
	backward_p.data 	= 	0b01000101; 
	backward_p.error = backward_p.addr^backward_p.data;

	return 0;
}

int terminate()
{
	gpioWrite(outPin, 0);
	gpioWrite(outPin2, 0);
	gpioWrite(turnoutPin, 0);
	gpioWrite(turnoutPin2, 0);
	gpioTerminate();
	return 0;
}
