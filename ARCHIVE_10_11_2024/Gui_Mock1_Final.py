#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pygame
import sys
import time
import pkt_send.lib as pkt

# Initialize pygame and command station
if pkt.initialize() == -1:
    sys.exit(-1)

pygame.init()

# Set up display
screen_width, screen_height = 1600, 500
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("PyGame DCC GUI")

# Define colors
colors = {
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'yellow': (255, 255, 0),
    'purple': (128, 0, 128),
    'cyan': (0, 255, 255),
    'gray': (169, 169, 169),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'orange': (255, 165, 0),
    'gray2': (50, 50, 50)
}
def toggle(i):
    toggles[i] = not toggles[i]
    return toggles[i]

toggles = [
    0,
    0,
    0,
    0,
    0,
    0,
]

# Define button attributes
button_width, button_height = 160, 100
gap = 100

# First set of buttons (locking)
locking_buttons = [
    {'rect': pygame.Rect(50 + i * (button_width + gap), 150, button_width, button_height), 
     'color': color, 
     'label': label, 
     'locked': False, 
     'original_color': color} for i, (label, color) in enumerate([
        ('White Oil Tanker', colors['white']),
        ('Orange Cargo Car', colors['orange']),
        ('Green Coal Car', colors['green']),
        ('Red Coal Car', colors['red']),
        ('Black Coal Car', colors['gray2']),
        ('Boppoty', colors['cyan'])
    ])
]

# Second set of buttons (non-locking) with blue color
non_locking_buttons = [
    {'rect': pygame.Rect(50 + i * (button_width + gap), 300, button_width, button_height), 
     'color': colors['blue'], 
     'label': label} for i, label in enumerate(['Lights', 'Dimmer', 'Bell', 'Long Horn', 'Short Horn', 'Mute'])
]

# Switch for Manual/Automatic mode
switch_rect = pygame.Rect(50, 20, 200, 50)
manual_mode = False  # Default to Automatic mode

font = pygame.font.Font(None, 36)
all_locked = False
lock_start_time = None

# Animation function for button press
def animate_button_press(button):
    if manual_mode and button in locking_buttons:
        return

    original_rect = button['rect']
    for size_change in range(10, 0, -1):  # Adjust size_change for larger buttons
        screen.fill(colors['white'])  # Clear the screen
        draw_switch()

        # Draw locking buttons
        for btn in locking_buttons:
            color = colors['gray'] if btn['locked'] else btn['color']
            if btn['label'] == 'White Oil Tanker':
                border_rect = btn['rect'].inflate(6, 6)
                pygame.draw.rect(screen, colors['black'], border_rect)
            pygame.draw.rect(screen, color, btn['rect'])
            label = font.render(btn['label'], True, colors['black'])
            screen.blit(label, (btn['rect'].centerx - label.get_width() // 2, btn['rect'].centery - label.get_height() // 2))

        # Draw non-locking buttons
        for btn in non_locking_buttons:
            pygame.draw.rect(screen, btn['color'], btn['rect'])
            label = font.render(btn['label'], True, colors['black'])
            screen.blit(label, (btn['rect'].centerx - label.get_width() // 2, btn['rect'].centery - label.get_height() // 2))

        pressed_rect = pygame.Rect(original_rect.x - size_change, original_rect.y - size_change,
                                   original_rect.width + 2 * size_change, original_rect.height + 2 * size_change)
        pygame.draw.rect(screen, button['color'], pressed_rect)
        pygame.display.flip()
        pygame.time.delay(50)

# Function to draw the Manual/Automatic switch
def draw_switch():
    switch_label = "Manual" if manual_mode else "Automatic"
    switch_color = colors['green'] if manual_mode else colors['blue']
    pygame.draw.rect(screen, switch_color, switch_rect)
    label = font.render(switch_label, True, colors['black'])
    screen.blit(label, (switch_rect.centerx - label.get_width() // 2, switch_rect.centery - label.get_height() // 2))

# Function to lock all top buttons
def lock_all_buttons():
    for button in locking_buttons:
        button['locked'] = True
        button['color'] = colors['gray']

# Function to unlock all top buttons
def unlock_all_buttons():
    for button in locking_buttons:
        button['locked'] = False
        button['color'] = button['original_color']

# Main loop
running = True
while running:
    screen.fill(colors['white'])
    draw_switch()

    keys = pygame.key.get_pressed()

    # Check manual mode for keypress actions
    if manual_mode:
        if keys[pygame.K_UP]:
            pkt.forward(5)
        elif keys[pygame.K_DOWN]:
            pkt.backward(5)
        else:
            pkt.stop(5)
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and switch_rect.collidepoint(event.pos):
            manual_mode = not manual_mode
            if manual_mode:
                lock_all_buttons()
                pkt.stop(5)
            else:
                unlock_all_buttons()
                pkt.stop(5)

        # Handle locking buttons (top)
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in locking_buttons:
                if button['rect'].collidepoint(event.pos):
                    if not manual_mode and not all_locked:
                        for btn in locking_buttons:
                            btn['locked'] = True
                        animate_button_press(button)
                        all_locked = True
                        lock_start_time = time.time()

            # Handle non-locking buttons (bottom)
            for i, button in enumerate(non_locking_buttons):
                if button['rect'].collidepoint(event.pos):
                    if i == 0:  # Lights
                        pkt.function(5, 4, toggle(i))
                    elif i == 1:  # Dimmer
                        pkt.function(5, 7, toggle(i))
                    elif i == 2:  # Bell
                        pkt.function(5, 0, toggle(i))
                    elif i == 3:  # Long Horn
                        pkt.function(5, 1, toggle(i))
                    elif i == 4:  # Short Horn
                        pkt.function(5, 2, toggle(i))
                    elif i == 5:  # Mute
                        pkt.function(5, 8, toggle(i))
                    else:
                        pkt.stop(5)
                    animate_button_press(button)

    # Check 3-second lock timer
    if all_locked and not manual_mode and time.time() - lock_start_time >= 3:
        all_locked = False
        unlock_all_buttons()

    # Draw locking buttons
    for button in locking_buttons:
        color = colors['gray'] if button['locked'] else button['color']
        if button['label'] == 'White Oil Tanker':
            border_rect = button['rect'].inflate(6, 6)
            pygame.draw.rect(screen, colors['black'], border_rect)
        pygame.draw.rect(screen, color, button['rect'])
        label = font.render(button['label'], True, colors['black'])
        screen.blit(label, (button['rect'].centerx - label.get_width() // 2, button['rect'].centery - label.get_height() // 2))

    # Draw non-locking buttons
    for button in non_locking_buttons:
        pygame.draw.rect(screen, button['color'], button['rect'])
        label = font.render(button['label'], True, colors['black'])
        screen.blit(label, (button['rect'].centerx - label.get_width() // 2, button['rect'].centery - label.get_height() // 2))

    pygame.display.flip()

# Quit pygame and terminate pkt
pygame.quit()
pkt.terminate()


# In[ ]:




