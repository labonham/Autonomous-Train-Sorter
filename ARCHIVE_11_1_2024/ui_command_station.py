#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  ui_command_station.py
#
import pygame
import math
import sys
################################################################## UI INIT ################################################
screen = None
def init():
    pygame.init()
    # Screen dimensions
    WIDTH, HEIGHT = 1200, 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DCC GUI")
    return screen

# Colors
BLACK = (0, 0, 0)
WHITEBACKGROUND = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
WHITE = (225, 225, 225)

# Color names mapping
color_names = {
    RED: "RED",
    GREEN: "GREEN",
    BLUE: "BLUE",
    YELLOW: "YELLOW",
    ORANGE: "ORANGE",
    WHITE: "WHITE",
}

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

###################################################################

def ui_loop(screen, block_positions, queue_positions):
    # font
    font = pygame.font.SysFont(None, 36)
    # Zones
    zones = {
        "middle": pygame.Rect(420, 200, 400, 400),
        "queue": pygame.Rect(830, 200, 350, 350),
    }
    
    # Dictionary to store block positions
    if block_positions == None:
        block_positions = {}
    # Array for queue
    if queue_positions == None:
        queue_positions = []

    # Slot setup for middle circle
    circle_center = (620, 400)
    circle_radius = 100
    num_slots = 6
    slot_radius = 15
    line_length = 40

    # Block setup
    colors = [RED, GREEN, BLUE, YELLOW, ORANGE, WHITE]
    blocks = pygame.sprite.Group()
    start_x = 150
    for i, color in enumerate(colors):
        block = Block(color, start_x + i * 60, 50)
        blocks.add(block)
        if color in block_positions:
           angle = -(math.pi / num_slots) * (block_positions[color] + 0.5)
           line_x = circle_center[0] + int((circle_radius + line_length) * math.cos(angle))
           line_y = circle_center[1] + int((circle_radius + line_length) * math.sin(angle))
           block.rect.center = (line_x, line_y)   


    # Button setup
    go_button = pygame.Rect(450, 620, 100, 50)
    button_scale_factor = 1.1  # Scale factor for the button animation
    is_button_pressed = False

    assemble_button = pygame.Rect(580, 620, 250, 50)
    is_assemble_pressed = False
        
    manual_button = pygame.Rect(300, 620, 120, 50)
    manual_button_pressed = False

    # Initialize color positions
    color_positions = {}

    # Initialize color queue
    color_queue = []
    # Main game loop
    running = True
    dragging_block = None
    while running:
            screen.fill(WHITEBACKGROUND)

            # Draw zones
            pygame.draw.rect(screen, BLACK, zones["queue"], 2)
            screen.blit(font.render("Queue", True, BLACK), (880, 450))

            pygame.draw.rect(screen, BLACK, zones["middle"], 2)
            pygame.draw.circle(screen, BLACK, circle_center, circle_radius, 2)

            # Draw lines pointing to the locking points outside the circle
            for i in range(num_slots):
                    angle = -(math.pi / num_slots) * (i + 0.5)
                    line_start = (circle_center[0] + int(circle_radius * math.cos(angle)),
                                              circle_center[1] + int(circle_radius * math.sin(angle)))
                    line_end = (circle_center[0] + int((circle_radius + line_length) * math.cos(angle)),
                                            circle_center[1] + int((circle_radius + line_length) * math.sin(angle)))
                    pygame.draw.line(screen, BLACK, line_start, line_end, 3)

                    locking_point_x = circle_center[0] + int((circle_radius + line_length) * math.cos(angle))
                    locking_point_y = circle_center[1] + int((circle_radius + line_length) * math.sin(angle))
                    pygame.draw.circle(screen, BLACK, (locking_point_x, locking_point_y), slot_radius, 2)

            # Draw designated slots in the right zone
            for i in range(num_slots):
                    slot_x = 830 + i * 50 + 10
                    pygame.draw.rect(screen, BLACK, (slot_x, 480, 40, 40), 2)


            # Draw blocks
            blocks.draw(screen)

            # Draw GO button with scaling effect
            scaled_button = go_button.inflate((go_button.width * (button_scale_factor - 1)), (go_button.height * (button_scale_factor - 1))) if is_button_pressed else go_button
            pygame.draw.rect(screen, GREEN, scaled_button)
            screen.blit(font.render("STORE", True, BLACK), (scaled_button.x + 10, scaled_button.y + 10))

            # Draw ASSEMBLE button with scaling effect
            scaled_button2 = assemble_button.inflate((assemble_button.width * (button_scale_factor - 1)), (assemble_button.height * (button_scale_factor - 1))) if is_button_pressed else assemble_button
            pygame.draw.rect(screen, ORANGE, scaled_button2)
            screen.blit(font.render("ASSEMBLE", True, BLACK), (scaled_button2.x + 60, scaled_button2.y + 10))

            # Draw ASSEMBLE button with scaling effect
            scaled_button3 = manual_button.inflate((manual_button.width * (button_scale_factor - 1)), (manual_button.height * (button_scale_factor - 1))) if is_button_pressed else manual_button
            pygame.draw.rect(screen, YELLOW, scaled_button3)
            screen.blit(font.render("MANUAL", True, BLACK), (scaled_button3.x + 10, scaled_button3.y + 10))

            # Event handling
            for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                            running = False

                    elif event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 1:
                                    for block in blocks:
                                            if block.rect.collidepoint(event.pos): # empty either queue or bays of block
                                                    block.dragging = True
                                                    dragging_block = block
                                                    if color_names[dragging_block.color] in block_positions:
                                                        del block_positions[dragging_block.color]
                                                    if color_names[dragging_block.color] in queue_positions:
                                                        queue_positions.remove(dragging_block)
                                                    break
                                    # update the queue to fill in if the block was in the queue
                                    if dragging_block in queue_positions:
                                        for i in range(queue_positions.index(dragging_block), len(queue_positions) - 1):
                                            slot_x = 1080 - i * 50 + 10
                                            slot_rect = pygame.Rect(slot_x, 480, 40, 40)
                                            queue_positions[i + 1].rect.topleft = slot_rect.topleft
                                            queue_positions[i] = queue_positions[i + 1]
                                        queue_positions = queue_positions[:-1] # delete last entry
                                                                            
                            if go_button.collidepoint(event.pos):
                                button_scale_factor = 0.9
                    elif event.type == pygame.MOUSEBUTTONUP:
                            is_button_pressed = go_button.collidepoint(event.pos)
                            is_assemble_pressed = assemble_button.collidepoint(event.pos)
                            is_manual_pressed = manual_button.collidepoint(event.pos)
                                
                            if event.button == 1:
                                    if dragging_block:
                                            for zone_name, zone_rect in zones.items():
                                                    if zone_rect.colliderect(dragging_block.rect):
                                                            if zone_name == "middle":
                                                                    for i in range(num_slots):
                                                                            angle = -(math.pi / num_slots) * (i + 0.5)
                                                                            line_x = circle_center[0] + int((circle_radius + line_length) * math.cos(angle))
                                                                            line_y = circle_center[1] + int((circle_radius + line_length) * math.sin(angle))
                                                                            if dragging_block.rect.collidepoint((line_x, line_y)):
                                                                                    block_positions[color_names[dragging_block.color]] = i
                                                                                    dragging_block.rect.center = (line_x, line_y)
                                                                                    dragging_block.dragging = False
                                                                                    break
                                                            else:
                                                                    collision = False
                                                                    for j in range(num_slots): # check each slot
                                                                            slot_x = 830 + j * 50 + 10
                                                                            slot_rect = pygame.Rect(slot_x, 480, 400, 400)
                                                                            print(dragging_block.rect.topleft, slot_rect.topleft)
                                                                            if slot_rect.colliderect(dragging_block.rect):
                                                                                    collision = True
                                                                                    dragging_block.dragging = False
                                                                                    break
                                                                    if collision:
                                                                        if not color_names[dragging_block.color] in queue_positions:
                                                                            slot_x = 1080 - len(queue_positions) * 50 + 10
                                                                            slot_rect = pygame.Rect(slot_x, 480, 40, 40)
                                                                            dragging_block.rect.topleft = slot_rect.topleft # snap
                                                                            queue_positions.append(dragging_block) # add to end the queue
                                                            break
                                            dragging_block = None

                                    # Check and update block variables only when GO is pressed
                                    if is_button_pressed:
                                            color_positions.clear()  # Clear previous positions

                                            # Update block variables based on positions
                                            for color, pos in block_positions.items():
                                                    print(pos, color)
                                                    color_name = color  # Get the name of the color
                                                    index = block_positions[color] + 1  # 1 to 6 for left zone
                                                    color_positions[color_name] = index

                                            # Print the color positions based on the blocks
                                            for color_name, position in color_positions.items():
                                                    print(f"{color_name}: {position}")
                                            screen.blit(font.render("STORING...", True, BLACK), (560, 550))
                                            pygame.display.flip()
                                            return ['store', color_positions]

                                    
                                    
                                    if is_assemble_pressed:
                                            color_queue.clear()  # Clear previous positions

                                            # Update block variables based on positions
                                            for block in queue_positions:
                                                    color_queue.append(color_names[block.color])  # Get the name of the color

                                            # Print the color positions based on the blocks
                                            for color in color_queue:
                                                    print(f"{color}")
                                            screen.blit(font.render("ASSEMBLING...", True, BLACK), (530, 550))
                                            pygame.display.flip()
                                            return ['assemble', color_queue]
                                    
                                    if is_manual_pressed:
                                            screen.blit(font.render("MANUAL... (press e to end)", True, BLACK), (470, 550))
                                            pygame.display.flip()
                                            return ['manual', None]
                    elif event.type == pygame.MOUSEMOTION: # drag the block
                            if dragging_block:
                                    dragging_block.update(event.pos)

            pygame.display.flip()
            pygame.time.Clock().tick(60)
    return ['term', None]

if __name__ == '__main__':
    screen = init()
    block_positions = {}
    while(1):
        ui_loop(screen, block_positions, None)
