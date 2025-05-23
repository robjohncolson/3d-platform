import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import json
import os
import time

# Initialize pygame and OpenGL
pygame.init()
display_width, display_height = 1200, 800
screen = pygame.display.set_mode((display_width, display_height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("3D Platformer Level Editor")

# OpenGL setup
glEnable(GL_DEPTH_TEST)
glMatrixMode(GL_PROJECTION)
gluPerspective(45, (display_width / display_height), 0.1, 100.0)
glMatrixMode(GL_MODELVIEW)
glClearColor(0.3, 0.5, 0.8, 1.0)

# Enable lighting
glEnable(GL_LIGHTING)
glEnable(GL_LIGHT0)
glEnable(GL_COLOR_MATERIAL)
glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

# Set up light
light_position = [10.0, 15.0, 10.0, 1.0]
light_ambient = [0.4, 0.4, 0.4, 1.0]
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
PURPLE = (0.7, 0.2, 0.7)
ORANGE = (0.9, 0.5, 0.1)
CYAN = (0.2, 0.8, 0.8)

PLATFORM_COLORS = [GREEN, DARK_GREEN, BLUE, RED, WHITE, YELLOW, PURPLE, ORANGE, CYAN]
COLOR_NAMES = ["Green", "Dark Green", "Blue", "Red", "White", "Yellow", "Purple", "Orange", "Cyan"]

def draw_cube(size, color, selected=False, wireframe=False):
    if not wireframe:
        glColor3f(*color)
    else:
        glColor3f(1.0, 1.0, 1.0)
    
    vertices = [
        [size, size, -size], [size, -size, -size], [-size, -size, -size], [-size, size, -size],
        [size, size, size], [size, -size, size], [-size, -size, size], [-size, size, size]
    ]
    
    faces = [
        ([0, 1, 2, 3], [0, 0, -1]), ([4, 7, 6, 5], [0, 0, 1]),
        ([7, 3, 2, 6], [-1, 0, 0]), ([1, 0, 4, 5], [1, 0, 0]),
        ([0, 3, 7, 4], [0, 1, 0]), ([1, 5, 6, 2], [0, -1, 0])
    ]
    
    if not wireframe:
        glBegin(GL_QUADS)
        for face_vertices, normal in faces:
            glNormal3f(*normal)
            for vertex_index in face_vertices:
                glVertex3f(*vertices[vertex_index])
        glEnd()
    
    # Draw wireframe
    if selected:
        glColor3f(1.0, 1.0, 0.0)  # Yellow for selected
        glLineWidth(3.0)
    else:
        glColor3f(0.0, 0.0, 0.0)  # Black for normal
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

def draw_platform(x, y, z, width, height, depth, color, selected=False):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(width, height, depth)
    draw_cube(0.5, color, selected)
    glPopMatrix()

def draw_coin(x, y, z, selected=False):
    glPushMatrix()
    glTranslatef(x, y, z)
    if selected:
        glColor3f(1.0, 1.0, 0.0)  # Yellow when selected
        draw_cube(0.2, YELLOW, True)
    else:
        glColor3f(*YELLOW)
        draw_cube(0.15, YELLOW)
    glPopMatrix()

def draw_grid(size=20, spacing=1.0):
    glDisable(GL_LIGHTING)
    glColor3f(0.5, 0.5, 0.5)
    glLineWidth(1.0)
    
    glBegin(GL_LINES)
    for i in range(-size, size + 1):
        # X lines
        glVertex3f(-size * spacing, 0, i * spacing)
        glVertex3f(size * spacing, 0, i * spacing)
        # Z lines
        glVertex3f(i * spacing, 0, -size * spacing)
        glVertex3f(i * spacing, 0, size * spacing)
    glEnd()
    
    # Draw axes
    glLineWidth(3.0)
    glBegin(GL_LINES)
    # X axis - red
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(0, 0, 0)
    glVertex3f(5, 0, 0)
    # Y axis - green
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 5, 0)
    # Z axis - blue
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, 5)
    glEnd()
    
    glEnable(GL_LIGHTING)

