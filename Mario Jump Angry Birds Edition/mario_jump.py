import pygame
import random
import os
import math # For sine wave animations
from pygame import mixer

# initialize pygame
pygame.init()

# window dimensions
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 2257

# create game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mario Jump")

# frame rate
clock = pygame.time.Clock()
FPS = 60

# game variables
SCROLL_THRESHOLD = SCREEN_HEIGHT // 4
GRAVITY = 5
MAX_PLATFORMS = 10
MAX_ENEMIES = 2
MAX_FIREBALLS = 15
MAX_DIAMONDS = 5 # Limit the number of diamonds on screen
scroll = 0
bg_scroll = 0
game_over = False
game_started = False
paused = False # New variable for pause state
score = 0
vertical_score = 0
kill_score = 0
diamond_score = 0 # Score from collecting diamonds

# Animation states and timers for intro and game over
# Intro Screen Animations
intro_title_y_target = SCREEN_HEIGHT // 2 - 350
intro_title_y_current = -200 # Start off-screen
intro_title_animation_speed = 400 # pixels per frame
intro_buttons_alpha = 0 # Start fully transparent
intro_buttons_fade_speed = 280 # alpha units per frame
intro_animation_done = False # True when intro animations are complete

# Game Over Screen Animations
gameover_reveal_radius = 0 # Start with no circle
gameover_reveal_speed = 1060 # pixels per frame
gameover_max_reveal_radius = int(math.hypot(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)) * 1.5 # Covers entire screen
gameover_elements_alpha = 0 # Start fully transparent (for text/buttons)
gameover_elements_fade_speed = 1060 # alpha units per frame
gameover_animation_done = False # True when game over animations are complete
game_over_alpha_overlay = None # Will be initialized when game_over is triggered

# High score
if os.path.exists("score.txt"):
    with open("score.txt", "r") as file:
        high_score = int(file.read())
else:
    high_score = 0

# define colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
AQUA = (153, 217, 234)
RED_BRIGHT = (255 , 0 , 0)
STAR_COLOR = (150, 150, 150)
HIGHLIGHT_COLOR = (200, 200, 200)
SHADOW_COLOR = (100, 100, 100)

# Diamond Colors
DIAMOND_COLOR = (173, 216, 230) # Light Blue
DIAMOND_SHINE_COLOR = (240, 248, 255) # Alice Blue for sparkle

# Modern Screen Gradient Colors (Dynamic)
# These will be the base, and we'll shift them for animation
BASE_GRADIENT_TOP = (40, 40, 60)
BASE_GRADIENT_BOTTOM = (20, 20, 30)

# Button colors and dimensions - Made square for circular buttons
BUTTON_SIZE = 200
BUTTON_WIDTH = BUTTON_SIZE
BUTTON_HEIGHT = BUTTON_SIZE
BUTTON_MARGIN = 50
BUTTON_NORMAL_COLOR = (70, 70, 70) # Darker grey for modern feel
BUTTON_HOVER_COLOR = (120, 120, 120) # Lighter grey on hover
BUTTON_PRESSED_COLOR = (180, 180, 180) # Even lighter when pressed

# define font
try:
    font_name = "Montserrat" # A clean, modern sans-serif font
    font_small = pygame.font.SysFont(font_name, 60)
    font_big = pygame.font.SysFont(font_name, 84)
    font_huge = pygame.font.SysFont(font_name, 160)
    font_game_over_title = pygame.font.SysFont(font_name, 120)
    font_button = pygame.font.SysFont(font_name, 100)
    font_intro_note = pygame.font.SysFont(font_name, 90)
except pygame.error:
    print(f"Error: {font_name} font not found. Using default system font.")
    font_small = pygame.font.SysFont(None, 60)
    font_big = pygame.font.SysFont(None, 84)
    font_huge = pygame.font.SysFont(None, 160)
    font_game_over_title = pygame.font.SysFont(None, 120)
    font_button = pygame.font.SysFont(None, 100)
    font_intro_note = pygame.font.SysFont(None, 90)

# Load images
player_img = pygame.image.load("mario.png").convert_alpha()

# Main game background remains
bg_image = pygame.image.load("sky4.png")
bg_image = pygame.transform.scale(bg_image, (1080, 2255))

platform_img = pygame.image.load("grass.png").convert_alpha()

# Load enemy image
enemy_img = pygame.image.load("enemy2.png").convert_alpha()

# Load sounds
dead_Sound = mixer.Sound("game_over.wav")
fireball_sound = mixer.Sound("fireball.wav")
stomp_sound = mixer.Sound("stomp.mp3")
fireball_hit_sound = mixer.Sound("hit.mp3")
diamond_collect_sound = mixer.Sound("coin.mp3")

