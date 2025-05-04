import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math
import random

# Initialize pygame and OpenGL
pygame.init()
display_width, display_height = 800, 600
pygame.display.set_mode((display_width, display_height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("3D Platformer - Raspberry Pi")

# Set up the OpenGL environment
glViewport(0, 0, display_width, display_height)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(45, (display_width / display_height), 0.1, 50.0)
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()
glTranslatef(0, 0, -5)
glEnable(GL_DEPTH_TEST)

# Game colors
BLUE = (0.0, 0.0, 1.0)
RED = (1.0, 0.0, 0.0)
GREEN = (0.0, 1.0, 0.0)
YELLOW = (1.0, 1.0, 0.0)
PURPLE = (1.0, 0.0, 1.0)
CYAN = (0.0, 1.0, 1.0)
WHITE = (1.0, 1.0, 1.0)

# Game state
class GameState:
    def __init__(self):
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.level = 1
        
game_state = GameState()

# Camera/Player class
class Player:
    def __init__(self):
        self.position = [0.0, 0.0, 0.0]
        self.velocity = [0.0, 0.0, 0.0]
        self.on_ground = False
        self.jump_velocity = 0.15
        self.gravity = 0.01
        self.movement_speed = 0.05
        self.size = 0.25
        self.color = RED
        self.collected_coins = 0
        
    def update(self, platforms, coins):
        # Apply gravity
        if not self.on_ground:
            self.velocity[1] -= self.gravity
            
        # Update position based on velocity
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.position[2] += self.velocity[2]
        
        # Check for platform collisions
        self.on_ground = False
        for platform in platforms:
            if self.check_platform_collision(platform):
                self.on_ground = True
                # Place player on top of platform
                self.position[1] = platform.position[1] + platform.height/2 + self.size
                self.velocity[1] = 0
                break
                
        # Check if player fell off
        if self.position[1] < -5:
            self.position = [0.0, 0.0, 0.0]
            self.velocity = [0.0, 0.0, 0.0]
            game_state.lives -= 1
            if game_state.lives <= 0:
                game_state.game_over = True
                
        # Check for coin collisions
        for coin in coins[:]:
            if self.check_coin_collision(coin):
                coins.remove(coin)
                game_state.score += 10
                self.collected_coins += 1
                
        # Apply friction/resistance
        self.velocity[0] *= 0.9
        self.velocity[2] *= 0.9
        
        # Limit horizontal speed
        max_speed = 0.2
        speed = math.sqrt(self.velocity[0]**2 + self.velocity[2]**2)
        if speed > max_speed:
            self.velocity[0] = self.velocity[0] / speed * max_speed
            self.velocity[2] = self.velocity[2] / speed * max_speed
            
    def jump(self):
        if self.on_ground:
            self.velocity[1] = self.jump_velocity
            self.on_ground = False
            
    def move(self, direction):
        # Direction is a normalized vector [x, z]
        self.velocity[0] += direction[0] * self.movement_speed
        self.velocity[2] += direction[1] * self.movement_speed
        
    def draw(self):
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])
        glColor3f(*self.color)
        self.draw_cube(self.size)
        glPopMatrix()
        
    def draw_cube(self, size):
        vertices = [
            [size, size, -size], [size, -size, -size], [-size, -size, -size], [-size, size, -size],
            [size, size, size], [size, -size, size], [-size, -size, size], [-size, size, size]
        ]
        
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        
        faces = [
            (0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 7, 3),
            (1, 5, 6, 2), (2, 6, 7, 3), (0, 4, 5, 1)
        ]
        
        glBegin(GL_QUADS)
        for face in faces:
            for vertex in face:
                glVertex3f(*vertices[vertex])
        glEnd()
        
    def check_platform_collision(self, platform):
        # Simple AABB collision detection
        px, py, pz = self.position
        half_size = self.size
        
        px_min, px_max = px - half_size, px + half_size
        py_min, py_max = py - half_size, py + half_size
        pz_min, pz_max = pz - half_size, pz + half_size
        
        plat_x, plat_y, plat_z = platform.position
        plat_w, plat_h, plat_d = platform.width, platform.height, platform.depth
        
        plat_x_min, plat_x_max = plat_x - plat_w/2, plat_x + plat_w/2
        plat_y_min, plat_y_max = plat_y - plat_h/2, plat_y + plat_h/2
        plat_z_min, plat_z_max = plat_z - plat_d/2, plat_z + plat_d/2
        
        x_collision = px_max > plat_x_min and px_min < plat_x_max
        z_collision = pz_max > plat_z_min and pz_min < plat_z_max
        y_close = py_min <= plat_y_max and py_min > plat_y_min
        
        return x_collision and z_collision and y_close
        
    def check_coin_collision(self, coin):
        # Distance-based collision with the coin
        distance = math.sqrt(
            (self.position[0] - coin.position[0])**2 +
            (self.position[1] - coin.position[1])**2 +
            (self.position[2] - coin.position[2])**2
        )
        return distance < (self.size + coin.size)

# Platform class
class Platform:
    def __init__(self, position, width, height, depth, color=GREEN):
        self.position = position  # [x, y, z]
        self.width = width
        self.height = height
        self.depth = depth
        self.color = color
        
    def draw(self):
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])
        glColor3f(*self.color)
        self.draw_cube(self.width, self.height, self.depth)
        glPopMatrix()
        
    def draw_cube(self, width, height, depth):
        w, h, d = width/2, height/2, depth/2
        vertices = [
            [w, h, -d], [w, -h, -d], [-w, -h, -d], [-w, h, -d],
            [w, h, d], [w, -h, d], [-w, -h, d], [-w, h, d]
        ]
        
        faces = [
            (0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 7, 3),
            (1, 5, 6, 2), (2, 6, 7, 3), (0, 4, 5, 1)
        ]
        
        glBegin(GL_QUADS)
        for face in faces:
            for vertex in face:
                glVertex3f(*vertices[vertex])
        glEnd()

# Coin class
class Coin:
    def __init__(self, position, size=0.15, color=YELLOW):
        self.position = position
        self.size = size
        self.color = color
        self.rotation = 0
        
    def update(self):
        self.rotation += 2
        if self.rotation >= 360:
            self.rotation = 0
            
    def draw(self):
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])
        glRotatef(self.rotation, 0, 1, 0)
        glColor3f(*self.color)
        self.draw_coin()
        glPopMatrix()
        
    def draw_coin(self):
        # Simplified coin as octagon
        glBegin(GL_POLYGON)
        num_segments = 8
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            x = self.size * math.cos(angle)
            y = self.size * math.sin(angle)
            glVertex3f(x, y, 0)
        glEnd()
        
        # Draw other side
        glBegin(GL_POLYGON)
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            x = self.size * math.cos(angle)
            y = self.size * math.sin(angle)
            glVertex3f(x, y, -0.02)
        glEnd()
        
        # Draw edge
        glBegin(GL_QUAD_STRIP)
        for i in range(num_segments + 1):
            angle = 2 * math.pi * i / num_segments
            x = self.size * math.cos(angle)
            y = self.size * math.sin(angle)
            glVertex3f(x, y, 0)
            glVertex3f(x, y, -0.02)
        glEnd()

# Create game objects
player = Player()

