#!/usr/bin/env python
# coding: utf-8

# In[7]:


import pygame
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DCC GUI")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)

# Color names mapping
color_names = {
    RED: "RED",
    GREEN: "GREEN",
    BLUE: "BLUE",
    YELLOW: "YELLOW",
    ORANGE: "ORANGE",
    PURPLE: "PURPLE",
}

# Fonts
font = pygame.font.SysFont(None, 36)

# Block class
class Block(pygame.sprite.Sprite):
    def __init__(self, color, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.color = color
        self.dragging = False

    def update(self, pos):
        if self.dragging:
            self.rect.topleft = (pos[0] - 20, pos[1] - 20)

# Zones
zones = {
    "left": pygame.Rect(50, 200, 350, 350),
    "middle": pygame.Rect(420, 200, 400, 400),
    "right": pygame.Rect(830, 200, 350, 350),
}

# Block setup
colors = [RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE]
blocks = pygame.sprite.Group()
start_x = 150
for i, color in enumerate(colors):
    block = Block(color, start_x + i * 60, 50)
    blocks.add(block)

# Dictionary to store block positions
block_positions = {
    "left": [],
    "middle": [],
    "right": []
}

# Button setup
go_button = pygame.Rect(450, 620, 100, 50)
button_scale_factor = 1.1  # Scale factor for the button animation
is_button_pressed = False

# Slot setup for middle circle
circle_center = (620, 400)
circle_radius = 100
num_slots = 6
slot_radius = 15
line_length = 40

# Initialize color positions
color_positions = {}

# Main game loop
running = True
dragging_block = None
while running:
    screen.fill(WHITE)

    # Draw zones
    pygame.draw.rect(screen, BLACK, zones["left"], 2)
    screen.blit(font.render("Left", True, BLACK), (150, 450))

    pygame.draw.rect(screen, BLACK, zones["middle"], 2)
    pygame.draw.circle(screen, BLACK, circle_center, circle_radius, 2)

    # Draw lines pointing to the locking points outside the circle
    for i in range(num_slots):
        angle = (math.pi / num_slots) * (i + 0.5)
        line_start = (circle_center[0] + int(circle_radius * math.cos(angle)),
                      circle_center[1] + int(circle_radius * math.sin(angle)))
        line_end = (circle_center[0] + int((circle_radius + line_length) * math.cos(angle)),
                    circle_center[1] + int((circle_radius + line_length) * math.sin(angle)))
        pygame.draw.line(screen, BLACK, line_start, line_end, 3)

        locking_point_x = circle_center[0] + int((circle_radius + line_length) * math.cos(angle))
        locking_point_y = circle_center[1] + int((circle_radius + line_length) * math.sin(angle))
        pygame.draw.circle(screen, BLACK, (locking_point_x, locking_point_y), slot_radius, 2)

    # Draw designated slots in the left zone
    for i in range(num_slots):
        slot_x = 60 + i * 50 + 10
        pygame.draw.rect(screen, BLACK, (slot_x, 480, 40, 40), 2)

    # Draw designated slots in the right zone
    for i in range(num_slots):
        slot_x = 830 + i * 50 + 10
        pygame.draw.rect(screen, BLACK, (slot_x, 480, 40, 40), 2)

    pygame.draw.rect(screen, BLACK, zones["right"], 2)
    screen.blit(font.render("Right", True, BLACK), (880, 450))

    # Draw blocks
    blocks.draw(screen)

    # Draw Go button with scaling effect
    scaled_button = go_button.inflate((go_button.width * (button_scale_factor - 1)), (go_button.height * (button_scale_factor - 1))) if is_button_pressed else go_button
    pygame.draw.rect(screen, GREEN, scaled_button)
    screen.blit(font.render("GO", True, WHITE), (scaled_button.x + 15, scaled_button.y + 10))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for block in blocks:
                    if block.rect.collidepoint(event.pos):
                        block.dragging = True
                        dragging_block = block
                        break

                if go_button.collidepoint(event.pos):
                    is_button_pressed = True  # Start button animation

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if dragging_block:
                    for zone_name, zone_rect in zones.items():
                        if zone_rect.colliderect(dragging_block.rect):
                            if zone_name == "middle":
                                for i in range(num_slots):
                                    angle = (math.pi / num_slots) * (i + 0.5)
                                    line_x = circle_center[0] + int((circle_radius + line_length) * math.cos(angle))
                                    line_y = circle_center[1] + int((circle_radius + line_length) * math.sin(angle))
                                    if dragging_block.rect.collidepoint((line_x, line_y)):
                                        block_positions["middle"].append(dragging_block.color)
                                        dragging_block.rect.center = (line_x, line_y)
                                        dragging_block.dragging = False
                                        break
                            else:
                                for j in range(num_slots):
                                    slot_x = 60 + j * 50 + 10 if zone_name == "left" else 830 + j * 50 + 10
                                    slot_rect = pygame.Rect(slot_x, 480, 40, 40)
                                    if slot_rect.colliderect(dragging_block.rect):
                                        block_positions[zone_name].append(dragging_block.color)
                                        dragging_block.rect.topleft = slot_rect.topleft
                                        dragging_block.dragging = False
                                        break
                            break
                    dragging_block = None

                # Check and update block variables only when GO is pressed
                if is_button_pressed:
                    color_positions.clear()  # Clear previous positions

                    # Update block variables based on positions
                    for zone, colors in block_positions.items():
                        for color in colors:
                            color_name = color_names[color]  # Get the name of the color
                            if zone == "left":
                                index = block_positions["left"].index(color) + 1  # 1 to 6 for left zone
                                color_positions[color_name] = index  
                            elif zone == "middle":
                                index = block_positions["middle"].index(color) + 7  # 7 to 12 for middle zone
                                color_positions[color_name] = index  
                            elif zone == "right":
                                index = block_positions["right"].index(color) + 13  # 13 to 18 for right zone
                                color_positions[color_name] = index  

                    # Print the color positions based on the blocks
                    for color_name, position in color_positions.items():
                        print(f"{color_name}: {position}")

                is_button_pressed = False  # Reset button animation

        elif event.type == pygame.MOUSEMOTION:
            if dragging_block:
                dragging_block.update(event.pos)

    pygame.display.flip()
    pygame.time.Clock().tick(60)

pygame.quit()


# In[ ]:




