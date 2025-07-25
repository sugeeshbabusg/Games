import pygame
import random
import math
from pygame import mixer
import os

# Initialize the pygame
pygame.init()

# Create the screen
screen_width = 1080  # Keep a similar width for detail, or adjust as needed
screen_height = 720  # Significantly reduced height for laptop screen
screen = pygame.display.set_mode((screen_width, screen_height))

# Background
background = pygame.image.load("space720.png")
# Scale background to fit new screen dimensions for the laptop version (1080x720)
background = pygame.transform.scale(background, (screen_width, screen_height)) # Scale to screen_width x screen_height

# Create a second background surface for seamless scrolling, twice the screen height
background_scrolling_image = pygame.Surface((screen_width, screen_height * 2))
background_scrolling_image.blit(background, (0, 0))
background_scrolling_image.blit(background, (0, screen_height)) # Place a duplicate below for seamless loop

background_height = background_scrolling_image.get_height()
background_y1 = 0
background_y2 = -screen_height # Start the second image above the first one's top

# Background sound
mixer.music.load("theme.mp3")
mixer.music.play(-1)

# Caption and icon
pygame.display.set_caption("Space Invaders Angry Birds Edition")
icon = pygame.image.load("ufo.png")
pygame.display.set_icon(icon)

# Player
playerImg = pygame.image.load("Pl3.png")
playerImg = pygame.transform.scale(playerImg, (100, 150)) # Halved player size for smaller screen
playerX = (screen_width - playerImg.get_width()) / 2  # Center player initially
playerY = screen_height - playerImg.get_height() - 10 # Initial player position 10px above bottom
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
current_bullet_img = pygame.transform.scale(current_bullet_img, (25, 75)) # Halved bullet size
bullet_destroys_eggs = False # For second powerup

# Player HP and MP
player_hp = 50
player_max_hp = 50
player_mp = 0
player_max_mp = 100 # Example max MP
damage_blink_duration = 500 # milliseconds for blinking
last_hit_time = 0
player_visible = True

# Enemy
enemyImg = []
enemyX = []
enemyY = []
enemyX_change = [] # Still used for horizontal oscillation
enemyY_speed = [] # Renamed for clarity: vertical speed
enemy_dead_state_active = [False] * 6 # To track if enemy is in dead state
enemy_dead_state_start_time = [0] * 6 # To track when dead state started
angry_dead_img = pygame.image.load("angry_dead.png") # Load the dead enemy image
angry_dead_img = pygame.transform.scale(angry_dead_img, (75, 75)) # Halved dead enemy size

num_of_enemies = 10
initial_enemy_y_speed_base = 0.025
initial_enemy_x_change_base = 0.025

def initialize_enemies():
    global enemyImg, enemyX, enemyY, enemyX_change, enemyY_speed, enemy_dead_state_active, enemy_dead_state_start_time
    enemyImg = []
    enemyX = []
    enemyY = []
    enemyX_change = []
    enemyY_speed = []
    enemy_dead_state_active = [False] * num_of_enemies
    enemy_dead_state_start_time = [0] * num_of_enemies

    for i in range(num_of_enemies):
        enemyImg.append(pygame.image.load("angryy.png"))
        enemyImg[i] = pygame.transform.scale(enemyImg[i], (75, 75)) # Halved enemy size
        enemyX.append(random.randint(0, screen_width - enemyImg[i].get_width()))
        enemyY.append(random.randint(-300, -50)) # Adjust start position for smaller screen
        
        enemyX_change.append(initial_enemy_x_change_base)
        enemyY_speed.append(random.uniform(initial_enemy_y_speed_base, initial_enemy_y_speed_base + 2))

initialize_enemies() # Initialize enemies at the start

# Boss
class Boss:
    def __init__(self):
        self.image = pygame.image.load("angryy.png")
        self.image = pygame.transform.scale(self.image, (75 * 3, 75 * 3)) # Scale relative to new enemy size
        self.rect = self.image.get_rect()
        self.x = (screen_width - self.rect.width) / 2
        self.y = -self.rect.height # Start off-screen at the top
        self.x_change = 7 
        self.y_speed = 1 
        self.hp = 200 # Boss HP
        self.hits_taken = 0
        self.dead = False
        self.entry_speed = 5 
        self.target_y = 50 # Adjust target Y position for the boss
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
        self.rect.topleft = (self.x, self.y)

    def take_hit(self):
        self.hp -= 1
        self.hits_taken += 1
        if self.hp <= 0:
            self.dead = True

