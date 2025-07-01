#import libraries
import pygame
import sys
import random
from pygame import mixer

#ball animation
def ball_animation():
    global ball_speed_x, ball_speed_y, player_score, enemy_score, score_time
    ball.x += ball_speed_x
    ball.y +=ball_speed_y
    
    if ball.top <= 0 or ball.bottom >= screen_height:
        ball_Sound.play()
        ball_speed_y *= -1
        
    if ball.left<= 0:
        player_score +=1
        score_time = pygame.time.get_ticks()
    
    if ball.right >= screen_width:
        enemy_score += 1
        score_time = pygame.time.get_ticks()
                
        
    if ball.colliderect(player) and ball_speed_x > 0:
            ball_Sound.play()
            if abs(ball.right - player.left) < 10:
                ball_speed_x *= -1
            elif abs(ball.bottom - player.top) < 10 and ball_speed_y > 0:
                ball_speed_y *= -1                       
            elif abs(ball.top - player.bottom) < 10 and ball_speed_y < 0:
                ball_speed_y *= -1            
            
    if ball.colliderect(enemy) and ball_speed_x < 0:
            ball_Sound.play()
            if abs(ball.left - enemy.right) < 10:
                ball_speed_x *= -1
            elif abs(ball.bottom - enemy.top) < 10 and ball_speed_y > 0:
                ball_speed_y *= -1                       
            elif abs(ball.top - enemy.bottom) < 10 and ball_speed_y < 0:
                ball_speed_y *= -1

        
#player animation
def player_animation():
    player.y += player_speed
    #player boundaries
    if player.top <= 0:
        player.top = 0
    if player.bottom >= screen_height:
        player.bottom = screen_height

#enemy AI animation
def enemy_ai():
    if enemy.top < ball.y:
        enemy.top += enemy_speed
    if enemy.bottom > ball.y:
        enemy.bottom -= enemy_speed
    #enemy boundaries 
    if enemy.top <= 0:
        enemy.top = 0
    if enemy.bottom >= screen_height:
        enemy.bottom = screen_height        

#ball posiotion reset
def ball_restart():
    global ball_speed_x, ball_speed_y, score_time
    
    current_time = pygame.time.get_ticks()    
    ball.center = (screen_width/2, screen_height/2)
            
    if current_time - score_time < 2100:
        ball_speed_x, ball_speed_y = 0,0
    else:            
        ball_speed_x = 10 * random.choice((1, -1))
        ball_speed_y = 10 * random.choice((1, -1))
        score_time = None
    
#initialize pygame
pygame.init()
clock = pygame.time.Clock()

#main window setup
screen_width = 2257
screen_height = 1080
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("PONG")

#game rectangles
ball = pygame.Rect(screen_width/2 - 30, screen_height/2 - 30, 60, 60)

player = pygame.Rect(screen_width - 60 , screen_height/2 - 70, 50, 300)

enemy = pygame.Rect(10, screen_height/2 - 70, 50, 300)

#colors
bg_color = pygame.Color("white")
black = (0,0,0)

#sound fx
ball_Sound = mixer.Sound("ball.mp3")

#ball speed
ball_speed_x = 10 * random.choice((1, -1))
ball_speed_y = 10 * random.choice((1, -1))
player_speed = 0
enemy_speed = 300 

#score
player_score = 0
enemy_score = 0
game_font = pygame.font.Font("freesansbold.ttf", 42)

#score timer
score_time = True

while True:
    #event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                player_speed += 10
            if event.key == pygame.K_UP:
                player_speed -= 10  
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                player_speed -= 10
            if event.key == pygame.K_UP:
                player_speed += 10                                                                                                                                  
                                    
    ball_animation()
    player_animation()
    enemy_ai()   
     
    #appearance 
    screen.fill(bg_color)
    pygame.draw.rect(screen, black, player)  
    pygame.draw.rect(screen, black, enemy)
    pygame.draw.ellipse(screen, black, ball)
    pygame.draw.aaline(screen, black, (screen_width/2, 0), (screen_width/2, screen_height))
    
    if score_time:
        ball_restart()
    
    player_text = game_font.render(f"{player_score}", False, black)
    screen.blit(player_text,(screen_width/2 + 55 ,screen_height/2 - 20))
    
    enemy_text = game_font.render(f"{enemy_score}", False, black)
    screen.blit(enemy_text,(screen_width/2 - 80 ,screen_height/2 - 20))   
     
    #update window
    pygame.display.flip()      
    clock.tick(60)            