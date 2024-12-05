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
BROWN = (150, 75, 0)
GRAY = (75, 75, 75)

# Color names mapping
color_names = {
    RED: "RED",
    GREEN: "GREEN",
    BLUE: "BLUE",
    YELLOW: "YELLOW",
    ORANGE: "ORANGE",
    BROWN: "BROWN",
    WHITE: "WHITE",
    BLACK: "BLACK",
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
startup = 0
locked = []

def ui_loop(screen, block_positions, queue_positions):
    global locked, startup
    # font
    font = pygame.font.SysFont(None, 36)
    fontSmall = pygame.font.SysFont(None, 22)
    # Zones
    zones = {
        "middle": pygame.Rect(420, 200, 400, 400),
        "queue": pygame.Rect(830, 200, 350, 350),
    }
    # Dictionary to store block positions
    if block_positions == None:
        block_positions = {}
    old_block_positions = {} 
    # Array for queue
    if queue_positions == None:
        queue_positions = []
    if len(block_positions) == 0 and len(queue_positions) == 0:
        ui_stage = 0   # startup
    elif len(queue_positions) == 0:
        ui_stage = 2   # next step is assembling
        old_block_positions = block_positions.copy()
    else:
        ui_stage = 1   # next step is storage (there's stuff in the queue to store)

    # Slot setup for middle circle
    circle_center = (620, 400)
    circle_radius = 100
    num_slots = 6
    slot_radius = 15
    line_length = 40
    
    # locks for user restriction
    img = pygame.image.load("lock.bmp").convert()
    img.set_colorkey((255,255,255))
    img = pygame.transform.scale(img, (35,35))
    
    # Block setup
    colors = [RED, GREEN, BROWN, BLACK]#, BLUE, YELLOW, ORANGE, WHITE]
    blocks = pygame.sprite.Group()
    start_x = 150
    for i, color in enumerate(colors):
        block = Block(color, start_x + i * 60, 50)
        blocks.add(block)
        if color_names[color] in block_positions:
            angle = -(math.pi / num_slots) * (block_positions[color_names[color]]-1 + 0.5)
            line_x = circle_center[0] + int((circle_radius + line_length) * math.cos(angle))
            line_y = circle_center[1] + int((circle_radius + line_length) * math.sin(angle))
            block.rect.center = (line_x, line_y)   
           
        if color_names[block.color] in queue_positions:
            slot_x = 1080 - queue_positions.index(color_names[block.color]) * 50 + 10
            slot_rect = pygame.Rect(slot_x, 480, 40, 40)
            block.rect.topleft = slot_rect.topleft
            if color_names[block.color] in block_positions:  # empty bays of block
                del block_positions[color_names[block.color]]


    # Button setup
    go_button = pygame.Rect(450, 620, 100, 50)
    button_scale_factor = 1.1  # Scale factor for the button animation
    is_button_pressed = False

    assemble_button = pygame.Rect(580, 620, 250, 50)
    is_assemble_pressed = False
        
    manual_button = pygame.Rect(300, 620, 120, 50)
    
    control_button = pygame.Rect(300, 680, 200, 50)

    # Initialize color positions
    color_positions = {}

    # Initialize color queue
    color_queue = []
    # Main game loop
    running = True
    dragging_block = None
    error = 0

    old_block_pos = (0,0);

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
            for block in blocks:
                if color_names[block.color] in locked:
                    screen.blit(img,block.rect.topleft)

            # Draw GO button with scaling effect
            scaled_button = go_button.inflate((go_button.width * (button_scale_factor - 1)), (go_button.height * (button_scale_factor - 1))) if is_button_pressed else go_button
            STORE_COLOR = GREEN if ui_stage != 2 else GRAY
            pygame.draw.rect(screen, STORE_COLOR, scaled_button)
            screen.blit(font.render("STORE", True, BLACK), (scaled_button.x + 10, scaled_button.y + 10))

            # Draw ASSEMBLE button with scaling effect
            scaled_button2 = assemble_button.inflate((assemble_button.width * (button_scale_factor - 1)), (assemble_button.height * (button_scale_factor - 1))) if is_button_pressed else assemble_button
            ASSEMBLE_COLOR = ORANGE if ui_stage == 2 else GRAY
            pygame.draw.rect(screen, ASSEMBLE_COLOR, scaled_button2)
            screen.blit(font.render("ASSEMBLE", True, BLACK), (scaled_button2.x + 60, scaled_button2.y + 10))

            # Draw MANUAL button with scaling effect
            scaled_button3 = manual_button.inflate((manual_button.width * (button_scale_factor - 1)), (manual_button.height * (button_scale_factor - 1))) if is_button_pressed else manual_button

            pygame.draw.rect(screen, YELLOW, scaled_button3)
            screen.blit(font.render("DEBUG", True, BLACK), (scaled_button3.x + 10, scaled_button3.y + 10))
            
            # Draw CONTROL button with scaling effect
            scaled_button4 = control_button.inflate((manual_button.width * (button_scale_factor - 1)), (manual_button.height * (button_scale_factor - 1))) if is_button_pressed else control_button

            pygame.draw.rect(screen, ORANGE, scaled_button4)
            screen.blit(font.render("TAKE CONTROL", True, BLACK), (scaled_button4.x + 10, scaled_button4.y + 10))

            match ui_stage:
                case 0: # just started
                    screen.blit(fontSmall.render("Move colored squares to bay and press STORE to store train cars", True, BLACK), (400, 150))
                case 2: # in assemble stage
                    screen.blit(fontSmall.render("Move colored squares to queue and press ASSEMBLE to build train sequence", True, BLACK), (400, 150))
                case 1: # in storage
                    screen.blit(fontSmall.render("Move colored squares to bay and press STORE to store train cars", True, BLACK), (400, 150))
                    
            match error:
                case 0:
                    pass # no error
                case 1: # queue needs to be empty to store
                    screen.blit(fontSmall.render("INVALID: Fully empty queue before storing", True, RED), (400, 175))
            
            # Event handling
            for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                            running = False

                    elif event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 1:
                                    for block in blocks:
                                            if block.rect.collidepoint(event.pos) and not color_names[block.color] in locked: # if the mouse is on top, make sure the block is not locked
                                                    block.dragging = True
                                                    dragging_block = block
                                                    old_block_pos = block.rect.center
                                                    
                                                    if color_names[dragging_block.color] in queue_positions and ui_stage == 2:    # shift queue if in assembling mode, but no other mode
                                                        queue_positions.remove(color_names[dragging_block.color])
                                                    break
                            if go_button.collidepoint(event.pos):
                                button_scale_factor = 0.9
                    elif event.type == pygame.MOUSEBUTTONUP:
                              
                            if event.button == 1:
                                    if dragging_block:
                                            # found a valid spot or no?
                                            valid_spot = False
                                            for zone_name, zone_rect in zones.items():
                                                    if zone_rect.colliderect(dragging_block.rect):
                                                            print("ui_stage",ui_stage)
                                                            if zone_name == "middle":
                                                                for i in range(num_slots):
                                                                        angle = -(math.pi / num_slots) * (i + 0.5)
                                                                        line_x = circle_center[0] + int((circle_radius + line_length) * math.cos(angle))
                                                                        line_y = circle_center[1] + int((circle_radius + line_length) * math.sin(angle))
                                                                        # if slot collided, if not already dragged somewhere else, if a block not already there
                                                                        if dragging_block.rect.collidepoint((line_x, line_y)) and not i+1 in block_positions.values():              # successful drop onto bay
                                                                                if color_names[dragging_block.color] in queue_positions:    # empty either queue or bays of block
                                                                                    queue_positions.remove(color_names[dragging_block.color])
                                                                            
                                                                                if not color_names[dragging_block.color] in old_block_positions or ui_stage != 2:
                                                                                    block_positions[color_names[dragging_block.color]] = i+1
                                                                                    dragging_block.rect.center = (line_x, line_y)
                                                                                else: # put back in old spot if in assemble mode
                                                                                    j = old_block_positions[color_names[dragging_block.color]] - 1
                                                                                    angle = -(math.pi / num_slots) * (j + 0.5)
                                                                                    line_x = circle_center[0] + int((circle_radius + line_length) * math.cos(angle))
                                                                                    line_y = circle_center[1] + int((circle_radius + line_length) * math.sin(angle))
                                                                                    block_positions[color_names[dragging_block.color]] = j + 1
                                                                                    dragging_block.rect.center = (line_x, line_y)
                                                                                dragging_block.dragging = False
                                                                                valid_spot = True
                                                                                break
                                                            elif ui_stage == 2: # in assemble stage
                                                                collision = False
                                                                for j in range(num_slots): # check each slot
                                                                        slot_x = 830 + j * 50 + 10
                                                                        slot_rect = pygame.Rect(slot_x, 480, 40, 40)
                                                                        if slot_rect.colliderect(dragging_block.rect):
                                                                                collision = True
                                                                                dragging_block.dragging = False
                                                                                break
                                                                if collision:
                                                                    if (not color_names[dragging_block.color] in queue_positions): # no duplicates
                                                                        queue_positions.append(color_names[dragging_block.color]) # add to end the queue
                                                                        valid_spot = True
                                                                        
                                                            break
                                            print("store", block_positions)
                                            print("queue", queue_positions)
                                            print("valid spot:", valid_spot)
                                            # if a valid spot was not found, put the block back
                                            if valid_spot == False:
                                                dragging_block.rect.center = old_block_pos;
                                            # update the queue to fill in if the block was in the queue
                                            if valid_spot:
                                                for block in blocks: # update the queue block locations
                                                    if color_names[block.color] in queue_positions:
                                                        if color_names[block.color] in block_positions:  # empty bays of block
                                                            del block_positions[color_names[block.color]]
                                                        slot_x = 1080 - queue_positions.index(color_names[block.color]) * 50 + 10
                                                        slot_rect = pygame.Rect(slot_x, 480, 40, 40)
                                                        block.rect.topleft = slot_rect.topleft
                                            dragging_block = None
                                            
                                    # Check and update block variables only when GO is pressed
                                    if go_button.collidepoint(event.pos) and len(block_positions)>0 and ui_stage != 2:
                                            if len(queue_positions) != 0:
                                                print("len", len(queue_positions))
                                                error = 1;
                                            else:
                                                is_button_pressed = True
                                                color_positions.clear()  # Clear previous positions

                                                # Update block variables based on positions
                                                for color, pos in block_positions.items():
                                                        print(pos, color)
                                                        color_name = color  # Get the name of the color
                                                        index = block_positions[color] # 1 to 6 for left zone
                                                        color_positions[color_name] = index
                                                        
                                                locked.clear()

                                                # Print the color positions based on the blocks
                                                for color_name, position in color_positions.items():
                                                        print(f"{color_name}: {position}")
                                                screen.blit(font.render("STORING...", True, BLACK), (560, 550))
                                                pygame.display.flip()
                                                return ['store', color_positions, color_queue]
                                    else:
                                        is_button_pressed = False
                                    
                                    
                                    if assemble_button.collidepoint(event.pos) and len(queue_positions)>0:
                                            is_assemble_pressed = True
                                        
                                            color_queue.clear()  # Clear previous positions

                                            # Update block variables based on positions
                                            for color in queue_positions:
                                                    color_queue.append(color)  # Get the name of the color
                                            for color, pos in block_positions.items():        
                                                    locked.append(color) # lock all the blocks
                                            # Print the color positions based on the blocks
                                            for color in color_queue:
                                                    print(f"{color}")
                                            screen.blit(font.render("ASSEMBLING...", True, BLACK), (530, 550))
                                            pygame.display.flip()
                                            return ['assemble', color_positions, color_queue]
                                    else:
                                            is_assemble_pressed = False
                                            
                                    if manual_button.collidepoint(event.pos):
                                            screen.blit(font.render("MANUAL... (press e to end)", True, BLACK), (470, 550))
                                            screen.blit(fontSmall.render("KEYS: 1 is straight | 2-7 is bays 1-6 | 8 is flipped ", True, BLACK), (10, 150))
                                            screen.blit(fontSmall.render("S is store | W is increase delay | X is decrease delay", True, BLACK), (10, 200))
                                            screen.blit(fontSmall.render("A is track switch | Z is track switch", True, BLACK), (10, 250))
                                            screen.blit(fontSmall.render("/\ is forward | \/ is backward | Space is stop", True, BLACK), (10, 300))
                                            pygame.display.flip()
                                            return ['manual', None, None]

                                    if control_button.collidepoint(event.pos):
                                            screen.blit(font.render("MANUAL CONTROL...", True, BLACK), (470, 550))
                                            screen.blit(font.render("To being STORE or ASSEMBLE, ram train into queue backstop", True, BLACK), (200, 120))
                                            screen.blit(fontSmall.render("A is switch to queue | Z is switch to circle", True, BLACK), (10, 250))
                                            screen.blit(fontSmall.render("B for Bell | L for Lights | H for Horn | M for Mute", True, BLACK), (10, 275))
                                            screen.blit(fontSmall.render("/\ is forward | \/ is backward | Space is stop", True, BLACK), (10, 300))
                                            pygame.display.flip()
                                            return ['control', None, None]
                                        
                    elif event.type == pygame.MOUSEMOTION: # drag the block
                            if dragging_block:
                                    dragging_block.update(event.pos)

            pygame.display.flip()
            pygame.time.Clock().tick(60)
            if startup == 0:
                startup = 1
                screen.blit(font.render("MANUAL CONTROL...", True, BLACK), (470, 550))
                screen.blit(fontSmall.render("A is switch to queue | Z is switch to circle", True, BLACK), (10, 250))
                screen.blit(fontSmall.render("B for Bell | L for Lights | H for Horn | M for Mute", True, BLACK), (10, 275))
                screen.blit(fontSmall.render("/\ is forward | \/ is backward | Space is stop", True, BLACK), (10, 300))
                pygame.display.flip()
                return ['control', None, None]
    return ['term', None, None]

if __name__ == '__main__':
    screen = init()
    block_positions = {}
    queue = []
    run = True
    while(run):
        op, op_store, op_queue = ui_loop(screen, block_positions, queue)
        if op == "term":
            run = False
            continue;
        
