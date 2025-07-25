import pygame
import random
import math
from pygame import mixer
import os

# Initialize the pygame
pygame.init()

# Create the screen
screen_width = 1080
screen_height = 2255
screen = pygame.display.set_mode((screen_width, screen_height))

# Background
background = pygame.image.load("bg5.png")
background_height = background.get_height()
background_y1 = 0
background_y2 = -background_height

# Background sound
mixer.music.load("theme.mp3")
mixer.music.play(-1)
music_enabled = True # New: state for music toggle

# Caption and icon
pygame.display.set_caption("Space Invaders Angry Birds Edition")
icon = pygame.image.load("ufo.png")
pygame.display.set_icon(icon)

# Player
playerImg = pygame.image.load("Pl3.png")
playerImg = pygame.transform.scale(playerImg, (200, 300))
playerX = (screen_width - playerImg.get_width()) / 2  # Center player initially
playerY = screen_height - playerImg.get_height() - 10 # Initial player position 20px above bottom
player_dragging = False
is_firing_continuously = True # Start with continuous firing enabled
fire_delay = 250 # Milliseconds between shots for continuous firing
last_shot_time = 0
original_fire_delay = 250
boosted_fire_delay_gift1 = 100 # Faster firing when boosted by first gift
boosted_fire_delay_gift2 = 50 # Even faster firing when boosted by second gift

firepower_boost_active = False
firepower_boost_end_time = 0
current_bullet_img = pygame.image.load("b1.png") # Default bullet
current_bullet_img = pygame.transform.scale(current_bullet_img, (50, 150))
bullet_destroys_eggs = False # For second powerup

# Player HP and MP
player_hp = 50
player_max_hp = 50
player_mp = 0
player_max_mp = 100 # Example max MP
damage_blink_duration = 500 # milliseconds for blinking
last_hit_time = 0
player_visible = True

# SFX Control
sfx_enabled = True # New: state for sfx toggle

# Load sounds
laser_sound = mixer.Sound("laser.wav")
collision_sound = mixer.Sound("collision.mp3")
levelup_sound = mixer.Sound("levelup.mp3")
boss_hit_sound = mixer.Sound("boss_hit.mp3")
explosion_sound = mixer.Sound("explosion.wav")
gift_collect_sound = mixer.Sound("col.mp3")

# Helper function to play sound if SFX is enabled
def play_sfx(sound):
    if sfx_enabled:
        sound.play()

# Enemy
enemyImg = []
enemyX = []
enemyY = []
enemyX_change = [] # Still used for horizontal oscillation
enemyY_speed = [] # Renamed for clarity: vertical speed
enemy_dead_state_active = [False] * 6 # To track if enemy is in dead state
enemy_dead_state_start_time = [0] * 6 # To track when dead state started
enemy_exiting_level = [False] * 6 # NEW: To track if enemy is exiting horizontally
angry_dead_img = pygame.image.load("angry_dead.png") # Load the dead enemy image
angry_dead_img = pygame.transform.scale(angry_dead_img, (150, 150))

num_of_enemies = 6
initial_enemy_y_speed_base = 2
initial_enemy_x_change_base = 5

def initialize_enemies():
    global enemyImg, enemyX, enemyY, enemyX_change, enemyY_speed, enemy_dead_state_active, enemy_dead_state_start_time, enemy_exiting_level
    enemyImg = []
    enemyX = []
    enemyY = []
    enemyX_change = []
    enemyY_speed = []
    enemy_dead_state_active = [False] * num_of_enemies
    enemy_dead_state_start_time = [0] * num_of_enemies
    enemy_exiting_level = [False] * num_of_enemies # Initialize this flag

    for i in range(num_of_enemies):
        enemyImg.append(pygame.image.load("angryy.png"))
        enemyImg[i] = pygame.transform.scale(enemyImg[i], (150, 150))
        enemyX.append(random.randint(0, screen_width - enemyImg[i].get_width()))
        enemyY.append(random.randint(-500, -50)) # Start randomly above the screen
        
        enemyX_change.append(initial_enemy_x_change_base)
        enemyY_speed.append(random.uniform(initial_enemy_y_speed_base, initial_enemy_y_speed_base + 2))

initialize_enemies() # Initialize enemies at the start

def enemy(x, y, i):
    screen.blit(enemyImg[i], (x, y))

# Boss
class Boss:
    def __init__(self):
        self.image = pygame.image.load("angryy.png")
        # Make it 3 times bigger than normal enemy
        self.image = pygame.transform.scale(self.image, (150 * 3, 150 * 3)) 
        self.rect = self.image.get_rect()
        self.x = (screen_width - self.rect.width) / 2
        self.y = -self.rect.height # Start off-screen at the top
        self.x_change = 7 # Slightly faster horizontal movement for boss
        self.y_speed = 1 # Slower vertical descent to allow player to shoot
        self.hp = 20 # Boss HP
        self.hits_taken = 0
        self.dead = False
        self.entry_speed = 5 # Speed at which boss enters the screen
        self.target_y = 100 # Target Y position for the boss
        self.entered_screen = False

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        if not self.entered_screen:
            self.y += self.entry_speed
            if self.y >= self.target_y:
                self.y = self.target_y
                self.entered_screen = True
        else:
            self.x += self.x_change
            if self.x <= 0 or self.x >= screen_width - self.rect.width:
                self.x_change *= -1
            # Boss can also move up and down slightly (optional)
            # self.y += self.y_speed 
            # if self.y <= 0 or self.y >= screen_height / 3: # Keep boss in upper third
            #     self.y_speed *= -1

        self.rect.topleft = (self.x, self.y)

    def take_hit(self):
        self.hits_taken += 1
        if self.hits_taken >= self.hp:
            self.dead = True