# On-screen button state variable for single press detection
fire_button_was_pressed_last_frame = False

# Global variables for pre-rendered text surfaces (optimization)
# Intro screen text
game_name_intro_surface = font_huge.render("MARIO JUMP", True, WHITE)

# Game over screen text (will be rendered on game_over event)
game_over_text_surface = None
score_text_surface_go = None 
high_score_text_surface_go = None


# function for printing the text on screen
def draw_text(text_surface, x, y, surface, alpha=255):
    """Draws a pre-rendered text surface with a specific alpha."""
    if text_surface is None: # Handle cases where text might not be rendered yet
        return

    # Create a temporary surface to apply alpha
    temp_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
    temp_surface.blit(text_surface, (0, 0)) # Blit the pre-rendered text onto it
    temp_surface.set_alpha(alpha) # Set alpha for the entire temporary surface
    surface.blit(temp_surface, (x, y)) # Blit to the target surface


# Function to draw a simple gradient background with animation
def draw_animated_gradient_background(surface, top_color_base, bottom_color_base, time_elapsed_ms):
    # Calculate color shift based on time
    shift_amount = (math.sin(time_elapsed_ms / 1500) + 1) / 2 # 0 to 1 over approx 3 seconds
    
    # Slight color variations
    top_r = top_color_base[0] + int(10 * shift_amount)
    top_g = top_color_base[1] + int(10 * shift_amount)
    top_b = top_color_base[2] + int(20 * shift_amount)

    bottom_r = bottom_color_base[0] - int(10 * shift_amount)
    bottom_g = bottom_color_base[1] - int(10 * shift_amount)
    bottom_b = bottom_color_base[2] - int(20 * shift_amount)

    current_top_color = (max(0, min(255, top_r)), max(0, min(255, top_g)), max(0, min(255, top_b)))
    current_bottom_color = (max(0, min(255, bottom_r)), max(0, min(255, bottom_g)), max(0, min(255, bottom_b)))

    # Draw lines for the gradient
    for y in range(surface.get_height()):
        r = current_top_color[0] + (current_bottom_color[0] - current_top_color[0]) * y / surface.get_height()
        g = current_top_color[1] + (current_bottom_color[1] - current_top_color[1]) * y / surface.get_height()
        b = current_top_color[2] + (current_bottom_color[2] - current_top_color[2]) * y / surface.get_height()
        pygame.draw.line(surface, (int(r), int(g), int(b)), (0, y), (surface.get_width(), y))


# function for drawing the score
def draw_score():
    pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, 50))
    pygame.draw.line(screen, WHITE, (0, 50), (SCREEN_WIDTH, 50), 2)

    score_text_surface = font_big.render("SCORE : " + str(score), True, WHITE)
    screen.blit(score_text_surface, (30, 5))

    high_score_text_surface = font_big.render("H S : " + str(high_score), True, WHITE)
    high_score_x = SCREEN_WIDTH - high_score_text_surface.get_width() - 50
    screen.blit(high_score_text_surface, (high_score_x, 5))


# function for drawing the background
def draw_bg(bg_scroll):
    screen.blit(bg_image, (0, 0 + bg_scroll))
    screen.blit(bg_image, (0, -2255 + bg_scroll))


# player class
class Player():
    def __init__(self, x, y):
        self.image = pygame.transform.scale(player_img, (120, 120))
        self.width = 105
        self.height = 115
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        self.vel_y = 0
        self.flip = False

    def move(self, move_left, move_right):
        scroll = 0
        dx = 0
        dy = 0

        if move_left:
            dx = -50
            self.flip = True
        if move_right:
            dx = +50
            self.flip = False

        self.vel_y += GRAVITY
        dy += self.vel_y

        for platform in platform_group:
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.rect.bottom < platform.rect.centery:
                    if self.vel_y > 0:
                        self.rect.bottom = platform.rect.top
                        dy = 0
                        self.vel_y = -70
                        jump_Sound = mixer.Sound("jump6.mp3")
                        jump_Sound.play()

        for enemy in enemy_group.copy():
            if self.rect.colliderect(enemy.rect):
                if self.vel_y > 0 and self.rect.bottom <= enemy.rect.centery:
                    enemy.kill()
                    global kill_score
                    kill_score += 200
                    self.vel_y = -50
                    stomp_sound.play()
                else:
                    global game_over # This sets game_over = True
                    game_over = True
                    dead_Sound.play()
                    
                    # Initialize game over elements when enemy collision causes game over
                    global gameover_reveal_radius, gameover_elements_alpha, gameover_animation_done, game_over_alpha_overlay
                    global game_over_text_surface, score_text_surface_go, high_score_text_surface_go

                    gameover_reveal_radius = 0
                    gameover_elements_alpha = 0
                    gameover_animation_done = False
                    game_over_alpha_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA) # Initialize overlay

                    # PRE-RENDER GAME OVER TEXT ONCE
                    game_over_text_surface = font_big.render("GAME OVER!", True, WHITE)
                    score_text_surface_go = font_big.render("SCORE : " + str(score), True, WHITE)
                    high_score_text_surface_go = font_big.render("HIGH SCORE : " + str(high_score), True, WHITE)


        if self.rect.top <= SCROLL_THRESHOLD:
            if self.vel_y < 0:
                scroll = -dy

        self.rect.x += dx
        # Implement screen wrap-around
        if self.rect.right < 0:  # If player moves off the left side
            self.rect.left = SCREEN_WIDTH  # Appear on the right side
        if self.rect.left > SCREEN_WIDTH:  # If player moves off the right side
            self.rect.right = 0  # Appear on the left side

        self.rect.y += dy + scroll

        return scroll

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x - 12, self.rect.y - 5))


# platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, moving):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(platform_img, (width + 100, 100))
        self.moving = moving
        self.move_counter = random.randint(0, 50)
        self.direction = random.choice([-1, 1])
        self.speed = random.randint(1, 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, scroll):
        if self.moving == True:
            self.move_counter += 1
            self.rect.x += self.direction * self.speed

        if self.move_counter >= 200 or self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.direction *= -1
            self.move_counter = 0

        self.rect.y += scroll

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, associated_platform=None):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(enemy_img, (160, 160))
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, y)
        self.associated_platform = associated_platform
        self.vel_y = 0
        self.is_jumping = False

    def update(self, scroll):
        if self.is_jumping:
            self.vel_y += GRAVITY
            self.rect.y += self.vel_y

            if self.associated_platform and self.rect.bottom > self.associated_platform.rect.top:
                self.rect.bottom = self.associated_platform.rect.top
                self.is_jumping = False
                self.vel_y = 0
            elif self.rect.top > SCREEN_HEIGHT:
                self.kill()

        self.rect.y += scroll

        if self.associated_platform and self.associated_platform.moving and not self.is_jumping:
            self.rect.centerx = self.associated_platform.rect.centerx

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def jump(self):
        if not self.is_jumping:
            self.vel_y = -30
            self.is_jumping = True

    def draw(self, screen):
        screen.blit(self.image, self.rect)


# Fireball class (now drawing a ninja star with pre-rendered rotations)
class Fireball(pygame.sprite.Sprite):
    _pre_rendered_stars = {}

    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.size = 40
        self.speed = 25
        self.direction = direction
        self.rotation = 0
        self.rotation_speed = 15

        if self.size not in Fireball._pre_rendered_stars:
            Fireball._pre_rendered_stars[self.size] = self._generate_rotated_stars()

        self.images = Fireball._pre_rendered_stars[self.size]
        self.current_image_index = 0

        self.image = self.images[self.current_image_index]
        self.rect = self.image.get_rect(center=(x, y))


    def _generate_star_surface(self):
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center_x, center_y = self.size // 2, self.size // 2
        outer_radius = self.size // 2
        inner_radius = self.size // 4

        triangle1_points = [
            (center_x, center_y - outer_radius),
            (center_x - outer_radius, center_y + inner_radius),
            (center_x + outer_radius, center_y + inner_radius)
        ]
        triangle2_points = [
            (center_x, center_y + outer_radius),
            (center_x - outer_radius, center_y - inner_radius),
            (center_x + outer_radius, center_y - inner_radius)
        ]

        pygame.draw.polygon(surface, STAR_COLOR, triangle1_points)
        pygame.draw.polygon(surface, STAR_COLOR, triangle2_points)

        pygame.draw.line(surface, HIGHLIGHT_COLOR, (center_x, center_y - outer_radius), (center_x + 5, center_y - outer_radius + 5), 2)
        pygame.draw.line(surface, SHADOW_COLOR, (center_x, center_y + outer_radius), (center_x - 5, center_y + outer_radius - 5), 2)
        return surface

    def _generate_rotated_stars(self):
        base_star = self._generate_star_surface()
        rotated_images = []
        rotation_step = 10
        for angle in range(0, 360, rotation_step):
            rotated_image = pygame.transform.rotate(base_star, angle)
            rotated_images.append(rotated_image)
        return rotated_images


    def update(self, current_scroll):
        self.rect.x += self.speed * self.direction
        self.rect.y += current_scroll

        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        self.image = self.images[self.current_image_index]
        self.rect = self.image.get_rect(center=self.rect.center)


        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0:
            self.kill()

    def draw(self, screen):
        screen.blit(self.image, self.rect)


