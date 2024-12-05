#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import subprocess
import sys

reader = SimpleMFRC522()

id, text = reader.read()
	
print(text)
		
GPIO.cleanup()