boss = None # Initialize boss as None

# Eggs
eggImg = pygame.image.load("egg.png")
eggImg = pygame.transform.scale(eggImg, (80, 100))
eggs = [] # Stores (eggX, eggY, egg_rect)
egg_speed = 5
base_egg_drop_chance = 0.002 # Significantly reduced probability of an enemy dropping an egg per frame
egg_drop_chance = base_egg_drop_chance # Current egg drop chance

class Egg:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = eggImg.get_rect(topleft=(self.x, self.y))

    def draw(self):
        screen.blit(eggImg, (self.x, self.y))

    def move(self):
        self.y += egg_speed
        self.rect.topleft = (self.x, self.y)

# Gifts
gift1Img = pygame.image.load("gift.png")
gift1Img = pygame.transform.scale(gift1Img, (120, 120))
gift2Img = pygame.image.load("gift2.png") # Second gift image
gift2Img = pygame.transform.scale(gift2Img, (120, 120))

gifts = [] # Stores (giftX, giftY, gift_rect, type)
gift_speed = 4
enemies_killed_since_last_gift = 0
kills_for_gift1 = 10 # Number of kills required to drop first gift
kills_for_gift2 = 20 # Number of kills required to drop second gift

class Gift:
    def __init__(self, x, y, gift_type):
        self.x = x
        self.y = y
        self.type = gift_type # "gift1" or "gift2"
        if self.type == "gift1":
            self.image = gift1Img
        else:
            self.image = gift2Img
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        self.y += gift_speed
        self.rect.topleft = (self.x, self.y)

# Bullet
bulletImg_b1 = pygame.image.load("b1.png")
bulletImg_b1 = pygame.transform.scale(bulletImg_b1, (50, 150))
bulletImg_b2 = pygame.image.load("b2.png") # Second bullet image
bulletImg_b2 = pygame.transform.scale(bulletImg_b2, (50, 150))

bullets = [] # Stores (bulletX, bulletY, bullet_state, bullet_rect)
bulletY_change = 70

# Score
score_value = 0
# Adjusted font for general text, slightly larger for better readability
game_font = pygame.font.Font("freesansbold.ttf", 48)  # Increased font size
score_font = pygame.font.Font("freesansbold.ttf", 48)
level_font = pygame.font.Font("freesansbold.ttf", 72) # Bigger font for level

score_textX = 10
score_textY = 10

# High Score
highscore_file = "highscore.txt"
high_score = 0
try:
    with open(highscore_file, "r") as f:
        high_score = int(f.read())
except (FileNotFoundError, ValueError):
    high_score = 0

def save_highscore(score):
    global high_score
    if score > high_score:
        high_score = score
        with open(highscore_file, "w") as f:
            f.write(str(score))

# Game over text
over_font = pygame.font.Font("freesansbold.ttf", 120) # Increased font size
game_name_font = pygame.font.Font("freesansbold.ttf", 72) # Increased font size

# Levels
current_level = 1
score_for_next_level = 200
level_display_timer = 0
level_display_duration = 3000 # milliseconds

def show_score(x, y):
    score = score_font.render("Score : " + str(score_value), True, (255, 255, 0)) # Yellow color
    screen.blit(score, (x, y))

def show_highscore(x, y):
    hs_text = score_font.render("High Score : " + str(high_score), True, (0, 255, 255)) # Cyan color
    screen.blit(hs_text, (x, y + 60))

def show_level(x, y):
    global level_display_timer
    if pygame.time.get_ticks() < level_display_timer + level_display_duration:
        level_text = level_font.render(f"Level {current_level}", True, (255, 255, 255)) # White color
        text_rect = level_text.get_rect(center=(screen_width / 2, screen_height / 2))
        screen.blit(level_text, text_rect)

