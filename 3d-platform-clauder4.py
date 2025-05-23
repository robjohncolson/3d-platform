import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random
import json
import os

# Initialize pygame and OpenGL
pygame.init()
display_width, display_height = 800, 600
screen = pygame.display.set_mode((display_width, display_height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Enhanced 3D Platformer")

# OpenGL setup
glEnable(GL_DEPTH_TEST)
glMatrixMode(GL_PROJECTION)
gluPerspective(45, (display_width / display_height), 0.1, 50.0)
glMatrixMode(GL_MODELVIEW)
glClearColor(0.5, 0.8, 1.0, 1.0)

# Enable lighting
glEnable(GL_LIGHTING)
glEnable(GL_LIGHT0)
glEnable(GL_COLOR_MATERIAL)
glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

# Set up light
light_position = [5.0, 10.0, 5.0, 1.0]
light_ambient = [0.3, 0.3, 0.3, 1.0]
light_diffuse = [0.8, 0.8, 0.8, 1.0]

glLightfv(GL_LIGHT0, GL_POSITION, light_position)
glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)

# Colors
RED = (0.8, 0.2, 0.2)
GREEN = (0.2, 0.7, 0.2)
BLUE = (0.2, 0.2, 0.8)
YELLOW = (0.9, 0.8, 0.1)
WHITE = (0.9, 0.9, 0.9)
DARK_GREEN = (0.1, 0.4, 0.1)

# Simple and reliable sound system
class SoundManager:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.enabled = True
            
            # Create simple sound effects using basic sine waves
            self.jump_sound = self.create_simple_beep(440, 0.1)
            self.coin_sound = self.create_simple_beep(880, 0.15) 
            self.death_sound = self.create_simple_beep(220, 0.3)
            
            print("Sound system initialized")
        except Exception as e:
            self.enabled = False
            print(f"Sound disabled: {e}")
    
    def create_simple_beep(self, frequency, duration):
        if not self.enabled:
            return None
        try:
            import numpy as np
            
            sample_rate = 22050
            frames = int(duration * sample_rate)
            
            # Generate time array
            t = np.linspace(0, duration, frames)
            
            # Generate sine wave with fade out
            wave = np.sin(frequency * 2 * np.pi * t)
            fade = np.linspace(1, 0, frames)  # Fade out envelope
            wave = wave * fade * 0.3  # Volume control
            
            # Convert to 16-bit integers
            wave = (wave * 32767).astype(np.int16)
            
            # Make stereo
            stereo_wave = np.zeros((frames, 2), dtype=np.int16)
            stereo_wave[:, 0] = wave
            stereo_wave[:, 1] = wave
            
            sound = pygame.sndarray.make_sound(stereo_wave)
            return sound
            
        except ImportError:
            # Fallback if numpy not available - create very basic sound
            try:
                import array
                sample_rate = 22050
                frames = int(duration * sample_rate)
                
                arr = array.array('h')
                for i in range(frames):
                    t = i / sample_rate
                    fade = max(0, 1.0 - t/duration)
                    value = int(fade * 16383 * math.sin(frequency * 2 * math.pi * t))
                    arr.append(value)  # Left channel
                    arr.append(value)  # Right channel
                
                sound = pygame.sndarray.make_sound(arr)
                return sound
            except:
                return None
        except:
            return None
    
    def play_jump(self):
        if self.enabled and self.jump_sound:
            try:
                self.jump_sound.play()
                print("Jump sound played")
            except Exception as e:
                print(f"Jump sound failed: {e}")
    
    def play_coin(self):
        if self.enabled and self.coin_sound:
            try:
                self.coin_sound.play()
                print("Coin sound played")
            except Exception as e:
                print(f"Coin sound failed: {e}")
    
    def play_death(self):
        if self.enabled and self.death_sound:
            try:
                self.death_sound.play()
                print("Death sound played")
            except Exception as e:
                print(f"Death sound failed: {e}")

# Particle system
class Particle:
    def __init__(self, x, y, z, vel_x, vel_y, vel_z, color, life):
        self.x, self.y, self.z = x, y, z
        self.vel_x, self.vel_y, self.vel_z = vel_x, vel_y, vel_z
        self.color = color
        self.life = life
        self.max_life = life
    
    def update(self, dt):
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        self.z += self.vel_z * dt
        self.vel_y -= 0.5 * dt  # gravity
        self.life -= dt
        return self.life > 0
    
    def draw(self):
        alpha = self.life / self.max_life
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glColor4f(self.color[0], self.color[1], self.color[2], alpha)
        
        size = 0.03
        glBegin(GL_QUADS)
        glVertex3f(-size, -size, 0)
        glVertex3f(size, -size, 0)
        glVertex3f(size, size, 0)
        glVertex3f(-size, size, 0)
        glEnd()
        glPopMatrix()

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def emit(self, x, y, z, color, count=8):
        for _ in range(count):
            vel_x = (random.random() - 0.5) * 1.5
            vel_y = random.random() * 1.0 + 0.3
            vel_z = (random.random() - 0.5) * 1.5
            life = random.uniform(0.3, 0.8)
            self.particles.append(Particle(x, y, z, vel_x, vel_y, vel_z, color, life))
    
    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def draw(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_LIGHTING)
        for particle in self.particles:
            particle.draw()
        glEnable(GL_LIGHTING)
        glDisable(GL_BLEND)

# Save system
class SaveSystem:
    def __init__(self):
        self.save_file = "platformer_save.json"
        self.data = self.load_save()
    
    def load_save(self):
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"high_score": 0, "coins_collected": 0}
    
    def save_data(self):
        try:
            with open(self.save_file, 'w') as f:
                json.dump(self.data, f)
        except:
            pass
    
    def update_high_score(self, score):
        if score > self.data["high_score"]:
            self.data["high_score"] = score
            self.save_data()
            return True
        return False