# Create level
def create_level(level_num):
    platforms = []
    coins = []
    
    # Base platform
    platforms.append(Platform([0, -0.5, 0], 5, 0.5, 5, GREEN))
    
    if level_num == 1:
        # Level 1 platforms
        platforms.extend([
            Platform([0, -0.5, -2], 1, 0.5, 1, BLUE),
            Platform([2, 0, -2], 1, 0.5, 1, BLUE),
            Platform([4, 0.5, 0], 1, 0.5, 1, BLUE),
            Platform([2, 1, 2], 1, 0.5, 1, BLUE),
            Platform([0, 1.5, 3], 1, 0.5, 1, BLUE),
            Platform([-2, 2, 2], 1, 0.5, 1, PURPLE)
        ])
        
        # Level 1 coins
        coins.extend([
            Coin([0, 0.2, -2]),
            Coin([2, 0.7, -2]),
            Coin([4, 1.2, 0]),
            Coin([2, 1.7, 2]),
            Coin([0, 2.2, 3]),
            Coin([-2, 2.7, 2])
        ])
    elif level_num == 2:
        # Level 2 platforms - more complex
        platforms.extend([
            Platform([1, -0.3, -3], 1, 0.3, 1, CYAN),
            Platform([3, 0, -1], 1, 0.3, 1, CYAN),
            Platform([3, 0.3, 2], 1, 0.3, 1, CYAN),
            Platform([1, 0.6, 3], 1, 0.3, 1, CYAN),
            Platform([-1, 0.9, 3], 1, 0.3, 1, CYAN),
            Platform([-3, 1.2, 1], 1, 0.3, 1, CYAN),
            Platform([-3, 1.5, -1], 1, 0.3, 1, CYAN),
            Platform([-1, 1.8, -3], 1, 0.3, 1, CYAN),
            Platform([0, 2.1, 0], 1, 0.3, 1, PURPLE)
        ])
        
        # Level 2 coins
        for platform in platforms[1:]:
            coins.append(Coin([
                platform.position[0], 
                platform.position[1] + platform.height/2 + 0.3, 
                platform.position[2]
            ]))
            
    return platforms, coins

platforms, coins = create_level(game_state.level)

# Game loop
clock = pygame.time.Clock()
running = True

font = pygame.font.SysFont(None, 36)

# Camera variables
camera_angle = 0  # for a rotating camera view
camera_distance = 7
camera_height = 3

def draw_text(text, position, color=(255, 255, 255)):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=position)
    screen = pygame.display.get_surface()
    screen.blit(surface, rect)

last_time = pygame.time.get_ticks()
while running:
    current_time = pygame.time.get_ticks()
    dt = (current_time - last_time) / 1000.0  # Delta time in seconds
    last_time = current_time
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                player.jump()
                
    # Handle continuous key presses
    keys = pygame.key.get_pressed()
    move_dir = [0, 0]  # x, z direction
    
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        move_dir[1] -= 1
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        move_dir[1] += 1
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        move_dir[0] -= 1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        move_dir[0] += 1
        
    # Normalize direction vector if needed
    length = math.sqrt(move_dir[0]**2 + move_dir[1]**2)
    if length > 0:
        move_dir[0] /= length
        move_dir[1] /= length
        player.move(move_dir)
    
    # Update game objects
    player.update(platforms, coins)
    for coin in coins:
        coin.update()
        
    # Check for level completion
    if player.collected_coins >= 5 and game_state.level == 1:
        game_state.level = 2
        player.position = [0.0, 0.0, 0.0]
        player.velocity = [0.0, 0.0, 0.0]
        player.collected_coins = 0
        platforms, coins = create_level(game_state.level)
        
    # Clear screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Set up camera (3rd person view)
    camera_angle += 0.1 * dt  # Slow rotation for visual effect
    cam_x = player.position[0] + camera_distance * math.sin(camera_angle)
    cam_z = player.position[2] + camera_distance * math.cos(camera_angle)
    cam_y = player.position[1] + camera_height
    
    gluLookAt(
        cam_x, cam_y, cam_z,  # Camera position
        player.position[0], player.position[1], player.position[2],  # Look at point
        0, 1, 0  # Up vector
    )
    
    # Draw game objects
    for platform in platforms:
        platform.draw()
        
    for coin in coins:
        coin.draw()
        
    player.draw()
    
    # Draw 2D text overlay
    pygame.display.flip()
    
    screen_surface = pygame.display.get_surface()
    glDisable(GL_DEPTH_TEST)
    score_text = f"Score: {game_state.score}  Lives: {game_state.lives}  Level: {game_state.level}"
    draw_text(score_text, (display_width // 2, 30))
    glEnable(GL_DEPTH_TEST)
    
    # Check game over
    if game_state.game_over:
        print("Game Over!")
        game_state.game_over = False
        game_state.lives = 3
        game_state.score = 0
        game_state.level = 1
        player.position = [0.0, 0.0, 0.0]
        player.velocity = [0.0, 0.0, 0.0]
        player.collected_coins = 0
        platforms, coins = create_level(game_state.level)
    
    # Cap the frame rate
    clock.tick(60)
    
pygame.quit()