def show_status(x, y_offset):
    # Bar dimensions and colors
    bar_width = 250
    bar_height = 30
    bar_padding = 10 # Padding between the label and the bar
    vertical_spacing = 20 # Spacing between HP and MP bars
    bar_background_color = (80, 80, 80) # Dark grey for empty part
    
    # HP Bar
    hp_label = game_font.render("HP:", True, (255, 255, 255))
    screen.blit(hp_label, (x, y_offset + 120))
    
    hp_bar_x = x + hp_label.get_width() + bar_padding
    hp_bar_y = y_offset + 120 + (hp_label.get_height() - bar_height) / 2 # Vertically center with label

    # Draw HP background bar
    pygame.draw.rect(screen, bar_background_color, (hp_bar_x, hp_bar_y, bar_width, bar_height), border_radius=5)
    
    # Calculate HP bar fill
    hp_fill_width = (player_hp / player_max_hp) * bar_width
    
    # Determine HP bar color (green when full, red when low)
    hp_color = (255, 0, 0) # Default to red
    if player_hp > player_max_hp / 2: # More than half HP
        hp_color = (0, 255, 0) # Green
    elif player_hp > player_max_hp / 4: # More than quarter HP
        hp_color = (255, 165, 0) # Orange
    
    pygame.draw.rect(screen, hp_color, (hp_bar_x, hp_bar_y, hp_fill_width, bar_height), border_radius=5)

    # HP Text (e.g., "50/50") on top of the bar
    hp_value_text = game_font.render(f"{player_hp}/{player_max_hp}", True, (255, 255, 255))
    screen.blit(hp_value_text, (hp_bar_x + (bar_width - hp_value_text.get_width()) / 2, 
                                 hp_bar_y + (bar_height - hp_value_text.get_height()) / 2))

    # MP Bar
    mp_label = game_font.render("MP:", True, (255, 255, 255))
    screen.blit(mp_label, (x, y_offset + 120 + bar_height + vertical_spacing))

    mp_bar_x = x + mp_label.get_width() + bar_padding
    mp_bar_y = y_offset + 120 + bar_height + vertical_spacing + (mp_label.get_height() - bar_height) / 2 # Vertically center with label

    # Draw MP background bar
    pygame.draw.rect(screen, bar_background_color, (mp_bar_x, mp_bar_y, bar_width, bar_height), border_radius=5)

    # Calculate MP bar fill
    mp_fill_width = (player_mp / player_max_mp) * bar_width
    mp_color = (50, 150, 255) # Blue for MP

    pygame.draw.rect(screen, mp_color, (mp_bar_x, mp_bar_y, mp_fill_width, bar_height), border_radius=5)

    # MP Text (e.g., "100/100") on top of the bar
    mp_value_text = game_font.render(f"{player_mp}/{player_max_mp}", True, (255, 255, 255))
    screen.blit(mp_value_text, (mp_bar_x + (bar_width - mp_value_text.get_width()) / 2, 
                                 mp_bar_y + (bar_height - mp_value_text.get_height()) / 2))


def game_over_screen():
    screen.fill((0, 0, 0)) # Black background for game over

    # Game Title
    game_name_text = game_name_font.render("GAME OVER", True, (255, 255, 255))
    screen.blit(game_name_text, (screen_width / 2 - game_name_text.get_width() / 2, screen_height / 4))

    # Score Displays
    final_score_text = game_font.render("Final Score: " + str(score_value), True, (255, 255, 255))
    screen.blit(final_score_text, (screen_width / 2 - final_score_text.get_width() / 2, screen_height / 2.5))

    hs_display_text = game_font.render("High Score: " + str(high_score), True, (255, 255, 255))
    screen.blit(hs_display_text, (screen_width / 2 - hs_display_text.get_width() / 2, screen_height / 2.2))

    # Buttons
    button_width = 400 # Made wider
    button_height = 90 # Made taller
    button_x = screen_width / 2 - button_width / 2
    button_spacing = 40 # Increased space between buttons

    restart_button = pygame.Rect(button_x, screen_height / 1.7, button_width, button_height)
    exit_button = pygame.Rect(button_x, restart_button.y + button_height + button_spacing, button_width, button_height)

    # Draw buttons with rounded corners and subtle shadows/borders
    pygame.draw.rect(screen, (0, 180, 0), restart_button, border_radius=20) # Green, darker
    pygame.draw.rect(screen, (180, 0, 0), exit_button, border_radius=20) # Red, darker

    # Add a subtle border/shadow effect to buttons
    pygame.draw.rect(screen, (50, 255, 50), restart_button, border_radius=20, width=4) # Brighter green border
    pygame.draw.rect(screen, (255, 50, 50), exit_button, border_radius=20, width=4) # Brighter red border

    restart_text = game_font.render("Restart", True, (255, 255, 255))
    exit_text = game_font.render("Exit", True, (255, 255, 255))

    screen.blit(restart_text, (restart_button.x + (restart_button.width - restart_text.get_width()) / 2,
                                  restart_button.y + (restart_button.height - restart_text.get_height()) / 2))
    screen.blit(exit_text, (exit_button.x + (exit_button.width - exit_text.get_width()) / 2,
                            exit_button.y + (exit_button.height - exit_text.get_height()) / 2))

    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.collidepoint(event.pos):
                    return "restart"
                if exit_button.collidepoint(event.pos):
                    return "quit"

def game_completed_screen():
    screen.fill((0, 0, 0))

    game_completed_message = over_font.render("GAME COMPLETED!", True, (0, 255, 0)) # Green text
    screen.blit(game_completed_message, (screen_width / 2 - game_completed_message.get_width() / 2, screen_height / 4))

    final_score_text = game_font.render("Final Score: " + str(score_value), True, (255, 255, 255))
    screen.blit(final_score_text, (screen_width / 2 - final_score_text.get_width() / 2, screen_height / 2.5))

    hs_display_text = game_font.render("High Score: " + str(high_score), True, (255, 255, 255))
    screen.blit(hs_display_text, (screen_width / 2 - hs_display_text.get_width() / 2, screen_height / 2.2))

    button_width = 400 # Made wider
    button_height = 90 # Made taller
    button_x = screen_width / 2 - button_width / 2
    button_spacing = 40 # Increased space

    restart_button = pygame.Rect(button_x, screen_height / 1.7, button_width, button_height)
    exit_button = pygame.Rect(button_x, restart_button.y + button_height + button_spacing, button_width, button_height)

    pygame.draw.rect(screen, (0, 180, 0), restart_button, border_radius=20)
    pygame.draw.rect(screen, (180, 0, 0), exit_button, border_radius=20)

    pygame.draw.rect(screen, (50, 255, 50), restart_button, border_radius=20, width=4)
    pygame.draw.rect(screen, (255, 50, 50), exit_button, border_radius=20, width=4)

    restart_text = game_font.render("Restart", True, (255, 255, 255))
    exit_text = game_font.render("Exit", True, (255, 255, 255))

    screen.blit(restart_text, (restart_button.x + (restart_button.width - restart_text.get_width()) / 2,
                                  restart_button.y + (restart_button.height - restart_text.get_height()) / 2))
    screen.blit(exit_text, (exit_button.x + (exit_button.width - exit_text.get_width()) / 2,
                            exit_button.y + (exit_button.height - exit_text.get_height()) / 2))
    
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.collidepoint(event.pos):
                    return "restart"
                if exit_button.collidepoint(event.pos):
                    return "quit"

def player_draw(x, y):
    global player_visible
    current_time = pygame.time.get_ticks()

    if current_time - last_hit_time < damage_blink_duration:
        # Blink effect: toggle visibility
        if (current_time // 100) % 2 == 0: # Change visibility every 100ms
            player_visible = True
        else:
            player_visible = False
    else:
        player_visible = True # Player is always visible if not recently hit

    if player_visible:
        screen.blit(playerImg, (x, y))

def fire_bullet(x, y):
    global last_shot_time, fire_delay, current_bullet_img
    current_time = pygame.time.get_ticks()
    if current_time - last_shot_time > fire_delay:
        play_sfx(laser_sound) # Use helper for SFX
        
        # Check for an available "ready" bullet first
        for i in range(len(bullets)):
            if bullets[i][2] == "ready":
                bullets[i][0] = x + playerImg.get_width() / 2 - current_bullet_img.get_width() / 2
                bullets[i][1] = y # Bullet fires from the top of the player
                bullets[i][2] = "fire"
                bullets[i][3].topleft = (bullets[i][0], bullets[i][1])
                last_shot_time = current_time
                return

        # If no "ready" bullet, create a new one
        new_bullet_x = x + playerImg.get_width() / 2 - current_bullet_img.get_width() / 2
        new_bullet_y = y # Bullet fires from the top of the player
        new_bullet_rect = current_bullet_img.get_rect(topleft=(new_bullet_x, new_bullet_y))
        bullets.append([new_bullet_x, new_bullet_y, "fire", new_bullet_rect])
        last_shot_time = current_time

def is_collision(rect1, rect2):
    return rect1.colliderect(rect2)

# Game states
GAME_STATE_INTRO = 0
GAME_STATE_PLAYING = 1
GAME_STATE_PAUSED = 2
GAME_STATE_GAMEOVER = 3
GAME_STATE_COMPLETED = 4 # New game state
current_game_state = GAME_STATE_INTRO

# Intro Screen
intro_image = pygame.image.load("intro_screen.png")
intro_image = pygame.transform.scale(intro_image, (screen_width, screen_height))

# Pause button (modern icon: two vertical rectangles)
pause_button_rect = pygame.Rect(screen_width - 90, 10, 80, 50) # Larger rect for easier clicking
pause_icon_width = 12
pause_icon_height = 35
pause_icon_padding = 8

# Clock for frame rate control
clock = pygame.time.Clock()
FPS = 60

# Game loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if current_game_state == GAME_STATE_INTRO:
            if event.type == pygame.MOUSEBUTTONDOWN:
                current_game_state = GAME_STATE_PLAYING
                level_display_timer = pygame.time.get_ticks() # Start level 1 display
            
        elif current_game_state == GAME_STATE_PLAYING:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                
                # Check for pause button click
                if pause_button_rect.collidepoint(mouse_x, mouse_y):
                    current_game_state = GAME_STATE_PAUSED
                    is_firing_continuously = False # Stop firing when paused
                # Check if the click is on the player to start dragging
                elif playerImg.get_rect(topleft=(playerX, playerY)).collidepoint(mouse_x, mouse_y):
                    player_dragging = True
                
            if event.type == pygame.MOUSEBUTTONUP:
                player_dragging = False

            if event.type == pygame.MOUSEMOTION:
                if player_dragging:
                    mouse_x, mouse_y = event.pos
                    playerX = mouse_x - playerImg.get_width() / 2
                    playerY = mouse_y - playerImg.get_height() / 2 # Allow vertical dragging
        
        elif current_game_state == GAME_STATE_PAUSED:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                
                # Button definitions for pause screen - RE-DEFINED HERE TO ENSURE CORRECT MAPPING
                button_width_pause = 350
                button_height_pause = 80
                button_x_pause = screen_width / 2 - button_width_pause / 2
                button_spacing_pause = 30

                # Define the Rects for the buttons directly before collision checking
                resume_button_pause = pygame.Rect(button_x_pause, screen_height / 2 - 70, button_width_pause, button_height_pause)
                music_button_pause = pygame.Rect(button_x_pause, resume_button_pause.y + button_height_pause + button_spacing_pause, button_width_pause, button_height_pause)
                sfx_button_pause = pygame.Rect(button_x_pause, music_button_pause.y + button_height_pause + button_spacing_pause, button_width_pause, button_height_pause)
                quit_button_pause = pygame.Rect(button_x_pause, sfx_button_pause.y + button_height_pause + button_spacing_pause, button_width_pause, button_height_pause)


                if resume_button_pause.collidepoint(mouse_x, mouse_y):
                    current_game_state = GAME_STATE_PLAYING
                    is_firing_continuously = True # Resume continuous firing
                elif music_button_pause.collidepoint(mouse_x, mouse_y):
                    music_enabled = not music_enabled
                    if music_enabled:
                        mixer.music.unpause()
                    else:
                        mixer.music.pause()
                elif sfx_button_pause.collidepoint(mouse_x, mouse_y):
                    sfx_enabled = not sfx_enabled
                elif quit_button_pause.collidepoint(mouse_x, mouse_y):
                    running = False
            
    # Game State Logic
    if current_game_state == GAME_STATE_INTRO:
        screen.blit(intro_image, (0, 0))

    elif current_game_state == GAME_STATE_PLAYING:
        # Infinite background scrolling
        scroll_speed = 20
        background_y1 += scroll_speed
        background_y2 += scroll_speed

        if background_y1 > screen_height:
            background_y1 = -background_height
        if background_y2 > screen_height:
            background_y2 = -background_height

        screen.blit(background, (0, background_y1))
        screen.blit(background, (0, background_y2))

        # Check for level progression
        if current_level < 5 and score_value >= score_for_next_level * current_level:
            current_level += 1
            level_display_timer = pygame.time.get_ticks() # Start level change display
            play_sfx(levelup_sound) # Play a level up sound
            
            if current_level < 5: # Increase difficulty for regular levels
                # Increase enemy speed and egg drop chance
                for i in range(num_of_enemies):
                    enemyY_speed[i] += 0.5 # Increase vertical speed
                    enemyX_change[i] = abs(enemyX_change[i]) + 1 # Increase horizontal speed (ensure positive)
                    if enemyX[i] >= screen_width - enemyImg[i].get_width(): # Adjust if already at edge
                        enemyX_change[i] *= -1
                egg_drop_chance *= 1.2 # Increase egg drop chance by 20%
                
            elif current_level == 5:
                # Clear all regular enemies
                # Modified: Instead of setting Y to -1000, make them exit horizontally
                for i in range(num_of_enemies):
                    if not enemy_dead_state_active[i]: # Only make live enemies exit
                        enemy_exiting_level[i] = True
                        # Decide direction based on current position
                        if enemyX[i] < screen_width / 2: # Closer to left, move left
                            enemyX_change[i] = -30 # Faster speed for exiting
                        else: # Closer to right, move right
                            enemyX_change[i] = 30 # Faster speed for exiting
                        enemyY_speed[i] = 0 # Stop vertical movement during exit
                eggs = [] # Clear any existing eggs
                gifts = [] # Clear any existing gifts

                # Introduce the boss
                boss = Boss()

        # Handle firepower boost duration
        current_time = pygame.time.get_ticks()
        if firepower_boost_active and current_time > firepower_boost_end_time:
            firepower_boost_active = False
            fire_delay = original_fire_delay # Reset fire delay
            current_bullet_img = bulletImg_b1 # Revert bullet image
            bullet_destroys_eggs = False # Revert egg destruction ability
            player_mp = 50 # MP goes back to 50 when powerup runs out


        # Continuous firing
        if is_firing_continuously:
            fire_bullet(playerX, playerY)

        # Player Movement clamping
        playerX = max(0, min(playerX, screen_width - playerImg.get_width()))
        playerY = max(screen_height / 3, min(playerY, screen_height - playerImg.get_height()))
        
        player_rect = playerImg.get_rect(topleft=(playerX, playerY))

        # Handle enemies or boss based on level
        if current_level < 5: # Regular enemy levels
            for i in range(num_of_enemies):
                enemy_rect = enemyImg[i].get_rect(topleft=(enemyX[i], enemyY[i]))

                # Handle enemy exiting level
                if enemy_exiting_level[i]:
                    enemyX[i] += enemyX_change[i]
                    # Once off-screen, "disable" them
                    if enemyX[i] < -enemyImg[i].get_width() or enemyX[i] > screen_width:
                        enemyY[i] = -1000 # Move far off-screen vertically
                        enemy_exiting_level[i] = False # Reset flag
                    # Skip other updates (collision, egg drop) for exiting enemies
                    continue # IMPORTANT: Skip remaining logic for exiting enemies

                # Handle enemy dead state
                if enemy_dead_state_active[i]:
                    if current_time - enemy_dead_state_start_time[i] < 1000: # 1 second duration
                        screen.blit(angry_dead_img, (enemyX[i], enemyY[i]))
                    else:
                        enemy_dead_state_active[i] = False
                        # After 1 second, reset enemy normally - this needs to be conditional on not exiting
                        if not enemy_exiting_level[i]: # Only reset if not in exit state
                            enemyY[i] = random.randint(-500, -50)
                            enemyX[i] = random.randint(0, screen_width - enemyImg[i].get_width())
                            enemyY_speed[i] = random.uniform(initial_enemy_y_speed_base + (current_level - 1) * 0.5, 
                                                             initial_enemy_y_speed_base + (current_level - 1) * 0.5 + 2)
                else: # Regular enemy movement
                    enemyY[i] += enemyY_speed[i]
                    enemyX[i] += enemyX_change[i]

                    if enemyX[i] <= 0 or enemyX[i] >= screen_width - enemyImg[i].get_width():
                        enemyX_change[i] *= -1

                    if enemyY[i] > screen_height:
                        enemyY[i] = random.randint(-500, -50)
                        enemyX[i] = random.randint(0, screen_width - enemyImg[i].get_width())
                        enemyY_speed[i] = random.uniform(initial_enemy_y_speed_base + (current_level - 1) * 0.5, 
                                                         initial_enemy_y_speed_base + (current_level - 1) * 0.5 + 2)

                    # Randomly drop eggs from enemies (less frequent)
                    if random.random() < egg_drop_chance:
                        eggs.append(Egg(enemyX[i] + enemyImg[i].get_width() / 2 - eggImg.get_width() / 2,
                                         enemyY[i] + enemyImg[i].get_height())) # Egg comes from beneath the enemy

                    # Player-Enemy Collision Check
                    if is_collision(player_rect, enemy_rect):
                        if current_time - last_hit_time > damage_blink_duration: # Prevent rapid hits
                            player_hp -= 30
                            last_hit_time = current_time
                            play_sfx(collision_sound)
                            if player_hp <= 0:
                                save_highscore(score_value)
                                current_game_state = GAME_STATE_GAMEOVER
                                break
                    
                    # Bullet movement and collision with enemies
                    for bullet_data in bullets:
                        bullet_x, bullet_y, bullet_state, bullet_rect = bullet_data
                        
                        if bullet_state == "fire":
                            bullet_rect.topleft = (bullet_x, bullet_y)

                            collision = is_collision(enemy_rect, bullet_rect)
                            if collision and not enemy_dead_state_active[i]: # Only hit if not already dead
                                play_sfx(collision_sound)
                                
                                bullet_data[2] = "ready"
                                bullet_data[1] = screen_height + 50 # Move off-screen
                                
                                score_value += 1
                                enemies_killed_since_last_gift += 1
                                
                                # Activate enemy dead state
                                enemy_dead_state_active[i] = True
                                enemy_dead_state_start_time[i] = current_time
                                
                                # Drop gift logic
                                if enemies_killed_since_last_gift == kills_for_gift1:
                                    gifts.append(Gift(enemyX[i] + enemyImg[i].get_width() / 2 - gift1Img.get_width() / 2,
                                                      enemyY[i], "gift1"))
                                elif enemies_killed_since_last_gift == kills_for_gift2:
                                    gifts.append(Gift(enemyX[i] + enemyImg[i].get_width() / 2 - gift2Img.get_width() / 2,
                                                      enemyY[i], "gift2"))
                                    enemies_killed_since_last_gift = 0 # Reset for next cycle of gifts

                                break # Only one bullet can hit an enemy at a time
                    
                    # Draw the enemy only if not in dead state and not exiting
                    if not enemy_dead_state_active[i] and not enemy_exiting_level[i]:
                        enemy(enemyX[i], enemyY[i], i)
        
        elif current_level == 5 and boss: # Boss battle
            boss.move()
            boss.draw()

            # Player-Boss Collision Check (similar to enemy)
            if is_collision(player_rect, boss.rect):
                if current_time - last_hit_time > damage_blink_duration:
                    player_hp -= 50 # Boss hits harder
                    last_hit_time = current_time
                    play_sfx(collision_sound)
                    if player_hp <= 0:
                        save_highscore(score_value)
                        current_game_state = GAME_STATE_GAMEOVER
            
            # Boss dropping eggs (thrice the normal rate)
            if random.random() < egg_drop_chance * 3:
                eggs.append(Egg(boss.x + boss.rect.width / 2 - eggImg.get_width() / 2,
                                boss.y + boss.rect.height))

            # Bullet-Boss Collision
            for bullet_data in bullets:
                bullet_x, bullet_y, bullet_state, bullet_rect = bullet_data
                if bullet_state == "fire":
                    bullet_rect.topleft = (bullet_x, bullet_y)
                    if is_collision(boss.rect, bullet_rect) and not boss.dead:
                        play_sfx(boss_hit_sound) # A sound for hitting boss
                        boss.take_hit()
                        score_value += 5 # More points for hitting boss
                        bullet_data[2] = "ready"
                        bullet_data[1] = screen_height + 50 # Move off-screen

                        if boss.hits_taken == 10:
                            gifts.append(Gift(boss.x + boss.rect.width / 2 - gift1Img.get_width() / 2,
                                              boss.y + boss.rect.height, "gift1"))
                        elif boss.hits_taken == 15:
                            gifts.append(Gift(boss.x + boss.rect.width / 2 - gift2Img.get_width() / 2,
                                              boss.y + boss.rect.height, "gift2"))
                        
                        if boss.dead:
                            play_sfx(explosion_sound) # Explosion sound for boss
                            save_highscore(score_value)
                            current_game_state = GAME_STATE_COMPLETED
                        break # Only one bullet can hit the boss at a time

        if current_game_state == GAME_STATE_GAMEOVER or current_game_state == GAME_STATE_COMPLETED:
            continue

        # Draw and move active bullets
        for bullet_data in bullets:
            bullet_x, bullet_y, bullet_state, bullet_rect = bullet_data
            if bullet_state == "fire":
                screen.blit(current_bullet_img, (bullet_x, bullet_y)) # Use current bullet image
                bullet_data[1] -= bulletY_change
                bullet_data[3].topleft = (bullet_data[0], bullet_data[1])

                if bullet_data[1] <= 0:
                    bullet_data[2] = "ready"
                    bullet_data[1] = screen_height + 50

        # Update and draw eggs - FIX APPLIED HERE
        eggs_to_keep = [] 
        for egg in eggs:
            egg.move()
            egg.draw()
            
            # Check if egg goes off screen
            if egg.y > screen_height:
                continue # Skip to next egg, this one is removed

            # Bullet-Egg Collision Check (if powerup active)
            hit_by_bullet = False
            if bullet_destroys_eggs:
                for bullet_data in bullets:
                    bullet_x, bullet_y, bullet_state, bullet_rect = bullet_data
                    if bullet_state == "fire":
                        if is_collision(egg.rect, bullet_rect):
                            play_sfx(collision_sound)
                            bullet_data[2] = "ready" # Reset bullet state
                            bullet_data[1] = screen_height + 50 # Move off-screen
                            hit_by_bullet = True
                            break # Only one bullet can hit one egg
                if hit_by_bullet:
                    continue # Skip to next egg, this one is removed

            # Player-Egg Collision Check
            player_hit_egg = False
            if is_collision(player_rect, egg.rect):
                if current_time - last_hit_time > damage_blink_duration: # Prevent rapid hits
                    player_hp -= 10
                    last_hit_time = current_time
                    play_sfx(collision_sound) # Use collision sound for egg as well
                    player_hit_egg = True
                    if player_hp <= 0:
                        save_highscore(score_value)
                        current_game_state = GAME_STATE_GAMEOVER
                        break # Exit loop if game over
            
            if player_hit_egg:
                continue # Skip to next egg, this one is removed

            # If the egg survived all checks, add it to the list to keep
            eggs_to_keep.append(egg)

        eggs = eggs_to_keep # Update the main eggs list with the surviving eggs

        # Update and draw gifts
        for gift in list(gifts): # Iterate over a copy to allow removal
            gift.move()
            gift.draw()
            if gift.y > screen_height: # Remove gifts that go off screen
                gifts.remove(gift)

            # Player-Gift Collision Check
            if is_collision(player_rect, gift.rect):
                play_sfx(gift_collect_sound) # Sound for collecting gift
                score_value += 100 # Increase score
                player_hp = player_max_hp # Fully increase HP
                gifts.remove(gift) # Remove collected gift

                # Apply power-up based on gift type
                if gift.type == "gift1":
                    player_mp = min(player_max_mp, player_mp + 50) # Increase MP, capped at max
                    firepower_boost_active = True
                    firepower_boost_end_time = current_time + 5000 # 5 seconds boost
                    fire_delay = boosted_fire_delay_gift1 # Apply boosted fire delay
                    current_bullet_img = bulletImg_b1 # Ensure bullet is b1
                    bullet_destroys_eggs = False

                elif gift.type == "gift2":
                    player_mp = min(player_max_mp, player_mp + 100) # Increase MP by 100
                    firepower_boost_active = True
                    firepower_boost_end_time = current_time + 10000 # 10 seconds boost
                    fire_delay = boosted_fire_delay_gift2 # Apply even faster fire delay
                    current_bullet_img = bulletImg_b2 # Change bullet image to b2.png
                    bullet_destroys_eggs = True # Enable egg destruction

                break # Exit loop if game over (only one gift can be collected at a time)

        player_draw(playerX, playerY) # Use the new player_draw function
        show_score(score_textX, score_textY)
        show_highscore(score_textX, score_textY)
        show_status(score_textX, score_textY) # Display HP and MP below score/highscore
        show_level(score_textX, score_textY) # Display current level

        # Draw elegant pause button icon
        # Draw the button background with a slight border radius for a softer look
        pygame.draw.rect(screen, (30, 30, 30), pause_button_rect, border_radius=5)  
        pygame.draw.rect(screen, (50, 50, 50), pause_button_rect, border_radius=5, width=2) # Light border

        # Draw the two vertical bars of the pause icon (changed color to yellow for better visibility)
        pygame.draw.rect(screen, (255, 255, 0), (pause_button_rect.x + pause_icon_padding,  
                                                     pause_button_rect.y + (pause_button_rect.height - pause_icon_height) / 2,  
                                                     pause_icon_width, pause_icon_height), border_radius=2)
        pygame.draw.rect(screen, (255, 255, 0), (pause_button_rect.x + pause_button_rect.width - pause_icon_width - pause_icon_padding,  
                                                     pause_button_rect.y + (pause_button_rect.height - pause_icon_height) / 2,  
                                                     pause_icon_width, pause_icon_height), border_radius=2)


    elif current_game_state == GAME_STATE_PAUSED:
        s = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180)) # Semi-transparent black overlay
        screen.blit(s, (0,0))

        pause_message = over_font.render("PAUSED", True, (255, 255, 255))
        screen.blit(pause_message, (screen_width / 2 - pause_message.get_width() / 2, screen_height / 3 - 100)) # Adjusted Y

        button_width_pause = 350 # Wider buttons
        button_height_pause = 80 # Taller buttons
        button_x_pause = screen_width / 2 - button_width_pause / 2
        button_spacing_pause = 30 # Increased space between buttons

        # Define the Rects for the buttons here to ensure they are up-to-date for drawing and collision
        resume_button_pause = pygame.Rect(button_x_pause, screen_height / 2 - 70, button_width_pause, button_height_pause)
        music_button_pause = pygame.Rect(button_x_pause, resume_button_pause.y + button_height_pause + button_spacing_pause, button_width_pause, button_height_pause)
        sfx_button_pause = pygame.Rect(button_x_pause, music_button_pause.y + button_height_pause + button_spacing_pause, button_width_pause, button_height_pause)
        quit_button_pause = pygame.Rect(button_x_pause, sfx_button_pause.y + button_height_pause + button_spacing_pause, button_width_pause, button_height_pause)

        # Resume Button
        pygame.draw.rect(screen, (70, 180, 70), resume_button_pause, border_radius=15) # Green resume button
        resume_text = game_font.render("Resume", True, (255, 255, 255))
        screen.blit(resume_text, (resume_button_pause.x + (resume_button_pause.width - resume_text.get_width()) / 2,
                                  resume_button_pause.y + (resume_button_pause.height - resume_text.get_height()) / 2))

        # Music Toggle Button
        music_text = "Music: ON" if music_enabled else "Music: OFF"
        pygame.draw.rect(screen, (100, 100, 200), music_button_pause, border_radius=15) # Blue-ish button
        music_render_text = game_font.render(music_text, True, (255, 255, 255))
        screen.blit(music_render_text, (music_button_pause.x + (music_button_pause.width - music_render_text.get_width()) / 2,
                                        music_button_pause.y + (music_button_pause.height - music_render_text.get_height()) / 2))

        # SFX Toggle Button
        sfx_text = "SFX: ON" if sfx_enabled else "SFX: OFF"
        pygame.draw.rect(screen, (200, 150, 50), sfx_button_pause, border_radius=15) # Orange-ish button
        sfx_render_text = game_font.render(sfx_text, True, (255, 255, 255))
        screen.blit(sfx_render_text, (sfx_button_pause.x + (sfx_button_pause.width - sfx_render_text.get_width()) / 2,
                                        sfx_button_pause.y + (sfx_button_pause.height - sfx_render_text.get_height()) / 2))

        # Quit Game Button
        pygame.draw.rect(screen, (180, 70, 70), quit_button_pause, border_radius=15) # Red quit button
        quit_render_text = game_font.render("Quit Game", True, (255, 255, 255))
        screen.blit(quit_render_text, (quit_button_pause.x + (quit_button_pause.width - quit_render_text.get_width()) / 2,
                                  quit_button_pause.y + (quit_button_pause.height - quit_render_text.get_height()) / 2))
    
    elif current_game_state == GAME_STATE_GAMEOVER:
        action = game_over_screen()
        if action == "restart":
            # Reset all game variables to initial state for a new game
            score_value = 0
            player_hp = player_max_hp
            player_mp = 0
            enemies_killed_since_last_gift = 0
            current_level = 1
            egg_drop_chance = base_egg_drop_chance # Reset egg drop chance
            
            initialize_enemies() # Re-initialize enemies for level 1
            
            bullets = []
            eggs = []
            gifts = []
            playerX = (screen_width - playerImg.get_width()) / 2
            playerY = screen_height - playerImg.get_height() - 20
            current_game_state = GAME_STATE_PLAYING
            is_firing_continuously = True
            firepower_boost_active = False
            fire_delay = original_fire_delay
            current_bullet_img = bulletImg_b1
            bullet_destroys_eggs = False
            boss = None # Ensure boss is reset
            level_display_timer = pygame.time.get_ticks() # Show Level 1
            if music_enabled: # Only play if music was enabled
                mixer.music.play(-1)
        elif action == "quit":
            running = False

    elif current_game_state == GAME_STATE_COMPLETED:
        action = game_completed_screen()
        if action == "restart":
            # Reset all game variables to initial state for a new game
            score_value = 0
            player_hp = player_max_hp
            player_mp = 0
            enemies_killed_since_last_gift = 0
            current_level = 1
            egg_drop_chance = base_egg_drop_chance # Reset egg drop chance
            
            initialize_enemies() # Re-initialize enemies for level 1
            
            bullets = []
            eggs = []
            gifts = []
            playerX = (screen_width - playerImg.get_width()) / 2
            playerY = screen_height - playerImg.get_height() - 20
            current_game_state = GAME_STATE_PLAYING
            is_firing_continuously = True
            firepower_boost_active = False
            fire_delay = original_fire_delay
            current_bullet_img = bulletImg_b1
            bullet_destroys_eggs = False
            boss = None # Ensure boss is reset
            level_display_timer = pygame.time.get_ticks() # Show Level 1
            if music_enabled: # Only play if music was enabled
                mixer.music.play(-1)
        elif action == "quit":
            running = False

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()