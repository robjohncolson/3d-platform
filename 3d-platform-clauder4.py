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
        
        # Initialize joystick support
        pygame.joystick.init()
        self.joystick = None
        self.setup_controller()
        
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
        
        # Camera rotation (added for right stick control)
        self.camera_yaw = 0.0      # Horizontal rotation (left/right)
        self.camera_pitch = -20.0  # Vertical rotation (up/down) - start slightly looking down
        self.camera_distance = 6.0 # Distance from player
        self.camera_sensitivity = 100.0  # How fast camera rotates
        
        # Timing
        self.clock = pygame.time.Clock()
        self.last_time = pygame.time.get_ticks()
        self.coin_rotation = 0
        
        print("Enhanced 3D Platformer")
        print("Game: WASD - Move, SPACE/SHIFT - Jump, ESC - Pause, R - Restart")
        print("Controller: Left stick/D-pad - Move, Right stick - Camera, A/B/X/Y - Jump, Start - Pause")
        print("Custom Levels: 6-0 - Load custom level from slots 1-5")
        print("Info: C - Show controller details, V - Reset camera")
        print("Game Started! Use WASD to move, SPACE or SHIFT to jump")
        
    def setup_controller(self):
        """Initialize and detect game controller"""
        try:
            # Quit any existing joystick first
            if self.joystick:
                try:
                    self.joystick.quit()
                except:
                    pass
                self.joystick = None
            
            joystick_count = pygame.joystick.get_count()
            if joystick_count > 0:
                # Try to find the best controller (prefer 8bitdo)
                best_controller = 0
                for i in range(joystick_count):
                    temp_joy = pygame.joystick.Joystick(i)
                    controller_name = temp_joy.get_name().lower()
                    
                    # Prefer 8bitdo controllers
                    if "8bitdo" in controller_name or "ultimate" in controller_name:
                        best_controller = i
                        break
                
                self.joystick = pygame.joystick.Joystick(best_controller)
                self.joystick.init()
                controller_name = self.joystick.get_name()
                
                print(f"🎮 Controller detected: {controller_name}")
                print(f"   Buttons: {self.joystick.get_numbuttons()}")
                print(f"   Axes: {self.joystick.get_numaxes()}")
                print(f"   Hats: {self.joystick.get_numhats()}")
                
                # Controller-specific optimizations
                controller_name_lower = controller_name.lower()
                if "8bitdo" in controller_name_lower:
                    if "ultimate" in controller_name_lower:
                        print("✓ 8bitdo Ultimate series detected! Full feature support enabled.")
                        print("  • Switch modes with the controller if needed (X+Start for X-input)")
                    else:
                        print("✓ 8bitdo controller detected! Basic support enabled.")
                elif "xbox" in controller_name_lower:
                    print("✓ Xbox controller detected! Compatible mode enabled.")
                elif "playstation" in controller_name_lower or "ps" in controller_name_lower:
                    print("✓ PlayStation controller detected! Compatible mode enabled.")
                else:
                    print("✓ Generic controller detected! Basic support enabled.")
                
                print("  • Press C key anytime to view detailed controller info")
                
                return True
                
            else:
                print("No controller detected. Keyboard controls available.")
                print("🎮 To use a controller:")
                print("  1. Connect your 8bitdo Ultimate 2")
                print("  2. Make sure it's in the right mode (try X+Start for X-input)")
                print("  3. Restart the game or press C to check status")
                return False
                
        except Exception as e:
            print(f"Controller setup failed: {e}")
            self.joystick = None
            return False
    
    def load_level(self, level_num):
        self.level = level_num
        
        # Try to load custom level first
        if self.load_custom_level(level_num):
            return
        
        # Fall back to built-in levels
        if level_num == 1:
            # Tutorial level - simple jumps
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
            # Precision jumping
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
        elif level_num == 3:
            # Spiral tower
            self.platforms = [
                [0, -0.5, 0, 3, 0.5, 3],      # Base
                [2, 0.0, 0, 1, 0.2, 1],       # Start spiral
                [2, 0.4, -2, 1, 0.2, 1],
                [0, 0.8, -3, 1, 0.2, 1],
                [-2, 1.2, -2, 1, 0.2, 1],
                [-3, 1.6, 0, 1, 0.2, 1],
                [-2, 2.0, 2, 1, 0.2, 1],
                [0, 2.4, 3, 1, 0.2, 1],
                [2, 2.8, 2, 1, 0.2, 1],
                [3, 3.2, 0, 1, 0.2, 1],
                [2, 3.6, -1, 1, 0.2, 1],
                [0, 4.0, -2, 2, 0.2, 2],     # Top platform
            ]
            self.platform_colors = [DARK_GREEN] + [RED] * 11
            self.coins = [
                [2, 0.7, 0], [2, 1.1, -2], [0, 1.5, -3], [-2, 1.9, -2],
                [-3, 2.3, 0], [-2, 2.7, 2], [0, 3.1, 3], [2, 3.5, 2],
                [3, 3.9, 0], [2, 4.3, -1], [0, 4.7, -2]
            ]
        elif level_num == 4:
            # Long jumps and gaps
            self.platforms = [
                [0, -0.5, 0, 2, 0.5, 2],      # Start
                [4, 0.0, 0, 1.5, 0.3, 1.5],   # Long jump
                [8, 0.3, -1, 1, 0.3, 1],
                [6, 0.8, -4, 1, 0.3, 1],
                [2, 1.2, -5, 1, 0.3, 1],
                [-2, 1.6, -4, 1, 0.3, 1],
                [-5, 2.0, -1, 1, 0.3, 1],
                [-7, 2.4, 2, 1, 0.3, 1],
                [-4, 2.8, 5, 1, 0.3, 1],
                [0, 3.2, 6, 1, 0.3, 1],
                [4, 3.6, 4, 1, 0.3, 1],
                [7, 4.0, 1, 1.5, 0.3, 1.5],
            ]
            self.platform_colors = [DARK_GREEN] + [YELLOW] * 11
            self.coins = [
                [4, 0.7, 0], [8, 1.0, -1], [6, 1.5, -4], [2, 1.9, -5],
                [-2, 2.3, -4], [-5, 2.7, -1], [-7, 3.1, 2], [-4, 3.5, 5],
                [0, 3.9, 6], [4, 4.3, 4], [7, 4.7, 1]
            ]
        elif level_num == 5:
            # Moving maze (static for now, but complex layout)
            self.platforms = [
                [0, -0.5, 0, 2, 0.5, 2],      # Start
                [3, 0.0, 0, 1, 0.2, 3],       # Wall
                [1, 0.4, 3, 3, 0.2, 1],
                [-1, 0.8, 5, 1, 0.2, 1],
                [-4, 1.2, 4, 1, 0.2, 3],
                [-6, 1.6, 1, 3, 0.2, 1],
                [-4, 2.0, -1, 1, 0.2, 1],
                [-1, 2.4, -2, 1, 0.2, 3],
                [2, 2.8, -1, 1, 0.2, 1],
                [5, 3.2, 0, 1, 0.2, 3],
                [3, 3.6, 3, 3, 0.2, 1],
                [0, 4.0, 5, 1, 0.2, 1],
                [-3, 4.4, 3, 1, 0.2, 1],
                [-5, 4.8, 0, 1, 0.2, 1],
                [-2, 5.2, -2, 3, 0.2, 1],    # Final platform
            ]
            self.platform_colors = [DARK_GREEN] + [WHITE] * 14
            self.coins = [
                [3, 0.7, 1], [1, 1.1, 3], [-1, 1.5, 5], [-4, 1.9, 3],
                [-6, 2.3, 1], [-4, 2.7, -1], [-1, 3.1, -1], [2, 3.5, -1],
                [5, 3.9, 1], [3, 4.3, 3], [0, 4.7, 5], [-3, 5.1, 3],
                [-5, 5.5, 0], [-2, 5.9, -2]
            ]
        
        self.player.reset()
        
    def load_custom_level(self, level_num):
        """Try to load a custom level from JSON file. Returns True if successful."""
        filename = f"my_level_{level_num}.json"
        
        try:
            if not os.path.exists(filename):
                return False
                
            with open(filename, 'r') as f:
                level_data = json.load(f)
            
            # Load platforms
            self.platforms = level_data.get("platforms", [])
            
            # Load platform colors
            platform_colors_data = level_data.get("platform_colors", [])
            self.platform_colors = []
            
            for color_data in platform_colors_data:
                # Convert from 0-1 range to RGB tuple
                if len(color_data) >= 3:
                    color = (color_data[0], color_data[1], color_data[2])
                    self.platform_colors.append(color)
                else:
                    self.platform_colors.append(GREEN)  # Default color
            
            # Load coins
            self.coins = level_data.get("coins", [])
            
            print(f"✓ Loaded custom level {level_num}: {len(self.platforms)} platforms, {len(self.coins)} coins")
            return True
            
        except Exception as e:
            print(f"Failed to load custom level {level_num}: {e}")
            return False

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
                elif event.key == pygame.K_c:
                    # Display controller information
                    self.display_controller_info()
                elif event.key == pygame.K_v:
                    # Reset camera to default position
                    self.camera_yaw = 0.0
                    self.camera_pitch = -20.0
                    print("Camera reset to default position")
                # Custom level loading
                elif self.game_state == "playing":
                    if event.key == pygame.K_6:
                        self.load_level(1)  # Slot 1
                        print("Loading custom level from slot 1...")
                    elif event.key == pygame.K_7:
                        self.load_level(2)  # Slot 2  
                        print("Loading custom level from slot 2...")
                    elif event.key == pygame.K_8:
                        self.load_level(3)  # Slot 3
                        print("Loading custom level from slot 3...")
                    elif event.key == pygame.K_9:
                        self.load_level(4)  # Slot 4
                        print("Loading custom level from slot 4...")
                    elif event.key == pygame.K_0:
                        self.load_level(5)  # Slot 5
                        print("Loading custom level from slot 5...")
            
            # Controller events
            elif event.type == pygame.JOYBUTTONDOWN:
                if self.joystick and event.joy == 0:
                    # 8bitdo Ultimate 2 button mapping:
                    # Button 0: A (South), Button 1: B (East)
                    # Button 2: X (West), Button 3: Y (North)
                    # Button 9: Start/Menu, Button 8: Back/Select
                    
                    if self.game_state == "playing":
                        # Jump buttons - A, B, X, Y (any face button)
                        if event.button in [0, 1, 2, 3]:
                            self.player.jump(self.sound_manager, self.particles)
                            print(f"Controller jump! Button {event.button}")
                        
                        # Start button for pause
                        elif event.button == 9:  # Start
                            self.game_state = "paused"
                            print("Game paused (controller)")
                            
                        # Back/Select button for restart
                        elif event.button == 8:  # Back/Select
                            self.restart_level()
                            print("Level restarted (controller)")
                            
                        # Shoulder buttons for level switching (L1/R1)
                        elif event.button == 6:  # L1/LB - previous level
                            if self.level > 1:
                                self.load_level(self.level - 1)
                                print(f"Switched to level {self.level}")
                        elif event.button == 7:  # R1/RB - next level  
                            if self.level < 5:
                                self.load_level(self.level + 1)
                                print(f"Switched to level {self.level}")
                    
                    elif self.game_state == "paused":
                        # Start button to unpause
                        if event.button == 9:  # Start
                            self.game_state = "playing"
                            print("Game unpaused (controller)")
            
            # Controller connected/disconnected
            elif event.type == pygame.JOYDEVICEADDED:
                print(f"🎮 Controller connected!")
                self.setup_controller()
            elif event.type == pygame.JOYDEVICEREMOVED:
                print("🎮 Controller disconnected!")
                self.joystick = None
        
        # Movement and jump - continuous input checking for both keyboard and controller
        if self.game_state == "playing":
            # Keyboard input
            keys = pygame.key.get_pressed()
            move_dir = [0, 0]
            
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                move_dir[1] -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                move_dir[1] += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                move_dir[0] -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                move_dir[0] += 1
            
            # Controller input
            if self.joystick:
                try:
                    # Left analog stick input (movement)
                    if self.joystick.get_numaxes() >= 2:
                        stick_x = self.joystick.get_axis(0)  # Left stick X
                        stick_y = self.joystick.get_axis(1)  # Left stick Y
                        
                        # Apply deadzone
                        deadzone = 0.15
                        if abs(stick_x) > deadzone:
                            move_dir[0] += stick_x
                        if abs(stick_y) > deadzone:
                            move_dir[1] += stick_y
                    
                    # D-pad input (movement)
                    if self.joystick.get_numhats() >= 1:
                        hat_x, hat_y = self.joystick.get_hat(0)
                        move_dir[0] += hat_x
                        move_dir[1] -= hat_y  # Invert Y for intuitive movement
                    
                    # Face buttons for jumping (continuous check for held buttons)
                    if (self.joystick.get_button(0) or  # A
                        self.joystick.get_button(1) or  # B  
                        self.joystick.get_button(2) or  # X
                        self.joystick.get_button(3)):   # Y
                        self.player.jump(self.sound_manager, self.particles)
                        
                except Exception as e:
                    print(f"Controller input error: {e}")
            
            # Keyboard jump input
            space_pressed = (keys[pygame.K_SPACE] or 
                           keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
            
            if space_pressed:
                self.player.jump(self.sound_manager, self.particles)
            
            # Normalize movement direction
            if move_dir[0] != 0 or move_dir[1] != 0:
                length = math.sqrt(move_dir[0]**2 + move_dir[1]**2)
                move_dir[0] /= length
                move_dir[1] /= length
                self.player.move(move_dir)
        
        return True
    
    def update(self, dt):
        if self.game_state == "playing":
            # Handle right stick camera input (moved here where dt is available)
            if self.joystick:
                try:
                    if self.joystick.get_numaxes() >= 4:
                        right_stick_x = self.joystick.get_axis(2)  # Right stick X
                        right_stick_y = self.joystick.get_axis(3)  # Right stick Y
                        
                        # Apply deadzone and sensitivity
                        camera_deadzone = 0.1
                        if abs(right_stick_x) > camera_deadzone:
                            self.camera_yaw += right_stick_x * self.camera_sensitivity * dt
                            print(f"Camera yaw: {self.camera_yaw:.1f}° (stick: {right_stick_x:.2f})")
                        if abs(right_stick_y) > camera_deadzone:
                            self.camera_pitch += right_stick_y * self.camera_sensitivity * dt
                            print(f"Camera pitch: {self.camera_pitch:.1f}° (stick: {right_stick_y:.2f})")
                        
                        # Clamp pitch to prevent camera flipping
                        self.camera_pitch = max(-80.0, min(80.0, self.camera_pitch))
                        
                except Exception as e:
                    print(f"Camera input error: {e}")
            
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
        # Debug output
        print(f"Camera angles - Yaw: {self.camera_yaw:.1f}°, Pitch: {self.camera_pitch:.1f}°")
        
        # Calculate camera position based on rotation angles
        # Convert degrees to radians
        yaw_rad = math.radians(self.camera_yaw)
        pitch_rad = math.radians(self.camera_pitch)
        
        # Calculate camera position relative to player
        # Use spherical coordinates: distance * cos(pitch) for horizontal plane
        horizontal_distance = self.camera_distance * math.cos(pitch_rad)
        
        camera_offset_x = horizontal_distance * math.sin(yaw_rad)
        camera_offset_z = horizontal_distance * math.cos(yaw_rad)
        camera_offset_y = self.camera_distance * math.sin(pitch_rad)
        
        # Position camera relative to player
        target_camera_x = self.player.x + camera_offset_x
        target_camera_y = self.player.y + camera_offset_y + 2.0  # Offset up from player center
        target_camera_z = self.player.z + camera_offset_z
        
        # Debug output
        print(f"Target camera pos: ({target_camera_x:.1f}, {target_camera_y:.1f}, {target_camera_z:.1f})")
        
        # Smooth camera movement (optional - can be made instant for more responsive feel)
        smooth_factor = 0.15
        self.camera_x += (target_camera_x - self.camera_x) * smooth_factor
        self.camera_y += (target_camera_y - self.camera_y) * smooth_factor
        self.camera_z += (target_camera_z - self.camera_z) * smooth_factor
        
        print(f"Actual camera pos: ({self.camera_x:.1f}, {self.camera_y:.1f}, {self.camera_z:.1f})")
    
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
    
    def display_controller_info(self):
        """Display detailed controller information for debugging"""
        if not self.joystick:
            print("No controller connected.")
            return
            
        try:
            print(f"\n🎮 Controller Info:")
            print(f"   Name: {self.joystick.get_name()}")
            print(f"   ID: {self.joystick.get_instance_id()}")
            print(f"   Buttons: {self.joystick.get_numbuttons()}")
            print(f"   Axes: {self.joystick.get_numaxes()}")
            print(f"   Hats: {self.joystick.get_numhats()}")
            
            print(f"\n🎮 8bitdo Ultimate 2 Controls:")
            print(f"   Left Stick/D-pad: Move character")
            print(f"   Right Stick: Control camera angle")
            print(f"   A/B/X/Y buttons: Jump")
            print(f"   Start button: Pause/Unpause")
            print(f"   Back/Select: Restart level")
            print(f"   L1/LB: Previous level")
            print(f"   R1/RB: Next level")
            
            # Show current input state
            if self.joystick.get_numaxes() >= 2:
                stick_x = self.joystick.get_axis(0)
                stick_y = self.joystick.get_axis(1)
                print(f"   Left stick: X={stick_x:.2f}, Y={stick_y:.2f}")
            
            if self.joystick.get_numaxes() >= 4:
                right_stick_x = self.joystick.get_axis(2)
                right_stick_y = self.joystick.get_axis(3)
                print(f"   Right stick: X={right_stick_x:.2f}, Y={right_stick_y:.2f}")
            
            if self.joystick.get_numhats() >= 1:
                hat_x, hat_y = self.joystick.get_hat(0)
                print(f"   D-pad: X={hat_x}, Y={hat_y}")
            
            # Show current camera state
            print(f"\n📷 Camera Info:")
            print(f"   Yaw: {self.camera_yaw:.1f}°")
            print(f"   Pitch: {self.camera_pitch:.1f}°")
            print(f"   Distance: {self.camera_distance:.1f}")
            print(f"   Position: ({self.camera_x:.1f}, {self.camera_y:.1f}, {self.camera_z:.1f})")
            
        except Exception as e:
            print(f"Error reading controller info: {e}")

    def restart_game(self):
        self.game_state = "playing"
        self.score = 0
        self.lives = 3
        self.level = 1
        
        # Reinitialize controller if needed
        if not self.joystick:
            self.setup_controller()
            
        self.load_level(1)
        print("Game Started! Use WASD to move, SPACE or SHIFT to jump")
        if self.joystick:
            print("🎮 Controller ready! Use left stick/D-pad to move, face buttons to jump")
        print(f"Current state: {self.game_state}")
        print(f"Platforms: {len(self.platforms)}")
        print(f"Coins: {len(self.coins)}")
        print(f"Player position: {self.player.x}, {self.player.y}, {self.player.z}")
    
    def restart_level(self):
        self.load_level(self.level)
        print(f"Level {self.level} restarted")
    
    def next_level(self):
        if self.level < 5:
            self.level += 1
            self.load_level(self.level)
            self.game_state = "playing"
            print(f"Starting Level {self.level}")
        else:
            print("🎉 CONGRATULATIONS! You completed ALL 5 levels! 🎉")
            print(f"Final Score: {self.score}")
            self.save_system.update_high_score(self.score)
            # Restart from level 1 for replay
            self.level = 1
            self.load_level(1)
            self.game_state = "playing"
            print("Restarting from Level 1...")
    
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