# Diamond Class
class Diamond(pygame.sprite.Sprite):
    def __init__(self, x, y, size=30):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self._draw_diamond()

    def _draw_diamond(self):
        center_x = self.size
        center_y = self.size
        half_width = self.size * 0.8
        half_height = self.size * 1.2

        top_triangle = [
            (center_x, center_y - half_height),
            (center_x - half_width, center_y),
            (center_x + half_width, center_y)
        ]
        bottom_triangle = [
            (center_x, center_y + half_height),
            (center_x - half_width, center_y),
            (center_x + half_width, center_y)
        ]

        pygame.draw.polygon(self.image, DIAMOND_COLOR, top_triangle)
        pygame.draw.polygon(self.image, DIAMOND_COLOR, bottom_triangle)

        pygame.draw.line(self.image, DIAMOND_SHINE_COLOR, (center_x, center_y - half_height), (center_x - half_width / 2, center_y / 2), 2)
        pygame.draw.line(self.image, DIAMOND_SHINE_COLOR, (center_x, center_y - half_height), (center_x + half_width / 2, center_y / 2), 2)
        pygame.draw.line(self.image, DIAMOND_SHINE_COLOR, (center_x - half_width, center_y), (center_x, center_y + half_height), 2)
        pygame.draw.line(self.image, DIAMOND_SHINE_COLOR, (center_x + half_width, center_y), (center_x, center_y + half_height), 2)
        pygame.draw.line(self.image, DIAMOND_SHINE_COLOR, (center_x, center_y - half_height), (center_x, center_y + half_height), 1)

    def update(self, scroll):
        self.rect.y += scroll
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def draw(self, screen):
        screen.blit(self.image, self.rect)


# Button class for on-screen controls
class Button():
    def __init__(self, x, y, width, height, text='', color=BUTTON_NORMAL_COLOR,
                 hover_color=BUTTON_HOVER_COLOR, pressed_color=BUTTON_PRESSED_COLOR, font=None, is_circle=True):
        self.original_rect = pygame.Rect(x, y, width, height) # Store original dimensions
        self.rect = self.original_rect.copy() # Current rect for drawing/collision
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        self.current_color = self.color
        self.font = font if font else pygame.font.SysFont(None, 80)
        self.is_hovered = False
        self.is_pressed_visual = False # For visual feedback when button is held down
        self.is_circle = is_circle

        self.animation_timer = 0
        self.animation_duration = 5 # frames for the scale animation (click pop)
        self.scale_factor = 0.95 # scale down to 95% when clicked

        self.pulsate_timer = 0 # For hover pulsating animation
        self.pulsate_amplitude = 0.03 # Max 3% size change
        self.pulsate_speed = 0.08 # Speed of pulsation

    def draw(self, screen_surface, alpha=255): # screen_surface is where it's drawn
        # Calculate current dimensions based on animation timers
        current_scale = 1.0

        if self.animation_timer > 0: # Click animation (priority)
            progress = (self.animation_duration - self.animation_timer) / self.animation_duration
            current_scale = 1 - (1 - self.scale_factor) * progress # Scale from 1 to scale_factor and back
        elif self.is_hovered: # Pulsating hover animation
            # Sine wave for smooth pulsing
            current_scale = 1 + self.pulsate_amplitude * math.sin(self.pulsate_timer * self.pulsate_speed)
        
        scaled_width = int(self.original_rect.width * current_scale)
        scaled_height = int(self.original_rect.height * current_scale)
        
        # Calculate draw_rect, centered on original position
        draw_rect = pygame.Rect(
            self.original_rect.centerx - scaled_width // 2,
            self.original_rect.centery - scaled_height // 2,
            scaled_width,
            scaled_height
        )
        
        # Determine current color for drawing
        if self.is_pressed_visual:
            self.current_color = self.pressed_color
        elif self.is_hovered:
            self.current_color = self.hover_color
        else:
            self.current_color = self.color

        # Apply alpha to color before drawing
        # Ensure alpha value is within valid range (0-255)
        final_alpha = int(alpha * (180/255)) # Base transparency for buttons
        final_alpha = max(0, min(255, final_alpha))

        background_color_with_alpha = (self.current_color[0], self.current_color[1], self.current_color[2], final_alpha)
        border_color_with_alpha = (200, 200, 200, int(alpha * (100/255))) # Border also fades

        if self.is_circle:
            radius = draw_rect.width // 2
            # Draw directly to the provided screen_surface
            pygame.draw.circle(screen_surface, background_color_with_alpha, draw_rect.center, radius)
            pygame.draw.circle(screen_surface, border_color_with_alpha, draw_rect.center, radius, width=3)
        else:
            # Draw directly to the provided screen_surface
            pygame.draw.rect(screen_surface, background_color_with_alpha, draw_rect, border_radius=15)
            pygame.draw.rect(screen_surface, border_color_with_alpha, draw_rect, width=3, border_radius=15)

        if self.text:
            # Render text with the given alpha
            text_alpha = max(0, min(255, alpha)) # Text alpha directly controlled by passed alpha
            text_surface = self.font.render(self.text, True, (WHITE[0], WHITE[1], WHITE[2], text_alpha))
            # Center text on the potentially scaled button
            text_rect = text_surface.get_rect(center=draw_rect.center)
            screen_surface.blit(text_surface, text_rect)

    def update(self, mouse_pos, mouse_buttons_held):
        # Update hover state based on original rect for consistent detection
        self.is_hovered = self.original_rect.collidepoint(mouse_pos)
        
        # Update pressed visual state
        if self.is_hovered and mouse_buttons_held[0] and not self.is_pressed_visual:
            self.animation_timer = self.animation_duration
            self.is_pressed_visual = True
        elif not mouse_buttons_held[0]:
            self.is_pressed_visual = False # Reset visual pressed state when button released

        # Decrement animation timer
        if self.animation_timer > 0:
            self.animation_timer -= 1
        
        # Update pulsate timer if hovered and not currently clicking
        if self.is_hovered and self.animation_timer == 0:
            self.pulsate_timer += 1
        else:
            self.pulsate_timer = 0 # Reset when not hovered or clicking

        self.rect = self.original_rect.copy() # Collision rect remains original size