class Camera:
    def __init__(self):
        self.x, self.y, self.z = 0, 5, 10
        self.pitch = -20  # Looking down slightly
        self.yaw = 0
        self.speed = 0.1
        self.mouse_sensitivity = 0.2
        
    def update(self, keys, mouse_rel, dt):
        # WASD movement
        forward = [math.sin(math.radians(self.yaw)), 0, -math.cos(math.radians(self.yaw))]
        right = [math.cos(math.radians(self.yaw)), 0, math.sin(math.radians(self.yaw))]
        
        if keys[pygame.K_w]:
            self.x += forward[0] * self.speed
            self.z += forward[2] * self.speed
        if keys[pygame.K_s]:
            self.x -= forward[0] * self.speed
            self.z -= forward[2] * self.speed
        if keys[pygame.K_a]:
            self.x -= right[0] * self.speed
            self.z -= right[2] * self.speed
        if keys[pygame.K_d]:
            self.x += right[0] * self.speed
            self.z += right[2] * self.speed
        if keys[pygame.K_q]:
            self.y += self.speed
        if keys[pygame.K_e]:
            self.y -= self.speed
            
        # Mouse look
        if mouse_rel[0] != 0 or mouse_rel[1] != 0:
            self.yaw += mouse_rel[0] * self.mouse_sensitivity
            self.pitch -= mouse_rel[1] * self.mouse_sensitivity
            self.pitch = max(-90, min(90, self.pitch))
    
    def apply(self):
        glLoadIdentity()
        glRotatef(self.pitch, 1, 0, 0)
        glRotatef(self.yaw, 0, 1, 0)
        glTranslatef(-self.x, -self.y, -self.z)

def unproject_mouse(mouse_x, mouse_y):
    """Convert mouse coordinates to 3D world ray"""
    # Get current matrices
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    
    # Convert mouse coordinates (flip Y)
    win_x = mouse_x
    win_y = viewport[3] - mouse_y
    
    # Unproject to get world coordinates
    try:
        near_point = gluUnProject(win_x, win_y, 0.0, modelview, projection, viewport)
        far_point = gluUnProject(win_x, win_y, 1.0, modelview, projection, viewport)
        
        # Calculate ray direction
        ray_dir = [far_point[i] - near_point[i] for i in range(3)]
        length = math.sqrt(sum(d*d for d in ray_dir))
        ray_dir = [d/length for d in ray_dir]
        
        return near_point, ray_dir
    except:
        return None, None

def ray_box_intersect(ray_start, ray_dir, box_center, box_size):
    """Check if ray intersects with box"""
    # Convert to box local coordinates
    box_min = [box_center[i] - box_size[i]/2 for i in range(3)]
    box_max = [box_center[i] + box_size[i]/2 for i in range(3)]
    
    t_min = float('-inf')
    t_max = float('inf')
    
    for i in range(3):
        if abs(ray_dir[i]) < 1e-8:  # Ray parallel to slab
            if ray_start[i] < box_min[i] or ray_start[i] > box_max[i]:
                return False, 0
        else:
            # Compute intersection t values
            t1 = (box_min[i] - ray_start[i]) / ray_dir[i]
            t2 = (box_max[i] - ray_start[i]) / ray_dir[i]
            
            if t1 > t2:
                t1, t2 = t2, t1
                
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
            
            if t_min > t_max:
                return False, 0
    
    return t_min >= 0, t_min

