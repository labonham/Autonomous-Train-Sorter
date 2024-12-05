#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  worker.py
#  
import sys
from time import sleep

i = 0
while (i < 100000):
    text_input = sys.stdin.read()
    if text_input:
        print(text_input)
    else:
        print("no signal")
    if 'term' in text_input:
        break
    #sleep(0.1)
    i += 1