def draw_cube(size, color):
    glColor3f(*color)
    
    vertices = [
        [size, size, -size], [size, -size, -size], [-size, -size, -size], [-size, size, -size],
        [size, size, size], [size, -size, size], [-size, -size, size], [-size, size, size]
    ]
    
    faces = [
        ([0, 1, 2, 3], [0, 0, -1]), ([4, 7, 6, 5], [0, 0, 1]),
        ([7, 3, 2, 6], [-1, 0, 0]), ([1, 0, 4, 5], [1, 0, 0]),
        ([0, 3, 7, 4], [0, 1, 0]), ([1, 5, 6, 2], [0, -1, 0])
    ]
    
    glBegin(GL_QUADS)
    for face_vertices, normal in faces:
        glNormal3f(*normal)
        for vertex_index in face_vertices:
            glVertex3f(*vertices[vertex_index])
    glEnd()
    
    # Wireframe outline
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(1.5)
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]
    glBegin(GL_LINES)
    for edge in edges:
        for vertex_index in edge:
            glVertex3f(*vertices[vertex_index])
    glEnd()

def draw_platform(x, y, z, width, height, depth, color=GREEN):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(width, height, depth)
    draw_cube(0.5, color)
    glPopMatrix()

def draw_coin(x, y, z, rotation):
    glPushMatrix()
    glTranslatef(x, y + math.sin(rotation * 0.1) * 0.1, z)
    glRotatef(rotation, 0, 1, 0)
    draw_cube(0.15, YELLOW)
    glPopMatrix()

class Player:
    def __init__(self):
        self.reset()
        self.size = 0.25
        # Enhanced movement
        self.acceleration = 0.006
        self.max_speed = 0.1
        self.friction = 0.88
        self.jump_velocity = 0.22
        self.gravity = 0.008
        # Coyote time
        self.coyote_time = 0.12
        self.coyote_timer = 0
        self.was_on_ground = False
        # Visual effects
        self.squash = 1.0
        # Jump buffering to prevent rapid jumps
        self.jump_buffer_time = 0.1
        self.jump_buffer_timer = 0
        
    def reset(self):
        self.x, self.y, self.z = 0.0, 1.0, 0.0
        self.vel_x = self.vel_y = self.vel_z = 0.0
        self.on_ground = False
        self.jump_buffer_timer = 0
        
    def update(self, platforms, dt, sound_manager, particles):
        self.was_on_ground = self.on_ground
        
        # Update coyote timer
        if self.coyote_timer > 0:
            self.coyote_timer -= dt
            
        # Update jump buffer timer
        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= dt
            
        # Apply gravity
        if not self.on_ground:
            self.vel_y -= self.gravity
            
        # Update position
        self.x += self.vel_x
        self.y += self.vel_y
        self.z += self.vel_z
        
        # Check collisions
        self.check_collisions(platforms, sound_manager, particles)
        
        # Coyote time
        if self.was_on_ground and not self.on_ground:
            self.coyote_timer = self.coyote_time
            
        # Apply friction
        self.vel_x *= self.friction
        self.vel_z *= self.friction
        
        # Limit speed
        speed = math.sqrt(self.vel_x**2 + self.vel_z**2)
        if speed > self.max_speed:
            self.vel_x = self.vel_x / speed * self.max_speed
            self.vel_z = self.vel_z / speed * self.max_speed
            
        # Visual squash effect
        if self.squash > 1.0:
            self.squash -= dt * 3
            if self.squash < 1.0:
                self.squash = 1.0
                
        # Reset if fallen
        if self.y < -10:
            self.reset()
            return True  # took damage
        return False
        
    def check_collisions(self, platforms, sound_manager, particles):
        self.on_ground = False
        
        for platform in platforms:
            px, py, pz, pw, ph, pd = platform[:6]
            
            # AABB collision
            if (abs(self.x - px) < pw/2 + self.size and
                abs(self.z - pz) < pd/2 + self.size and
                self.y - self.size <= py + ph/2 and
                self.y - self.size > py + ph/2 - 0.2 and
                self.vel_y <= 0):
                
                # Landing
                if not self.was_on_ground and self.vel_y < -0.05:
                    particles.emit(self.x, self.y - self.size, self.z, (0.7, 0.7, 0.7), 5)
                    self.squash = 1.3
                
                self.y = py + ph/2 + self.size
                self.vel_y = 0
                self.on_ground = True
                self.coyote_timer = 0
                break
        
    def move(self, direction):
        self.vel_x += direction[0] * self.acceleration
        self.vel_z += direction[1] * self.acceleration
        
    def jump(self, sound_manager, particles):
        # Only jump if buffer timer has expired (prevents rapid jumping when holding space)
        if self.jump_buffer_timer <= 0 and (self.on_ground or self.coyote_timer > 0):
            self.vel_y = self.jump_velocity
            self.on_ground = False
            self.coyote_timer = 0
            self.jump_buffer_timer = self.jump_buffer_time  # Reset buffer timer
            sound_manager.play_jump()
            particles.emit(self.x, self.y - self.size, self.z, (0.8, 0.8, 0.8), 4)
            
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        # Squash effect
        scale_y = 1.0 / self.squash
        scale_xz = self.squash
        glScalef(scale_xz, scale_y, scale_xz)
        
        draw_cube(self.size, RED)
        glPopMatrix()

