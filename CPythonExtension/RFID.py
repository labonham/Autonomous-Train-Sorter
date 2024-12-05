#!/usr/bin/env python

import pigpio
import pkt_send.lib as pkt

import pygame
import sys

if (pkt.initialize() == -1):
	sys.exit()

pygame.init()
window = pygame.display.set_mode((300, 300))
pygame.display.set_caption("Train Controller")
text = sys.stdin.read()
print("HELLO")
print(text)

run = 1
while(run):
	keys = pygame.key.get_pressed()
	
	if keys[pygame.K_UP]:
		pkt.forward(5);
	elif keys[pygame.K_DOWN]:
		pkt.backward(5);
	else:
		pkt.stop(5);
	
	if "GREEN" in text:
		pkt.function(5, 1);
	if "BLACK" in text:
		pkt.function(5, 4);
	
	for event in pygame.event.get():
		if event.type == pygame. QUIT:
			run = False

pygame.quit()
pkt.terminate();