# player instance
player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)

# create sprite groups
platform_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
fireball_group = pygame.sprite.Group()
diamond_group = pygame.sprite.Group()


# Create on-screen button instances
left_button = Button(BUTTON_MARGIN, SCREEN_HEIGHT - BUTTON_HEIGHT - BUTTON_MARGIN, BUTTON_SIZE, BUTTON_SIZE, '<', font=font_button)
right_button = Button(SCREEN_WIDTH - BUTTON_WIDTH - BUTTON_MARGIN, SCREEN_HEIGHT - BUTTON_HEIGHT - BUTTON_MARGIN,
                        BUTTON_SIZE, BUTTON_SIZE, '>', font=font_button)
fire_button = Button(SCREEN_WIDTH // 2 - BUTTON_WIDTH // 2, SCREEN_HEIGHT - BUTTON_HEIGHT * 1.5 - BUTTON_MARGIN,
                        BUTTON_SIZE, BUTTON_SIZE, 'F', font=font_button)

# Game Over and Pause Menu Buttons (non-circular)
GO_BUTTON_WIDTH = 800
GO_BUTTON_HEIGHT = 120
GO_BUTTON_Y_OFFSET = 150
GO_BUTTON_SPACING = 50

restart_button_go = Button(SCREEN_WIDTH // 2 - GO_BUTTON_WIDTH // 2, SCREEN_HEIGHT // 2 + GO_BUTTON_Y_OFFSET,
                           GO_BUTTON_WIDTH, GO_BUTTON_HEIGHT, 'RESTART', font=font_button, is_circle=False)
quit_button_go = Button(SCREEN_WIDTH // 2 - GO_BUTTON_WIDTH // 2, SCREEN_HEIGHT // 2 + GO_BUTTON_Y_OFFSET + GO_BUTTON_HEIGHT + GO_BUTTON_SPACING,
                        GO_BUTTON_WIDTH, GO_BUTTON_HEIGHT, 'QUIT', font=font_button, is_circle=False)

pause_resume_button = Button(SCREEN_WIDTH // 2 - GO_BUTTON_WIDTH // 2, SCREEN_HEIGHT // 2 - GO_BUTTON_HEIGHT - GO_BUTTON_SPACING,
                             GO_BUTTON_WIDTH, GO_BUTTON_HEIGHT, 'RESUME', font=font_button, is_circle=False)
pause_quit_button = Button(SCREEN_WIDTH // 2 - GO_BUTTON_WIDTH // 2, SCREEN_HEIGHT // 2 + GO_BUTTON_SPACING,
                           GO_BUTTON_WIDTH, GO_BUTTON_HEIGHT, 'QUIT', font=font_button, is_circle=False)

# Intro Screen Buttons
INTRO_BUTTON_WIDTH = 800
INTRO_BUTTON_HEIGHT = 120
INTRO_BUTTON_Y_START = SCREEN_HEIGHT // 2 + 100
INTRO_BUTTON_SPACING = 40

start_game_button_intro = Button(SCREEN_WIDTH // 2 - INTRO_BUTTON_WIDTH // 2, INTRO_BUTTON_Y_START,
                                 INTRO_BUTTON_WIDTH, INTRO_BUTTON_HEIGHT, 'START GAME', font=font_button, is_circle=False)