boss = None # Initialize boss as None

# Eggs
eggImg = pygame.image.load("egg.png")
eggImg = pygame.transform.scale(eggImg, (40, 50)) # Halved egg size
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
gift1Img = pygame.transform.scale(gift1Img, (60, 60)) # Halved gift size
gift2Img = pygame.image.load("gift2.png") # Second gift image
gift2Img = pygame.transform.scale(gift2Img, (60, 60)) # Halved gift size

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
bulletImg_b1 = pygame.transform.scale(bulletImg_b1, (25, 75)) # Halved bullet size
bulletImg_b2 = pygame.image.load("b2.png") # Second bullet image
bulletImg_b2 = pygame.transform.scale(bulletImg_b2, (25, 75)) # Halved bullet size

bullets = [] # Stores (bulletX, bulletY, bullet_state, bullet_rect)
bulletY_change = 35 # Halved bullet speed for smaller screen

# Score
score_value = 0
# Adjusted font for general text, smaller for laptop screen
game_font = pygame.font.Font("freesansbold.ttf", 18)  
score_font = pygame.font.Font("freesansbold.ttf", 24)
level_font = pygame.font.Font("freesansbold.ttf", 30) # Smaller font for level

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
over_font = pygame.font.Font("freesansbold.ttf", 50) # Smaller font
game_name_font = pygame.font.Font("freesansbold.ttf", 30) # Smaller font

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
    screen.blit(hs_text, (x, y + 25)) # Adjusted y offset

def show_level(x, y):
    global level_display_timer
    if pygame.time.get_ticks() < level_display_timer + level_display_duration:
        level_text = level_font.render(f"Level {current_level}", True, (255, 255, 255)) # White color
        text_rect = level_text.get_rect(center=(screen_width / 2, screen_height / 2))
        screen.blit(level_text, text_rect)

def show_status(x, y_offset):
    # Position HP/MP below score/highscore
    hp_text = game_font.render(f"HP: {player_hp}/{player_max_hp}", True, (255, 50, 50)) # Softer red
    mp_text = game_font.render(f"MP: {player_mp}/{player_max_mp}", True, (50, 150, 255)) # Softer blue
    
    screen.blit(hp_text, (x, y_offset + 50)) # Adjusted y offset
    screen.blit(mp_text, (x, y_offset + 70)) # Adjusted y offset

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
    button_width = 150 # Smaller buttons
    button_height = 35 # Smaller buttons
    button_x = screen_width / 2 - button_width / 2
    button_spacing = 15 # Space between buttons

    restart_button = pygame.Rect(button_x, screen_height / 1.7, button_width, button_height)
    exit_button = pygame.Rect(button_x, restart_button.y + button_height + button_spacing, button_width, button_height)

    # Draw buttons with rounded corners and subtle shadows/borders
    pygame.draw.rect(screen, (0, 150, 0), restart_button, border_radius=15) # Green
    pygame.draw.rect(screen, (150, 0, 0), exit_button, border_radius=15) # Red

    # Add a subtle border/shadow effect to buttons
    pygame.draw.rect(screen, (50, 200, 50), restart_button, border_radius=15, width=3)
    pygame.draw.rect(screen, (200, 50, 50), exit_button, border_radius=15, width=3)

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

    button_width = 150
    button_height = 35
    button_x = screen_width / 2 - button_width / 2
    button_spacing = 15

    restart_button = pygame.Rect(button_x, screen_height / 1.7, button_width, button_height)
    exit_button = pygame.Rect(button_x, restart_button.y + button_height + button_spacing, button_width, button_height)

    pygame.draw.rect(screen, (0, 150, 0), restart_button, border_radius=15)
    pygame.draw.rect(screen, (150, 0, 0), exit_button, border_radius=15)

    pygame.draw.rect(screen, (50, 200, 50), restart_button, border_radius=15, width=3)
    pygame.draw.rect(screen, (200, 50, 50), exit_button, border_radius=15, width=3)

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
        bullet_Sound = mixer.Sound("laser.wav")
        bullet_Sound.play()
        
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
intro_image = pygame.image.load("intro.png")
intro_image = pygame.transform.scale(intro_image, (screen_width, screen_height)) # Scale intro image