class LevelEditor:
    def __init__(self):
        self.camera = Camera()
        self.platforms = []  # [x, y, z, width, height, depth, color_index]
        self.coins = []      # [x, y, z]
        
        self.selected_platform = None
        self.selected_coin = None
        self.mode = "platform"  # "platform" or "coin"
        self.color_index = 0
        
        # Editing state
        self.dragging = False
        self.drag_start_pos = None
        self.drag_offset = [0, 0, 0]
        
        # Grid snapping
        self.snap_to_grid = True
        self.grid_size = 0.5
        
        # Mouse capture
        self.mouse_captured = False
        pygame.mouse.set_visible(True)
        
        # File handling - no more input() calls!
        self.current_level_name = "my_level"
        self.save_slot = 1
        
        print("3D Level Editor Controls:")
        print("Camera: WASD - Move, Q/E - Up/Down, Right-click+drag - Look around")
        print("F1 - Platform mode, F2 - Coin mode")
        print("Left Click - Select/Place object")
        print("Delete - Remove selected object")
        print("Arrow Keys - Move selected object, PageUp/PageDown - Move up/down")
        print("Shift+Arrow Keys - Resize selected platform")
        print("C - Change platform color")
        print("G - Toggle grid snap")
        print("S - Quick save (saves as 'my_level_1.json')")
        print("L - Quick load, 1-5 - Load save slot 1-5")
        print("R - Reset level")
        print("ESC - Exit editor")
        
    def snap_to_grid_pos(self, pos):
        if self.snap_to_grid:
            return [round(pos[i] / self.grid_size) * self.grid_size for i in range(3)]
        return pos
    
    def handle_events(self):
        mouse_rel = [0, 0]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_F1:
                    self.mode = "platform"
                    print("Platform mode")
                elif event.key == pygame.K_F2:
                    self.mode = "coin"
                    print("Coin mode")
                elif event.key == pygame.K_DELETE:
                    self.delete_selected()
                elif event.key == pygame.K_c:
                    self.change_color()
                elif event.key == pygame.K_g:
                    self.snap_to_grid = not self.snap_to_grid
                    print(f"Grid snap: {'ON' if self.snap_to_grid else 'OFF'}")
                elif event.key == pygame.K_s:
                    self.quick_save()
                elif event.key == pygame.K_l:
                    self.quick_load()
                elif event.key == pygame.K_r:
                    self.reset_level()
                # Number keys for save slots
                elif event.key >= pygame.K_1 and event.key <= pygame.K_5:
                    self.save_slot = event.key - pygame.K_1 + 1
                    self.quick_load()
                # Movement keys for selected objects
                elif event.key == pygame.K_UP:
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        self.resize_selected([0, 0, -0.5])
                    else:
                        self.move_selected([0, 0, -0.5])
                elif event.key == pygame.K_DOWN:
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        self.resize_selected([0, 0, 0.5])
                    else:
                        self.move_selected([0, 0, 0.5])
                elif event.key == pygame.K_LEFT:
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        self.resize_selected([-0.5, 0, 0])
                    else:
                        self.move_selected([-0.5, 0, 0])
                elif event.key == pygame.K_RIGHT:
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        self.resize_selected([0.5, 0, 0])
                    else:
                        self.move_selected([0.5, 0, 0])
                elif event.key == pygame.K_PAGEUP:
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        self.resize_selected([0, 0.5, 0])
                    else:
                        self.move_selected([0, 0.5, 0])
                elif event.key == pygame.K_PAGEDOWN:
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        self.resize_selected([0, -0.5, 0])
                    else:
                        self.move_selected([0, -0.5, 0])
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_left_click(event.pos)
                elif event.button == 3:  # Right click
                    self.mouse_captured = True
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:  # Right click release
                    self.mouse_captured = False
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_captured:
                    mouse_rel = event.rel
        
        return True, mouse_rel
    
    def handle_left_click(self, mouse_pos):
        ray_start, ray_dir = unproject_mouse(mouse_pos[0], mouse_pos[1])
        if not ray_start or not ray_dir:
            return
            
        # Check for object selection
        closest_dist = float('inf')
        closest_platform = None
        closest_coin = None
        
        # Check platforms
        for i, platform in enumerate(self.platforms):
            x, y, z, w, h, d = platform[:6]
            hit, dist = ray_box_intersect(ray_start, ray_dir, [x, y, z], [w, h, d])
            if hit and dist < closest_dist:
                closest_dist = dist
                closest_platform = i
                closest_coin = None
                
        # Check coins
        for i, coin in enumerate(self.coins):
            x, y, z = coin
            hit, dist = ray_box_intersect(ray_start, ray_dir, [x, y, z], [0.3, 0.3, 0.3])
            if hit and dist < closest_dist:
                closest_dist = dist
                closest_coin = i
                closest_platform = None
        
        # Select object or place new one
        if closest_platform is not None:
            self.selected_platform = closest_platform
            self.selected_coin = None
            print(f"Selected platform {closest_platform}")
        elif closest_coin is not None:
            self.selected_coin = closest_coin
            self.selected_platform = None
            print(f"Selected coin {closest_coin}")
        else:
            # Place new object
            self.place_object(ray_start, ray_dir)
    
    def place_object(self, ray_start, ray_dir):
        # Cast ray to y=0 plane for placement
        if abs(ray_dir[1]) > 1e-8:
            t = -ray_start[1] / ray_dir[1]
            if t > 0:
                hit_point = [ray_start[i] + t * ray_dir[i] for i in range(3)]
                hit_point = self.snap_to_grid_pos(hit_point)
                
                if self.mode == "platform":
                    # Place platform at ground level
                    self.platforms.append([hit_point[0], hit_point[1] + 0.25, hit_point[2], 
                                         1.0, 0.5, 1.0, self.color_index])
                    self.selected_platform = len(self.platforms) - 1
                    self.selected_coin = None
                    print(f"Placed platform at {hit_point}")
                elif self.mode == "coin":
                    # Place coin slightly above ground
                    self.coins.append([hit_point[0], hit_point[1] + 0.5, hit_point[2]])
                    self.selected_coin = len(self.coins) - 1
                    self.selected_platform = None
                    print(f"Placed coin at {hit_point}")
    
    def delete_selected(self):
        if self.selected_platform is not None:
            del self.platforms[self.selected_platform]
            self.selected_platform = None
            print("Deleted platform")
        elif self.selected_coin is not None:
            del self.coins[self.selected_coin]
            self.selected_coin = None
            print("Deleted coin")
    
    def change_color(self):
        if self.selected_platform is not None:
            self.platforms[self.selected_platform][6] = (self.platforms[self.selected_platform][6] + 1) % len(PLATFORM_COLORS)
            print(f"Changed platform color to {COLOR_NAMES[self.platforms[self.selected_platform][6]]}")
        else:
            self.color_index = (self.color_index + 1) % len(PLATFORM_COLORS)
            print(f"Next platform color: {COLOR_NAMES[self.color_index]}")
    
    def move_selected(self, delta):
        if self.selected_platform is not None:
            for i in range(3):
                self.platforms[self.selected_platform][i] += delta[i]
            if self.snap_to_grid:
                pos = self.snap_to_grid_pos(self.platforms[self.selected_platform][:3])
                for i in range(3):
                    self.platforms[self.selected_platform][i] = pos[i]
        elif self.selected_coin is not None:
            for i in range(3):
                self.coins[self.selected_coin][i] += delta[i]
            if self.snap_to_grid:
                pos = self.snap_to_grid_pos(self.coins[self.selected_coin])
                for i in range(3):
                    self.coins[self.selected_coin][i] = pos[i]
    
    def resize_selected(self, delta):
        if self.selected_platform is not None:
            # Resize platform (only width, height, depth - indices 3, 4, 5)
            for i in range(3):
                self.platforms[self.selected_platform][3 + i] = max(0.1, self.platforms[self.selected_platform][3 + i] + delta[i])
    
    def quick_save(self):
        filename = f"{self.current_level_name}_{self.save_slot}.json"
        
        # Convert to game format
        platforms_data = []
        platform_colors = []
        
        for platform in self.platforms:
            platforms_data.append(platform[:6])  # x, y, z, w, h, d
            platform_colors.append(PLATFORM_COLORS[platform[6]])
        
        level_data = {
            "platforms": platforms_data,
            "platform_colors": platform_colors,
            "coins": self.coins
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(level_data, f, indent=2)
            print(f"Level saved as {filename}")
        except Exception as e:
            print(f"Error saving: {e}")
    
    def quick_load(self):
        filename = f"{self.current_level_name}_{self.save_slot}.json"
        
        try:
            with open(filename, 'r') as f:
                level_data = json.load(f)
            
            # Convert from game format
            self.platforms = []
            self.coins = level_data.get("coins", [])
            
            platforms_data = level_data.get("platforms", [])
            platform_colors = level_data.get("platform_colors", [])
            
            for i, platform in enumerate(platforms_data):
                color_index = 0
                if i < len(platform_colors):
                    # Find matching color index
                    color = platform_colors[i]
                    for j, pc in enumerate(PLATFORM_COLORS):
                        if abs(pc[0] - color[0]) < 0.1 and abs(pc[1] - color[1]) < 0.1 and abs(pc[2] - color[2]) < 0.1:
                            color_index = j
                            break
                
                self.platforms.append(platform + [color_index])
            
            self.selected_platform = None
            self.selected_coin = None
            print(f"Level loaded from {filename}")
            
        except FileNotFoundError:
            print(f"No save file found: {filename}")
        except Exception as e:
            print(f"Error loading: {e}")
    
    def reset_level(self):
        self.platforms = []
        self.coins = []
        self.selected_platform = None
        self.selected_coin = None
        print("Level reset")
    
    def update(self, dt):
        keys = pygame.key.get_pressed()
        running, mouse_rel = self.handle_events()
        
        if not running:
            return False
            
        self.camera.update(keys, mouse_rel, dt)
        return True
    
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.camera.apply()
        
        # Draw grid
        draw_grid()
        
        # Draw platforms
        for i, platform in enumerate(self.platforms):
            x, y, z, w, h, d, color_idx = platform
            color = PLATFORM_COLORS[color_idx]
            selected = (i == self.selected_platform)
            draw_platform(x, y, z, w, h, d, color, selected)
        
        # Draw coins
        for i, coin in enumerate(self.coins):
            x, y, z = coin
            selected = (i == self.selected_coin)
            draw_coin(x, y, z, selected)
        
        # Draw UI
        self.render_ui()
        
        pygame.display.flip()
    
    def render_ui(self):
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
        
        # Background panel
        glColor4f(0, 0, 0, 0.7)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBegin(GL_QUADS)
        glVertex2f(10, display_height - 200)
        glVertex2f(350, display_height - 200)
        glVertex2f(350, display_height - 10)
        glVertex2f(10, display_height - 10)
        glEnd()
        glDisable(GL_BLEND)
        
        # Mode indicator
        y = display_height - 30
        
        # Mode (simple text representation)
        mode_color = [1, 0, 0] if self.mode == "platform" else [1, 1, 0]
        glColor3f(*mode_color)
        glBegin(GL_QUADS)
        glVertex2f(20, y - 15)
        glVertex2f(80, y - 15)
        glVertex2f(80, y)
        glVertex2f(20, y)
        glEnd()
        
        # Current color indicator
        if self.mode == "platform":
            color = PLATFORM_COLORS[self.color_index]
            glColor3f(*color)
            glBegin(GL_QUADS)
            glVertex2f(90, y - 15)
            glVertex2f(120, y - 15)
            glVertex2f(120, y)
            glVertex2f(90, y)
            glEnd()
        
        # Save slot indicator
        glColor3f(0.8, 0.8, 0.8)
        for i in range(5):
            x = 140 + i * 20
            if i + 1 == self.save_slot:
                glColor3f(1, 1, 1)  # Bright for current slot
            else:
                glColor3f(0.4, 0.4, 0.4)  # Dark for other slots
            glBegin(GL_QUADS)
            glVertex2f(x, y - 15)
            glVertex2f(x + 15, y - 15)
            glVertex2f(x + 15, y)
            glVertex2f(x, y)
            glEnd()
        
        # Object count
        platform_count = len(self.platforms)
        coin_count = len(self.coins)
        
        # Draw platform counter
        for i in range(min(platform_count, 20)):
            x = 20 + i * 12
            glColor3f(0, 1, 0)
            glBegin(GL_QUADS)
            glVertex2f(x, y - 40)
            glVertex2f(x + 8, y - 40)
            glVertex2f(x + 8, y - 30)
            glVertex2f(x, y - 30)
            glEnd()
        
        # Draw coin counter
        for i in range(min(coin_count, 20)):
            x = 20 + i * 12
            glColor3f(1, 1, 0)
            glBegin(GL_QUADS)
            glVertex2f(x, y - 60)
            glVertex2f(x + 8, y - 60)
            glVertex2f(x + 8, y - 50)
            glVertex2f(x, y - 50)
            glEnd()
        
        # Grid snap indicator
        glColor3f(0, 1, 1) if self.snap_to_grid else glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_QUADS)
        glVertex2f(20, y - 80)
        glVertex2f(50, y - 80)
        glVertex2f(50, y - 70)
        glVertex2f(20, y - 70)
        glEnd()
        
        # Selection info
        if self.selected_platform is not None:
            platform = self.platforms[self.selected_platform]
            glColor3f(1, 1, 0)
            # Draw platform selection indicator
            glBegin(GL_QUADS)
            glVertex2f(260, y - 40)
            glVertex2f(340, y - 40)
            glVertex2f(340, y - 30)
            glVertex2f(260, y - 30)
            glEnd()
        elif self.selected_coin is not None:
            glColor3f(1, 1, 0)
            # Draw coin selection indicator
            glBegin(GL_QUADS)
            glVertex2f(260, y - 60)
            glVertex2f(340, y - 60)
            glVertex2f(340, y - 50)
            glVertex2f(260, y - 50)
            glEnd()
        
        # Restore 3D
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    def run(self):
        clock = pygame.time.Clock()
        last_time = pygame.time.get_ticks()
        
        running = True
        while running:
            current_time = pygame.time.get_ticks()
            dt = (current_time - last_time) / 1000.0
            last_time = current_time
            dt = min(dt, 1/30.0)  # Cap delta time
            
            running = self.update(dt)
            self.render()
            clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    try:
        editor = LevelEditor()
        editor.run()
    except Exception as e:
        print(f"Error: {e}")
        pygame.quit() 