class Game:
    def __init__(self):
        self.sound_manager = SoundManager()
        self.particles = ParticleSystem()
        self.save_system = SaveSystem()
        
        # Game state - simplified, no menu
        self.game_state = "playing"  # playing, paused, game_over, level_complete
        self.score = 0
        self.lives = 3
        self.level = 1
        
        # Objects
        self.player = Player()
        self.load_level(1)
        
        # Camera
        self.camera_x, self.camera_y, self.camera_z = 0, 3, 6
        
        # Timing
        self.clock = pygame.time.Clock()
        self.last_time = pygame.time.get_ticks()
        self.coin_rotation = 0
        
        print("Enhanced 3D Platformer")
        print("Game: WASD - Move, SPACE/SHIFT - Jump, ESC - Pause, R - Restart")
        print("Game Started! Use WASD to move, SPACE or SHIFT to jump")
        
    def load_level(self, level_num):
        self.level = level_num
        
        if level_num == 1:
            self.platforms = [
                [0, -0.5, 0, 4, 0.5, 4],      # Base
                [0, -0.2, -2, 1.5, 0.3, 1.5],
                [2, 0.2, -2, 1, 0.3, 1],
                [3, 0.6, 0, 1, 0.3, 1],
                [2, 1.0, 2, 1, 0.3, 1],
                [0, 1.4, 3, 1.5, 0.3, 1.5],
                [-2, 1.8, 2, 1, 0.3, 1],
            ]
            self.platform_colors = [DARK_GREEN] + [GREEN] * 6
            self.coins = [
                [0, 0.5, -2], [2, 0.9, -2], [3, 1.3, 0],
                [2, 1.7, 2], [0, 2.1, 3], [-2, 2.5, 2]
            ]
        elif level_num == 2:
            self.platforms = [
                [0, -0.5, 0, 4, 0.5, 4],
                [1, -0.2, -3, 1, 0.2, 1],
                [3, 0.1, -2, 1, 0.2, 1],
                [4, 0.5, 0, 1, 0.2, 1],
                [3, 0.9, 2, 1, 0.2, 1],
                [1, 1.3, 3, 1, 0.2, 1],
                [-1, 1.7, 3, 1, 0.2, 1],
                [-3, 2.1, 2, 1, 0.2, 1],
                [-4, 2.5, 0, 1, 0.2, 1],
                [-3, 2.9, -2, 1, 0.2, 1],
                [-1, 3.3, -3, 2, 0.2, 2],
            ]
            self.platform_colors = [DARK_GREEN] + [BLUE] * 10
            self.coins = [
                [1, 0.5, -3], [3, 0.8, -2], [4, 1.2, 0], [3, 1.6, 2],
                [1, 2.0, 3], [-1, 2.4, 3], [-3, 2.8, 2], [-4, 3.2, 0],
                [-3, 3.6, -2], [-1, 4.0, -3]
            ]
        
        self.player.reset()
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == "playing":
                        self.game_state = "paused"
                    elif self.game_state == "paused":
                        self.game_state = "playing"
                elif event.key == pygame.K_r and self.game_state == "playing":
                    self.restart_level()
        
        # Movement and jump - all handled with continuous key checking
        if self.game_state == "playing":
            keys = pygame.key.get_pressed()
            move_dir = [0, 0]
            
            # Debug key detection
            pressed_keys = []
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                move_dir[1] -= 1
                pressed_keys.append("W/UP")
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                move_dir[1] += 1
                pressed_keys.append("S/DOWN")
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                move_dir[0] -= 1
                pressed_keys.append("A/LEFT")
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                move_dir[0] += 1
                pressed_keys.append("D/RIGHT")
            
            # Handle jump with multiple detection methods to work around keyboard ghosting
            space_pressed = (keys[pygame.K_SPACE] or 
                           keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])  # Alternative: shift also jumps
            
            if space_pressed:
                pressed_keys.append("JUMP")
                self.player.jump(self.sound_manager, self.particles)
            
            if move_dir[0] != 0 or move_dir[1] != 0:
                length = math.sqrt(move_dir[0]**2 + move_dir[1]**2)
                move_dir[0] /= length
                move_dir[1] /= length
                self.player.move(move_dir)
        
        return True
    
    def update(self, dt):
        if self.game_state == "playing":
            # Update player
            took_damage = self.player.update(self.platforms, dt, self.sound_manager, self.particles)
            
            if took_damage:
                self.lives -= 1
                self.sound_manager.play_death()
                print(f"Life lost! Lives remaining: {self.lives}")
                if self.lives <= 0:
                    print(f"Game Over! Final Score: {self.score}")
                    if self.save_system.update_high_score(self.score):
                        print(f"New high score: {self.score}!")
                    # Auto-restart instead of showing menu
                    self.restart_game()
            
            # Update particles
            self.particles.update(dt)
            
            # Update coin rotation
            self.coin_rotation += 120 * dt
            
            # Check coin collection
            for coin in self.coins[:]:
                coin_x, coin_y, coin_z = coin
                distance = math.sqrt((self.player.x - coin_x)**2 + 
                                   (self.player.y - coin_y)**2 + 
                                   (self.player.z - coin_z)**2)
                if distance < 0.4:
                    self.coins.remove(coin)
                    self.score += 100
                    self.sound_manager.play_coin()
                    self.particles.emit(coin_x, coin_y, coin_z, YELLOW, 12)
                    print(f"Coin collected! Score: {self.score}")
            
            # Check level completion
            if len(self.coins) == 0:
                level_bonus = 500 * self.level
                self.score += level_bonus
                print(f"Level {self.level} Complete! Bonus: {level_bonus}")
                # Auto-advance to next level
                self.next_level()
            
            # Update camera
            self.update_camera()
    
    def update_camera(self):
        # Smooth camera follow
        target_x = self.player.x + 4
        target_y = self.player.y + 3
        target_z = self.player.z + 5
        
        self.camera_x += (target_x - self.camera_x) * 0.08
        self.camera_y += (target_y - self.camera_y) * 0.08
        self.camera_z += (target_z - self.camera_z) * 0.08
    
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        if self.game_state in ["playing", "paused"]:
            self.render_game()
            if self.game_state == "paused":
                self.render_pause()
        elif self.game_state == "level_complete":
            self.render_game()  # Show game while transitioning
        
        pygame.display.flip()
    
    def render_game(self):
        # Set camera
        gluLookAt(
            self.camera_x, self.camera_y, self.camera_z,
            self.player.x, self.player.y, self.player.z,
            0, 1, 0
        )
        
        # Draw platforms
        for i, platform in enumerate(self.platforms):
            draw_platform(*platform, self.platform_colors[i])
        
        # Draw coins
        for coin in self.coins:
            draw_coin(coin[0], coin[1], coin[2], self.coin_rotation)
        
        # Draw player
        self.player.draw()
        
        # Draw shadow
        draw_shadow(self.player.x, self.player.y, self.player.z, self.platforms, self.player.on_ground)
        
        # Draw particles
        self.particles.draw()
        
        # Draw HUD
        self.render_hud()
    
    def render_hud(self):
        # Switch to 2D
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, display_width, 0, display_height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # Score bar (white)
        glColor3f(1, 1, 1)
        score_width = min(200, self.score // 10)
        glBegin(GL_QUADS)
        glVertex2f(10, display_height - 40)
        glVertex2f(10 + score_width, display_height - 40)
        glVertex2f(10 + score_width, display_height - 30)
        glVertex2f(10, display_height - 30)
        glEnd()
        
        # Lives (red squares)
        glColor3f(1, 0, 0)
        for i in range(self.lives):
            x = 230 + i * 25
            glBegin(GL_QUADS)
            glVertex2f(x, display_height - 40)
            glVertex2f(x + 20, display_height - 40)
            glVertex2f(x + 20, display_height - 20)
            glVertex2f(x, display_height - 20)
            glEnd()
        
        # Coins remaining (yellow circles)
        glColor3f(1, 1, 0)
        for i in range(min(len(self.coins), 10)):
            x = 350 + i * 15
            glBegin(GL_POLYGON)
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                glVertex2f(x + 6 + 5 * math.cos(rad), display_height - 30 + 5 * math.sin(rad))
            glEnd()
        
        # Level indicator (blue bar)
        glColor3f(0, 0, 1)
        glBegin(GL_QUADS)
        glVertex2f(display_width - 80, display_height - 40)
        glVertex2f(display_width - 80 + self.level * 30, display_height - 40)
        glVertex2f(display_width - 80 + self.level * 30, display_height - 30)
        glVertex2f(display_width - 80, display_height - 30)
        glEnd()
        
        # Restore 3D
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    def render_pause(self):
        # Pause overlay
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, display_width, 0, display_height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # Semi-transparent overlay
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0, 0, 0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(display_width, 0)
        glVertex2f(display_width, display_height)
        glVertex2f(0, display_height)
        glEnd()
        glDisable(GL_BLEND)
        
        # Pause text
        glColor3f(1, 1, 1)
        for i in range(6):
            x = display_width//2 - 60 + i * 20
            glBegin(GL_QUADS)
            glVertex2f(x, display_height//2)
            glVertex2f(x + 15, display_height//2)
            glVertex2f(x + 15, display_height//2 + 30)
            glVertex2f(x, display_height//2 + 30)
            glEnd()
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    def restart_game(self):
        self.game_state = "playing"
        self.score = 0
        self.lives = 3
        self.level = 1
        self.load_level(1)
        print("Game Started! Use WASD to move, SPACE or SHIFT to jump")
        print(f"Current state: {self.game_state}")
        print(f"Platforms: {len(self.platforms)}")
        print(f"Coins: {len(self.coins)}")
        print(f"Player position: {self.player.x}, {self.player.y}, {self.player.z}")
    
    def restart_level(self):
        self.load_level(self.level)
        print(f"Level {self.level} restarted")
    
    def next_level(self):
        if self.level < 2:
            self.level += 1
            self.load_level(self.level)
            self.game_state = "playing"
            print(f"Starting Level {self.level}")
        else:
            print("Congratulations! You completed all levels!")
            self.game_state = "playing"
            self.save_system.update_high_score(self.score)
    
    def run(self):
        running = True
        
        while running:
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_time) / 1000.0
            self.last_time = current_time
            dt = min(dt, 1/30.0)  # Cap delta time
            
            running = self.handle_events()
            self.update(dt)
            self.render()
            
            self.clock.tick(60)
        
        pygame.quit()

def draw_shadow(player_x, player_y, player_z, platforms, player_on_ground, shadow_size=0.3):
    # Only draw shadow when player is in the air
    if player_on_ground:
        return
    
    # Find the highest platform below the player
    ground_y = -10  # Default very low ground
    for platform in platforms:
        px, py, pz, pw, ph, pd = platform[:6]
        
        # Check if player is above this platform (within x,z bounds)
        if (abs(player_x - px) < pw/2 + 0.5 and 
            abs(player_z - pz) < pd/2 + 0.5 and 
            py + ph/2 < player_y):  # Platform is below player
            
            # This platform is below the player, update ground level
            ground_y = max(ground_y, py + ph/2)
    
    # Calculate shadow opacity based on height above ground
    height_above_ground = player_y - ground_y
    if height_above_ground < 0.1:  # Too close to ground
        return
        
    max_height = 3.0
    opacity = max(0.3, min(0.8, 1.0 - (height_above_ground / max_height)))
    
    # Calculate shadow size based on height (higher = larger shadow)
    shadow_scale = min(1.5, 1.0 + height_above_ground * 0.2)
    actual_shadow_size = shadow_size * shadow_scale
    
    glPushMatrix()
    glTranslatef(player_x, ground_y + 0.01, player_z)  # Slightly above the ground/platform
    
    # Disable lighting for shadow
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Dark gray shadow with opacity
    glColor4f(0.1, 0.1, 0.1, opacity)
    
    # Draw shadow as a simple circle made of triangles
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0)  # Center
    segments = 12
    for i in range(segments + 1):
        angle = (i / segments) * 2 * math.pi
        x = actual_shadow_size * math.cos(angle)
        z = actual_shadow_size * math.sin(angle)
        glVertex3f(x, 0, z)
    glEnd()
    
    # Re-enable lighting and disable blend
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)
    glPopMatrix()

# Run the game
if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Error: {e}")
        pygame.quit()