exit_game_button_intro = Button(SCREEN_WIDTH // 2 - INTRO_BUTTON_WIDTH // 2, INTRO_BUTTON_Y_START + INTRO_BUTTON_HEIGHT + INTRO_BUTTON_SPACING,
                                INTRO_BUTTON_WIDTH, INTRO_BUTTON_HEIGHT, 'EXIT', font=font_button, is_circle=False)

# create the starting platform
platform = Platform(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 100, 200, False)
platform_group.add(platform)

player_y_position = 0

def reset_game():
    global game_over, score, vertical_score, kill_score, diamond_score, scroll, bg_scroll, player_y_position, paused, game_started
    global intro_title_y_current, intro_buttons_alpha, intro_animation_done
    global gameover_reveal_radius, gameover_elements_alpha, gameover_animation_done, game_over_alpha_overlay
    global game_over_text_surface, score_text_surface_go, high_score_text_surface_go # Reset pre-rendered text

    game_over = False
    game_started = True # Game is restarted, so it's started
    score = 0
    vertical_score = 0
    kill_score = 0
    diamond_score = 0
    scroll = 0
    bg_scroll = 0
    player_y_position = 0
    paused = False # Ensure game is not paused after reset

    # Reset Intro animation states for next time it might appear
    intro_title_y_current = -200
    intro_buttons_alpha = 0
    intro_animation_done = False

    # Reset Game Over animation states and surfaces
    gameover_reveal_radius = 0
    gameover_elements_alpha = 0
    gameover_animation_done = False
    game_over_alpha_overlay = None # Reset overlay to be re-initialized

    # Clear pre-rendered game over text surfaces
    game_over_text_surface = None
    score_text_surface_go = None
    high_score_text_surface_go = None

    player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)

    platform_group.empty()
    enemy_group.empty()
    fireball_group.empty()
    diamond_group.empty()

    new_platform = Platform(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 100, 200, False)
    platform_group.add(new_platform)