# Pause button (modern icon: two vertical rectangles)
pause_button_rect = pygame.Rect(screen_width - 45, 5, 40, 25) # Smaller rect for easier clicking
pause_icon_width = 6
pause_icon_height = 18
pause_icon_padding = 4

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
                resume_button = pygame.Rect(screen_width / 2 - 75, screen_height / 2 - 35, 150, 40) # Smaller buttons
                quit_button = pygame.Rect(screen_width / 2 - 75, screen_height / 2 + 25, 150, 40) # Smaller buttons

                if resume_button.collidepoint(mouse_x, mouse_y):
                    current_game_state = GAME_STATE_PLAYING
                    is_firing_continuously = True # Resume continuous firing
                elif quit_button.collidepoint(mouse_x, mouse_y):
                    running = False
            
    # Game State Logic
    if current_game_state == GAME_STATE_INTRO:
        screen.blit(intro_image, (0, 0))

    elif current_game_state == GAME_STATE_PLAYING:
        # Infinite background scrolling
        scroll_speed = 2# Reduced scroll speed
        background_y1 += scroll_speed
        background_y2 += scroll_speed

        if background_y1 > screen_height:
            background_y1 = -screen_height
        if background_y2 > screen_height:
            background_y2 = -screen_height

        screen.blit(background_scrolling_image, (0, background_y1))
        screen.blit(background_scrolling_image, (0, background_y2))

        # Check for level progression
        if current_level < 5 and score_value >= score_for_next_level * current_level:
            current_level += 1
            level_display_timer = pygame.time.get_ticks() # Start level change display
            mixer.Sound("levelup.mp3").play() # Play a level up sound
            
            if current_level < 5: # Increase difficulty for regular levels
                # Increase enemy speed and egg drop chance
                for i in range(num_of_enemies):
                    enemyY_speed[i] += 0.25 # Slightly increased vertical speed
                    enemyX_change[i] = abs(enemyX_change[i]) + 0.5 # Slightly increased horizontal speed (ensure positive)
                    if enemyX[i] >= screen_width - enemyImg[i].get_width(): # Adjust if already at edge
                        enemyX_change[i] *= -1
                egg_drop_chance *= 1.1 # Increase egg drop chance by 10%
                
            elif current_level == 5:
                # Clear all regular enemies
                for i in range(num_of_enemies):
                    enemyY[i] = -1000 # Move enemies far off-screen
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

                # Handle enemy dead state
                if enemy_dead_state_active[i]:
                    if current_time - enemy_dead_state_start_time[i] < 200: # 1 second duration
                        screen.blit(angry_dead_img, (enemyX[i], enemyY[i]))
                    else:
                        enemy_dead_state_active[i] = False
                        # After 1 second, reset enemy normally
                        enemyY[i] = random.randint(-300, -50) # Adjusted start position for smaller screen
                        enemyX[i] = random.randint(0, screen_width - enemyImg[i].get_width())
                        # Enemy speeds already increased with level, just re-randomize vertical start speed
                        enemyY_speed[i] = random.uniform(initial_enemy_y_speed_base + (current_level - 1) * 0.25, 
                                                         initial_enemy_y_speed_base + (current_level - 1) * 0.25 + 2)
                else:
                    enemyY[i] += enemyY_speed[i]
                    enemyX[i] += enemyX_change[i]

                    if enemyX[i] <= 0 or enemyX[i] >= screen_width - enemyImg[i].get_width():
                        enemyX_change[i] *= -1

                    if enemyY[i] > screen_height:
                        enemyY[i] = random.randint(-300, -50) # Adjusted start position for smaller screen
                        enemyX[i] = random.randint(0, screen_width - enemyImg[i].get_width())
                        enemyY_speed[i] = random.uniform(initial_enemy_y_speed_base + (current_level - 1) * 0.25, 
                                                         initial_enemy_y_speed_base + (current_level - 1) * 0.25 + 2)

                    # Randomly drop eggs from enemies (less frequent)
                    if random.random() < egg_drop_chance:
                        eggs.append(Egg(enemyX[i] + enemyImg[i].get_width() / 2 - eggImg.get_width() / 2,
                                         enemyY[i] + enemyImg[i].get_height())) # Egg comes from beneath the enemy

                    # Player-Enemy Collision Check
                    if is_collision(player_rect, enemy_rect):
                        if current_time - last_hit_time > damage_blink_duration: # Prevent rapid hits
                            player_hp -= 30
                            last_hit_time = current_time
                            mixer.Sound("collision.mp3").play()
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
                                mixer.Sound("collision.mp3").play()
                                
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
                    
                    # Draw the enemy
                    if not enemy_dead_state_active[i]:
                        screen.blit(enemyImg[i], (enemyX[i], enemyY[i])) # Corrected: Use screen.blit directly
        
        elif current_level == 5 and boss: # Boss battle
            boss.move()
            boss.draw()

            # Player-Boss Collision Check (similar to enemy)
            if is_collision(player_rect, boss.rect):
                if current_time - last_hit_time > damage_blink_duration:
                    player_hp -= 50 # Boss hits harder
                    last_hit_time = current_time
                    mixer.Sound("collision.mp3").play()
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
                        mixer.Sound("boss_hit.mp3").play() # A sound for hitting boss
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
                            mixer.Sound("explosion.wav").play() # Explosion sound for boss
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
                            mixer.Sound("collision.mp3").play()
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
                    mixer.Sound("collision.mp3").play() # Use collision sound for egg as well
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
                mixer.Sound("col.mp3").play() # Sound for collecting gift
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

        # Draw the two vertical bars of the pause icon
        pygame.draw.rect(screen, (255, 255, 255), (pause_button_rect.x + pause_icon_padding,  
                                                     pause_button_rect.y + (pause_button_rect.height - pause_icon_height) / 2,  
                                                     pause_icon_width, pause_icon_height), border_radius=2)
        pygame.draw.rect(screen, (255, 255, 255), (pause_button_rect.x + pause_button_rect.width - pause_icon_width - pause_icon_padding,  
                                                     pause_button_rect.y + (pause_button_rect.height - pause_icon_height) / 2,  
                                                     pause_icon_width, pause_icon_height), border_radius=2)


    elif current_game_state == GAME_STATE_PAUSED:
        s = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180)) # Semi-transparent black overlay
        screen.blit(s, (0,0))

        pause_message = over_font.render("PAUSED", True, (255, 255, 255))
        screen.blit(pause_message, (screen_width / 2 - pause_message.get_width() / 2, screen_height / 3))

        button_width = 150
        button_height = 40
        button_x = screen_width / 2 - button_width / 2
        button_spacing = 15 # Space between buttons

        resume_button = pygame.Rect(button_x, screen_height / 2 - 35, button_width, button_height)
        pygame.draw.rect(screen, (70, 180, 70), resume_button, border_radius=15) # Green resume button
        resume_text = game_font.render("Resume", True, (255, 255, 255))
        screen.blit(resume_text, (resume_button.x + (resume_button.width - resume_text.get_width()) / 2,
                                  resume_button.y + (resume_button.height - resume_text.get_height()) / 2))

        quit_button = pygame.Rect(button_x, resume_button.y + button_height + button_spacing, button_width, button_height)
        pygame.draw.rect(screen, (180, 70, 70), quit_button, border_radius=15) # Red quit button
        quit_text = game_font.render("Quit Game", True, (255, 255, 255))
        screen.blit(quit_text, (quit_button.x + (quit_button.width - quit_text.get_width()) / 2,
                                  quit_button.y + (quit_button.height - quit_text.get_height()) / 2))
    
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
            playerY = screen_height - playerImg.get_height() - 10 # Adjusted initial player Y
            current_game_state = GAME_STATE_PLAYING
            is_firing_continuously = True
            firepower_boost_active = False
            fire_delay = original_fire_delay
            current_bullet_img = bulletImg_b1
            bullet_destroys_eggs = False
            boss = None # Ensure boss is reset
            level_display_timer = pygame.time.get_ticks() # Show Level 1
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
            playerY = screen_height - playerImg.get_height() - 10 # Adjusted initial player Y
            current_game_state = GAME_STATE_PLAYING
            is_firing_continuously = True
            firepower_boost_active = False
            fire_delay = original_fire_delay
            current_bullet_img = bulletImg_b1
            bullet_destroys_eggs = False
            boss = None # Ensure boss is reset
            level_display_timer = pygame.time.get_ticks() # Show Level 1
            mixer.music.play(-1)
        elif action == "quit":
            running = False

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()