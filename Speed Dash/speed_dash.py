#import libaries
import pygame
from pygame.locals import *
import random
from pygame import mixer
import pygame.font

size = width , height = (1080,2257)#perfect size

FPS=60
# animation parameters
speed = 200

#initialize the game
pygame.init()

running=True
#create screen
screen = pygame.display.set_mode(size)


#background
background = pygame.image.load("road.png")

#background sound
mixer.music.load("bg.wav")
mixer.music.play(-1)

#set caption
pygame.display.set_caption("Sugeesh のカー ゲーム")

#Player
playerImg = pygame.image.load("car1.png")
player_loc = playerImg.get_rect()
player_loc.center = 340,1800
playerX_change = 0

#Enemy
enemyImg = pygame.image.load("truck1.png")
enemy_loc = enemyImg.get_rect()
enemy_loc.center = 740,200

# Stopwatch font
font = pygame.font.Font("freesansbold.ttf" , 50)

# Create masks for player and enemy
player_mask = pygame.mask.from_surface(playerImg)
enemy_mask = pygame.mask.from_surface(enemyImg)

dragging = False

#game over text
over_font = pygame.font.Font("freesansbold.ttf",100)


def game_over_text():
    over_text = over_font.render("GAME   OVER",True,(255,255,255))
    screen.blit(over_text,(190,1000))

# Function for pixel-perfect collision detection
def is_collision(player_rect, enemy_rect):
    offset = (enemy_rect.x - player_rect.x, enemy_rect.y - player_rect.y)
    return player_mask.overlap(enemy_mask, offset)

# Display the stopwatch
def display_stopwatch(time):
    stopwatch_text = font.render("TIME: " + str(time) +"s", True, (240,0,255))  # color
    screen.blit(stopwatch_text, (780, 20))  # Adjust the position as needed

# Background position
bg_y = 0

counter = 0

# Initialize the clock
clock = pygame.time.Clock()

#Game loop
running = True
elapsed_time = 0
while running:
    
    counter += 1

    # increase game difficulty overtime
    if counter == 100:
        speed += 50
        counter = 0
        #print("level up", speed)
    
    #RGB
    screen.fill((10,20,20))
    
    # Update background position
    screen.blit(background, (0, bg_y))
    screen.blit(background, (0, bg_y - height))  # Display a second background image above the first one
    bg_y += speed
    if bg_y >= height:
        bg_y = 0
    
    # animate enemy vehicle
    enemy_loc[1] += speed + 50
    if enemy_loc[1] > height:
        # randomly select lane
        if random.randint(0,1) == 0:
            enemy_loc.center = 340,-200
        else:
            enemy_loc.center = 740, -200        
                         
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEMOTION:
            if dragging:
                x, y = event.pos
                player_loc.center = x, y

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button (drag start)
                if player_loc.collidepoint(event.pos):
                    dragging = True

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 0:  # Left mouse button (drag end)
                dragging = False
   
    #checking for boundaries  so player doesn't go out of bounds
    
    
    if player_loc[0]<= 150:
        player_loc[0]= 150
    elif  player_loc[0] >= 580:
        player_loc[0] = 580                
    elif player_loc[1]<= 0:
        player_loc[1]= 0
    elif  player_loc[1] >= 2000:
        player_loc[1] = 2000 
        
    # Check for collision
    if is_collision(player_loc, enemy_loc):
        explosion_Sound = mixer.Sound("collision2.mp3")
        explosion_Sound.play()
        game_over_text()
        pygame.display.update()
        pygame.time.delay(1000)  # Pause for a moment to display "GAME OVER" before exiting
        running = False        
      
    display_stopwatch(elapsed_time)  # Display the stopwatch        
            
    # place car images on the screen
    screen.blit(playerImg,player_loc)
    screen.blit(enemyImg,enemy_loc)
    
    # apply changes
    pygame.display.update()
    
    # Control the frame rate
    clock.tick(FPS)
    
    elapsed_time = pygame.time.get_ticks() // 1000

# collapse application window
pygame.quit()        