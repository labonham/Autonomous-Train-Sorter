#include "addme.h"
#include <pigpio.h>
#include <stdio.h>
#include <unistd.h>

int addme(int a, int b){
	if (gpioInitialise() == -1) {
		return -1;
	}
	gpioSetMode(17, PI_OUTPUT);
	gpioSetMode(27, PI_OUTPUT);
	gpioTerminate();
	
	return (a + b);
}