# game loop
run = True
while run:
    # Get mouse position and button state once per frame
    mouse_x, mouse_y = pygame.mouse.get_pos()
    current_mouse_pos = (mouse_x, mouse_y)
    mouse_buttons_held = pygame.mouse.get_pressed() # (left_button, middle_button, right_button)

    time_elapsed_ms = pygame.time.get_ticks() # Get milliseconds for animations

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if score > high_score:
                high_score = score
                with open("score.txt", "w") as file:
                    file.write(str(high_score))
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: # Back button / Escape key
                if game_started and not game_over:
                    paused = not paused # Toggle pause state
                elif game_over or not game_started: # If on game over screen or intro, escape can quit
                    if score > high_score:
                        high_score = score
                        with open("score.txt", "w") as file:
                            file.write(str(high_score))
                    run = False
        
        if event.type == pygame.MOUSEBUTTONUP: # Check for mouse button releases
            if not game_started:
                # Click to start game from intro screen (only if buttons are visible)
                if intro_animation_done: # Ensure buttons are fully faded in before clickable
                    if start_game_button_intro.original_rect.collidepoint(event.pos):
                        game_started = True
                        reset_game() # Call reset to properly setup game and reset animation variables
                    elif exit_game_button_intro.original_rect.collidepoint(event.pos):
                        if score > high_score:
                            high_score = score
                            with open("score.txt", "w") as file:
                                file.write(str(high_score))
                        run = False
            elif game_over:
                # Check for clicks on game over buttons (only if fully visible)
                if gameover_animation_done:
                    if restart_button_go.original_rect.collidepoint(event.pos):
                        if score > high_score:
                            high_score = score
                            with open("score.txt", "w") as file:
                                file.write(str(high_score))
                        reset_game()
                    elif quit_button_go.original_rect.collidepoint(event.pos):
                        if score > high_score:
                            high_score = score
                            with open("score.txt", "w") as file:
                                file.write(str(high_score))
                        run = False
            elif paused:
                # Check for clicks on pause menu buttons
                if pause_resume_button.original_rect.collidepoint(event.pos):
                    paused = False
                elif pause_quit_button.original_rect.collidepoint(event.pos):
                    if score > high_score:
                        high_score = score
                        with open("score.txt", "w") as file:
                            file.write(str(high_score))
                    run = False

    # --- Game Logic and Drawing ---
    if not game_started:
        # Draw modern gradient background
        draw_animated_gradient_background(screen, BASE_GRADIENT_TOP, BASE_GRADIENT_BOTTOM, time_elapsed_ms)
        
        # Animate title sliding down
        if intro_title_y_current < intro_title_y_target:
            intro_title_y_current += intro_title_animation_speed
            if intro_title_y_current > intro_title_y_target:
                intro_title_y_current = intro_title_y_target
        else:
            # Once title is in place, start fading in buttons
            if intro_buttons_alpha < 255:
                intro_buttons_alpha += intro_buttons_fade_speed
                if intro_buttons_alpha >= 255:
                    intro_buttons_alpha = 255
                    intro_animation_done = True # Mark animation as complete
        
        # Use pre-rendered title surface
        game_name_img = game_name_intro_surface 
        game_name_x = (SCREEN_WIDTH - game_name_img.get_width()) // 2
        
        screen.blit(game_name_img, (game_name_x, intro_title_y_current))

        # Update and draw intro screen buttons with fade-in alpha
        start_game_button_intro.update(current_mouse_pos, mouse_buttons_held)
        exit_game_button_intro.update(current_mouse_pos, mouse_buttons_held)
        start_game_button_intro.draw(screen, alpha=intro_buttons_alpha) # Pass screen as surface
        exit_game_button_intro.draw(screen, alpha=intro_buttons_alpha) # Pass screen as surface


    elif game_over == False and not paused: # Game running state
        # Update on-screen controls' hover/press state (but actions handled by MOUSEBUTTONUP)
        left_button.update(current_mouse_pos, mouse_buttons_held)
        right_button.update(current_mouse_pos, mouse_buttons_held)
        fire_button.update(current_mouse_pos, mouse_buttons_held)

        # Player movement based on button states
        scroll = player.move(left_button.is_pressed_visual, right_button.is_pressed_visual) # Use is_pressed_visual for continuous movement

        # Fireball logic (triggered on button press, not release)
        if fire_button.is_pressed_visual and not fire_button_was_pressed_last_frame and len(fireball_group) < MAX_FIREBALLS:
            fireball_direction = 1 if not player.flip else -1
            fireball = Fireball(player.rect.centerx, player.rect.centery, fireball_direction)
            fireball_group.add(fireball)
            fireball_sound.play()

            for enemy in enemy_group: # Make enemies jump when player fires
                enemy.jump()

        fire_button_was_pressed_last_frame = fire_button.is_pressed_visual # Update for next frame

        player_y_position += scroll
        vertical_score = int(player_y_position / 100)
        score = vertical_score + kill_score + diamond_score # ADD diamond_score to total score

        collided_enemies = pygame.sprite.groupcollide(fireball_group, enemy_group, True, True)
        if collided_enemies:
            for fireball_obj, enemies_hit in collided_enemies.items(): # Iterate if multiple fireballs or enemies hit
                for enemy_obj in enemies_hit:
                    kill_score += 100
                    fireball_hit_sound.play()

        # Check for player-diamond collision
        collided_diamonds = pygame.sprite.spritecollide(player, diamond_group, True) # True means remove diamond
        if collided_diamonds:
            for diamond in collided_diamonds:
                diamond_score += 300 # Add points for collecting diamond
                diamond_collect_sound.play()


        draw_bg(bg_scroll)
        bg_scroll += scroll
        if bg_scroll >= 2255:
            bg_scroll = 0

        # generate the platforms
        if len(platform_group) < MAX_PLATFORMS:
            p_w = random.randint(60, 150)
            p_x = random.randint(0, SCREEN_WIDTH - p_w)
            last_platform = platform_group.sprites()[-1] if platform_group else platform
            p_y = last_platform.rect.y - random.randint(200, 250)
            p_type = random.randint(1, 2)
            if p_type == 1 and score > 2:
                p_moving = True
            else:
                p_moving = False
            new_platform = Platform(p_x, p_y, p_w, p_moving)
            platform_group.add(new_platform)

            # Spawn enemy on new platform (with a chance)
            if random.random() < 0.2 and len(enemy_group) < MAX_ENEMIES and score > 5:
                enemy = Enemy(new_platform.rect.centerx, new_platform.rect.top, new_platform)
                enemy_group.add(enemy)

            # Spawn diamond on new platform (with a chance)
            if random.random() < 0.3 and len(diamond_group) < MAX_DIAMONDS and score > 0:
                # Position the diamond slightly above the platform
                diamond = Diamond(new_platform.rect.centerx, new_platform.rect.top - 30)
                diamond_group.add(diamond)


        # update all sprites
        platform_group.update(scroll)
        enemy_group.update(scroll)
        fireball_group.update(scroll)
        diamond_group.update(scroll)


        # draw sprites
        platform_group.draw(screen)
        for enemy in enemy_group:
            enemy.draw(screen)
        for fireball in fireball_group:
            fireball.draw(screen)
        for diamond in diamond_group:
            diamond.draw(screen)


        player.draw()

        left_button.draw(screen)
        right_button.draw(screen)
        fire_button.draw(screen)

        draw_score()

        if player.rect.top > SCREEN_HEIGHT:
            game_over = True
            dead_Sound.play()
            # Reset game over animation states for fresh start
            gameover_reveal_radius = 0
            gameover_elements_alpha = 0
            gameover_animation_done = False
            game_over_alpha_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA) # Initialize overlay

            # PRE-RENDER GAME OVER TEXT ONCE
            game_over_text_surface = font_big.render("GAME OVER!", True, WHITE)
            score_text_surface_go = font_big.render("SCORE : " + str(score), True, WHITE)
            high_score_text_surface_go = font_big.render("HIGH SCORE : " + str(high_score), True, WHITE)
            
    elif game_over: # Game over screen
        # Draw modern gradient background
        draw_animated_gradient_background(screen, BASE_GRADIENT_TOP, BASE_GRADIENT_BOTTOM, time_elapsed_ms)

        # Animate expanding circle reveal on the overlay
        if gameover_reveal_radius < gameover_max_reveal_radius:
            gameover_reveal_radius += gameover_reveal_speed
            if gameover_reveal_radius >= gameover_max_reveal_radius:
                gameover_reveal_radius = gameover_max_reveal_radius
        else:
            # Once circle is fully expanded, start fading in elements
            if gameover_elements_alpha < 255:
                gameover_elements_alpha += gameover_elements_fade_speed
                if gameover_elements_alpha >= 255:
                    gameover_elements_alpha = 255
                    gameover_animation_done = True # Mark animation as complete
        
        # Create and draw the alpha overlay with the expanding hole
        game_over_alpha_overlay.fill((0, 0, 0, 200)) # Fill with semi-transparent black

        # Draw an opaque circle on a temporary surface, then blit with BLEND_RGBA_SUB to punch hole
        temp_circle_surface = pygame.Surface(game_over_alpha_overlay.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(temp_circle_surface, (0, 0, 0, 255), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), gameover_reveal_radius)
        game_over_alpha_overlay.blit(temp_circle_surface, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        
        screen.blit(game_over_alpha_overlay, (0,0)) # Blit the overlay to the screen

        # Display game over texts (using pre-rendered surfaces and draw_text helper)
        draw_text(game_name_intro_surface, (SCREEN_WIDTH - game_name_intro_surface.get_width()) // 2, SCREEN_HEIGHT // 2 - 400, screen, alpha=gameover_elements_alpha)
        draw_text(game_over_text_surface, (SCREEN_WIDTH - game_over_text_surface.get_width()) // 2, SCREEN_HEIGHT // 2 - 250, screen, alpha=gameover_elements_alpha)
        draw_text(score_text_surface_go, (SCREEN_WIDTH - score_text_surface_go.get_width()) // 2, SCREEN_HEIGHT // 2 - 100, screen, alpha=gameover_elements_alpha)
        draw_text(high_score_text_surface_go, (SCREEN_WIDTH - high_score_text_surface_go.get_width()) // 2, SCREEN_HEIGHT // 2 + 0, screen, alpha=gameover_elements_alpha)

        # Update and draw buttons
        restart_button_go.update(current_mouse_pos, mouse_buttons_held)
        quit_button_go.update(current_mouse_pos, mouse_buttons_held)
        restart_button_go.draw(screen, alpha=gameover_elements_alpha) # Draw directly to screen
        quit_button_go.draw(screen, alpha=gameover_elements_alpha)     # Draw directly to screen


        if score > high_score:
            high_score = score
            with open("score.txt", "w") as file:
                file.write(str(high_score))
    
    elif paused: # Pause menu
        # Draw background and existing game elements behind the pause menu
        draw_bg(bg_scroll)
        platform_group.draw(screen)
        for enemy in enemy_group:
            enemy.draw(screen)
        for fireball in fireball_group:
            fireball.draw(screen)
        for diamond in diamond_group:
            diamond.draw(screen)
        player.draw()
        draw_score()
        left_button.draw(screen) # Draw game controls so they don't disappear on pause
        right_button.draw(screen)
        fire_button.draw(screen)


        # Darken the screen for the pause effect
        overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay_surface.fill((0, 0, 0, 180)) # Semi-transparent black
        screen.blit(overlay_surface, (0, 0))

        # Draw pause text and buttons
        pause_text = font_huge.render("PAUSED", True, WHITE)
        pause_text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 350))
        screen.blit(pause_text, pause_text_rect)

        pause_resume_button.update(current_mouse_pos, mouse_buttons_held)
        pause_quit_button.update(current_mouse_pos, mouse_buttons_held)
        pause_resume_button.draw(screen)
        pause_quit_button.draw(screen)


    pygame.display.update()
    clock.tick(FPS) # Ensure FPS is maintained even when game is not actively moving

pygame.quit()