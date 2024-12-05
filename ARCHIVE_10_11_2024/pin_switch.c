/*
 * pin_switch.c
 * 
 * Copyright 2024  <traingroup@raspberrypi>
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 * 
 * 
 */

#include <pigpio.h>
#include <stdio.h>
#include <unistd.h>

int outPin = 17;
int outPin2 = 27;

static char preamble 	= 	0b11111111;
static char start	 	= 	0b0;
static char end			= 	0b1;

struct Packet forward_p;
struct Packet backward_p;

struct Packet {
    char addr;
	char data;
	char error;
};

void sendByte(char bytes, int count) {
	char mask = 0b00000001 << (count-1);
	
	for (int i = 0; i < count; i++)
	{
		if (bytes & mask)
		{
			gpioWrite(outPin, 0);
			gpioWrite(outPin2, 1);
			gpioDelay(58);
			gpioWrite(outPin, 1);
			gpioWrite(outPin2, 0);
			gpioDelay(58);
		} else
		{
			gpioWrite(outPin, 0);
			gpioWrite(outPin2, 1);
			gpioDelay(100);
			gpioWrite(outPin, 1);
			gpioWrite(outPin2, 0);
			gpioDelay(100);
		}
		mask = mask >> 1;
	}
}

void forward(int n) {
	forward_p.addr 	= 	3; 
	forward_p.data 	= 	0b01100011; 
	forward_p.error = forward_p.addr^forward_p.data;
	for (int i = 0; i < n; i++)
	{
		sendByte(preamble, 8);
		sendByte(preamble, 4);
        sendByte(start, 1);
        sendByte(forward_p.addr, 8);
        sendByte(start, 1);
        sendByte(forward_p.data, 8);
        sendByte(start, 1);
        sendByte(forward_p.error, 8);
        sendByte(end, 1);
	}
}

void backward(int n) {
	backward_p.addr 	= 	3; 
	backward_p.data 	= 	0b01000011; 
	backward_p.error = backward_p.addr^backward_p.data;
	for (int i = 0; i < n; i++)
	{
		sendByte(preamble, 8);
		sendByte(preamble, 4);
        sendByte(start, 1);
        sendByte(backward_p.addr, 8);
        sendByte(start, 1);
        sendByte(backward_p.data, 8);
        sendByte(start, 1);
        sendByte(backward_p.error, 8);
        sendByte(end, 1);
	}
}

void stop(int n) {
	for (int i = 0; i < n; i++)
	{
		sendByte(preamble, 8);
		sendByte(preamble, 4);
        sendByte(start, 1);
        sendByte(3, 8);
        sendByte(start, 1);
        sendByte(0b01000000, 8);
        sendByte(start, 1);
        sendByte(backward_p.error, 8);
        sendByte(end, 1);
	}
}

int main()
{
	if (gpioInitialise() == -1) {
		return -1;
	}
	gpioSetMode(outPin, PI_OUTPUT);
	gpioSetMode(outPin2, PI_OUTPUT);	
	
	while (1) {
        stop(100);
        backward(200);
		stop(100);
		forward(200);
	}
	return 0;
}
