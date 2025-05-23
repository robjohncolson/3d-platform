import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import json
import os

# Initialize pygame and OpenGL
pygame.init()
display_width, display_height = 1200, 800
screen = pygame.display.set_mode((display_width, display_height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("3D Platformer Level Editor - FIXED")

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

def draw_cube(size, color, selected=False):
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
        draw_cube(0.2, YELLOW, True)
    else:
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
        self.x, self.y, self.z = 0, 8, 15  # Move camera higher and farther back
        self.pitch = -30  # Look down more to see the grid
        self.yaw = 0
        self.speed = 0.15
        self.sprint_multiplier = 3.0
        self.mouse_sensitivity = 0.2
        
    def update(self, keys, mouse_rel, dt):
        current_speed = self.speed
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            current_speed *= self.sprint_multiplier
        
        # WASD movement
        forward = [math.sin(math.radians(self.yaw)), 0, -math.cos(math.radians(self.yaw))]
        right = [math.cos(math.radians(self.yaw)), 0, math.sin(math.radians(self.yaw))]
        
        if keys[pygame.K_w]:
            self.x += forward[0] * current_speed
            self.z += forward[2] * current_speed
        if keys[pygame.K_s]:
            self.x -= forward[0] * current_speed
            self.z -= forward[2] * current_speed
        if keys[pygame.K_a]:
            self.x -= right[0] * current_speed
            self.z -= right[2] * current_speed
        if keys[pygame.K_d]:
            self.x += right[0] * current_speed
            self.z += right[2] * current_speed
        if keys[pygame.K_e]:
            self.y += current_speed
        if keys[pygame.K_q]:
            self.y -= current_speed
            
        # Mouse look
        if mouse_rel[0] != 0 or mouse_rel[1] != 0:
            self.yaw += mouse_rel[0] * self.mouse_sensitivity
            self.pitch -= mouse_rel[1] * self.mouse_sensitivity
            self.pitch = max(-89.9, min(89.9, self.pitch))
    
    def apply(self):
        glLoadIdentity()
        glRotatef(self.pitch, 1, 0, 0)
        glRotatef(self.yaw, 0, 1, 0)
        glTranslatef(-self.x, -self.y, -self.z)

def unproject_mouse(mouse_x, mouse_y):
    """Convert mouse coordinates to 3D world ray"""
    try:
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        
        win_x = float(mouse_x)
        win_y = float(viewport[3] - mouse_y)
        
        near_point = gluUnProject(win_x, win_y, 0.0, modelview, projection, viewport)
        far_point = gluUnProject(win_x, win_y, 1.0, modelview, projection, viewport)
        
        ray_dir = [far_point[i] - near_point[i] for i in range(3)]
        length = math.sqrt(sum(d*d for d in ray_dir))
        if length == 0:
            return near_point, [0, 0, -1]
        ray_dir = [d/length for d in ray_dir]
        
        return near_point, ray_dir
    except Exception as e:
        print(f"Error in unproject_mouse: {e}")
        return None, None

def ray_box_intersect(ray_start, ray_dir, box_center, box_dims):
    """Check if ray intersects with an AABB box"""
    box_min = [box_center[i] - box_dims[i]/2 for i in range(3)]
    box_max = [box_center[i] + box_dims[i]/2 for i in range(3)]
    
    t_min = float('-inf')
    t_max = float('inf')
    
    for i in range(3):
        if abs(ray_dir[i]) < 1e-8:
            if ray_start[i] < box_min[i] or ray_start[i] > box_max[i]:
                return False, 0
        else:
            t1 = (box_min[i] - ray_start[i]) / ray_dir[i]
            t2 = (box_max[i] - ray_start[i]) / ray_dir[i]
            
            if t1 > t2:
                t1, t2 = t2, t1
                
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
            
            if t_min > t_max:
                return False, 0
    
    if t_max < 0:
        return False, 0
    
    if t_min >= 0:
        return True, t_min
    else:
        return True, 0

class LevelEditor:
    def __init__(self):
        self.camera = Camera()
        self.platforms = []
        self.coins = []
        
        self.selected_platform = None
        self.selected_coin = None
        self.mode = "platform"
        self.color_index = 0
        
        self.snap_to_grid = True
        self.grid_size = 0.5
        
        self.mouse_captured = False
        pygame.mouse.set_visible(True)
        
        self.current_level_name = "my_level"
        self.save_slot = 1
        
        # Initialize font for text rendering
        try:
            self.font = pygame.font.SysFont("arial", 16)
        except:
            try:
                self.font = pygame.font.Font(None, 16)
            except:
                self.font = None
                print("Warning: Could not initialize font")
        
        print("=== 3D Level Editor - FIXED VERSION ===")
        print("Camera: WASD - Move, E - Up, Q - Down, SHIFT - Sprint")
        print("Mouse: Right-click + drag - Look around")
        print("F1 - Platform mode, F2 - Coin mode")
        print("Left Click - Select/Place object")
        print("Delete - Remove selected object")
        print("Arrow Keys - Move selected object")
        print("Shift+Arrow Keys - Resize selected platform")
        print("C - Change platform color")
        print("G - Toggle grid snap")
        print("S - Quick save, L - Quick load")
        print("1-5 - Select save slot")
        print("R - Reset level, ESC - Exit")
        print("==========================================")
        
        # Create a default platform so there's something to see
        self.platforms = [[0, 0.25, 0, 2, 0.5, 2, 0]]  # Default platform
        
    def snap_to_grid_pos(self, pos):
        if self.snap_to_grid:
            return [round(p / self.grid_size) * self.grid_size for p in pos]
        return pos
    
    def handle_events(self):
        mouse_rel = [0, 0]
        
        # Ensure we process all events
        pygame.event.pump()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, mouse_rel
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False, mouse_rel
                elif event.key == pygame.K_F1:
                    self.mode = "platform"
                    self.selected_coin = None
                    print(">>> Platform mode")
                elif event.key == pygame.K_F2:
                    self.mode = "coin"
                    self.selected_platform = None
                    print(">>> Coin mode")
                elif event.key == pygame.K_DELETE:
                    self.delete_selected()
                elif event.key == pygame.K_c:
                    self.change_color()
                elif event.key == pygame.K_g:
                    self.snap_to_grid = not self.snap_to_grid
                    print(f">>> Grid snap: {'ON' if self.snap_to_grid else 'OFF'}")
                elif event.key == pygame.K_s:
                    self.quick_save()
                elif event.key == pygame.K_l:
                    self.quick_load()
                elif event.key == pygame.K_r:
                    self.reset_level()
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    self.save_slot = event.key - pygame.K_0
                    print(f">>> Selected slot {self.save_slot}")
                    self.quick_load()
                
                # Movement keys
                elif event.key == pygame.K_UP:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.resize_selected([0, 0, -0.5])
                    else:
                        self.move_selected([0, 0, -0.5])
                elif event.key == pygame.K_DOWN:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.resize_selected([0, 0, 0.5])
                    else:
                        self.move_selected([0, 0, 0.5])
                elif event.key == pygame.K_LEFT:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.resize_selected([-0.5, 0, 0])
                    else:
                        self.move_selected([-0.5, 0, 0])
                elif event.key == pygame.K_RIGHT:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.resize_selected([0.5, 0, 0])
                    else:
                        self.move_selected([0.5, 0, 0])
                elif event.key == pygame.K_PAGEUP:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.resize_selected([0, 0.5, 0])
                    else:
                        self.move_selected([0, 0.5, 0])
                elif event.key == pygame.K_PAGEDOWN:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
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
                    pygame.mouse.get_rel()  # Reset relative motion
                    
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
            
        closest_dist = float('inf')
        new_selected_platform = None
        new_selected_coin = None
        
        # Check platforms
        for i, platform_data in enumerate(self.platforms):
            x, y, z, w, h, d = platform_data[:6]
            hit, dist = ray_box_intersect(ray_start, ray_dir, [x, y, z], [w, h, d])
            if hit and dist < closest_dist:
                closest_dist = dist
                new_selected_platform = i
                new_selected_coin = None
                
        # Check coins
        for i, coin_data in enumerate(self.coins):
            x, y, z = coin_data
            hit, dist = ray_box_intersect(ray_start, ray_dir, [x, y, z], [0.3, 0.3, 0.3])
            if hit and dist < closest_dist:
                closest_dist = dist
                new_selected_coin = i
                new_selected_platform = None
        
        # Update selection
        self.selected_platform = new_selected_platform
        self.selected_coin = new_selected_coin
        
        if self.selected_platform is not None:
            print(f">>> Selected platform {self.selected_platform}")
        elif self.selected_coin is not None:
            print(f">>> Selected coin {self.selected_coin}")
        else:
            # Place new object
            self.place_object(ray_start, ray_dir)
    
    def place_object(self, ray_start, ray_dir):
        # Cast ray to y=0 plane for placement
        if abs(ray_dir[1]) > 1e-5:
            t = -ray_start[1] / ray_dir[1]
            if t > 0:
                hit_point = [ray_start[i] + t * ray_dir[i] for i in range(3)]
            else:
                # Fallback: place object fixed distance in front of camera
                hit_point = [ray_start[i] + 10.0 * ray_dir[i] for i in range(3)]
                hit_point[1] = 0
        else:
            hit_point = [ray_start[i] + 10.0 * ray_dir[i] for i in range(3)]
            hit_point[1] = 0
        
        hit_point = self.snap_to_grid_pos(hit_point)
        
        if self.mode == "platform":
            platform_y = hit_point[1] + 0.25
            self.platforms.append([hit_point[0], platform_y, hit_point[2], 
                                 1.0, 0.5, 1.0, self.color_index])
            self.selected_platform = len(self.platforms) - 1
            self.selected_coin = None
            print(f">>> Placed platform at {[round(c,2) for c in self.platforms[-1][:3]]}")
        elif self.mode == "coin":
            coin_y = hit_point[1] + 0.25
            self.coins.append([hit_point[0], coin_y, hit_point[2]])
            self.selected_coin = len(self.coins) - 1
            self.selected_platform = None
            print(f">>> Placed coin at {[round(c,2) for c in self.coins[-1]]}")
    
    def delete_selected(self):
        if self.selected_platform is not None:
            del self.platforms[self.selected_platform]
            self.selected_platform = None
            print(">>> Deleted platform")
        elif self.selected_coin is not None:
            del self.coins[self.selected_coin]
            self.selected_coin = None
            print(">>> Deleted coin")
    
    def change_color(self):
        if self.selected_platform is not None and self.mode == "platform":
            self.platforms[self.selected_platform][6] = \
                (self.platforms[self.selected_platform][6] + 1) % len(PLATFORM_COLORS)
            new_color_name = COLOR_NAMES[self.platforms[self.selected_platform][6]]
            print(f">>> Changed selected platform color to {new_color_name}")
        else:
            self.color_index = (self.color_index + 1) % len(PLATFORM_COLORS)
            print(f">>> Next platform color: {COLOR_NAMES[self.color_index]}")
    
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
    
    def resize_selected(self, delta_dims):
        if self.selected_platform is not None and self.mode == "platform":
            for i in range(3):
                new_dim = self.platforms[self.selected_platform][3 + i] + delta_dims[i]
                self.platforms[self.selected_platform][3 + i] = max(0.1, new_dim)
            print(f">>> Resized platform to {[round(d,2) for d in self.platforms[self.selected_platform][3:6]]}")
    
    def quick_save(self):
        filename = f"{self.current_level_name}_{self.save_slot}.json"
        
        platforms_data = []
        platform_colors_data = []
        
        for p_data in self.platforms:
            platforms_data.append(p_data[:6])
            platform_colors_data.append(list(PLATFORM_COLORS[p_data[6]]))
        
        level_data = {
            "platforms": platforms_data,
            "platform_colors": platform_colors_data,
            "coins": self.coins
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(level_data, f, indent=2)
            print(f">>> Level saved as {filename}")
        except Exception as e:
            print(f">>> Error saving {filename}: {e}")
    
    def quick_load(self):
        filename = f"{self.current_level_name}_{self.save_slot}.json"
        
        try:
            with open(filename, 'r') as f:
                level_data = json.load(f)
            
            self.platforms = []
            self.coins = level_data.get("coins", [])
            
            loaded_platforms_data = level_data.get("platforms", [])
            loaded_platform_colors = level_data.get("platform_colors", [])
            
            for i, platform_geom in enumerate(loaded_platforms_data):
                color_index = 0
                if i < len(loaded_platform_colors):
                    loaded_color_rgb = loaded_platform_colors[i]
                    
                    min_dist_sq = float('inf')
                    best_match_idx = 0
                    for j, palette_color_rgb in enumerate(PLATFORM_COLORS):
                        dist_sq = sum((lc - pc)**2 for lc, pc in zip(loaded_color_rgb, palette_color_rgb))
                        if dist_sq < min_dist_sq:
                            min_dist_sq = dist_sq
                            best_match_idx = j
                        if min_dist_sq < 1e-9:
                            break
                    color_index = best_match_idx
                
                self.platforms.append(list(platform_geom) + [color_index])
            
            self.selected_platform = None
            self.selected_coin = None
            print(f">>> Level loaded from {filename}. Platforms: {len(self.platforms)}, Coins: {len(self.coins)}")
            
        except FileNotFoundError:
            print(f">>> Save file not found: {filename}. Using default level.")
            self.platforms = [[0, 0.25, 0, 2, 0.5, 2, 0]]  # Default platform
            self.coins = []
            self.selected_platform = None
            self.selected_coin = None
        except Exception as e:
            print(f">>> Error loading {filename}: {e}. Using default level.")
            self.platforms = [[0, 0.25, 0, 2, 0.5, 2, 0]]
            self.coins = []
            self.selected_platform = None
            self.selected_coin = None
    
    def reset_level(self):
        self.platforms = [[0, 0.25, 0, 2, 0.5, 2, 0]]  # Keep one default platform
        self.coins = []
        self.selected_platform = None
        self.selected_coin = None
        print(">>> Level reset")
    
    def update(self, dt):
        keys = pygame.key.get_pressed()
        running, mouse_rel = self.handle_events()
        
        if not running:
            return False
            
        self.camera.update(keys, mouse_rel, dt)
        return True
    
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearDepth(1.0)
        self.camera.apply()
        
        # Draw grid
        glPushMatrix()
        draw_grid(size=20, spacing=1.0)
        glPopMatrix()
        
        # Draw platforms
        for i, platform_data in enumerate(self.platforms):
            x, y, z, w, h, d, color_idx = platform_data
            color = PLATFORM_COLORS[color_idx]
            is_selected = (i == self.selected_platform)
            glPushMatrix()
            draw_platform(x, y, z, w, h, d, color, is_selected)
            glPopMatrix()
        
        # Draw coins
        for i, coin_data in enumerate(self.coins):
            x, y, z = coin_data
            is_selected = (i == self.selected_coin)
            glPushMatrix()
            draw_coin(x, y, z, is_selected)
            glPopMatrix()
        
        # Draw UI
        self.render_ui()
        
        pygame.display.flip()
    
    def render_ui(self):
        if not self.font:
            return
            
        # Create text surfaces
        ui_texts = [
            f"Mode: {self.mode.title()}",
            f"Color: {COLOR_NAMES[self.platforms[self.selected_platform][6] if self.selected_platform is not None and self.mode == 'platform' else self.color_index]}" if self.mode == "platform" else "Color: N/A",
            f"Slot: {self.save_slot}",
            f"Platforms: {len(self.platforms)}, Coins: {len(self.coins)}",
            f"Grid Snap: {'ON' if self.snap_to_grid else 'OFF'}",
            f"Camera: ({self.camera.x:.1f}, {self.camera.y:.1f}, {self.camera.z:.1f})"
        ]
        
        # Switch to 2D
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, display_width, display_height, 0, -1, 1)  # Note: flipped Y
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # Draw background
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.0, 0.0, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(5, 5)
        glVertex2f(350, 5)
        glVertex2f(350, 130)
        glVertex2f(5, 130)
        glEnd()
        glDisable(GL_BLEND)
        
        # Render text using pygame to OpenGL
        y_pos = 15
        for text in ui_texts:
            text_surface = self.font.render(text, True, (255, 255, 255))
            text_data = pygame.image.tostring(text_surface, "RGBA", 1)
            text_width, text_height = text_surface.get_size()
            
            # Create and bind texture
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_width, text_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            
            # Draw textured quad
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(1, 1, 1, 1)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(10, y_pos)
            glTexCoord2f(1, 0); glVertex2f(10 + text_width, y_pos)
            glTexCoord2f(1, 1); glVertex2f(10 + text_width, y_pos + text_height)
            glTexCoord2f(0, 1); glVertex2f(10, y_pos + text_height)
            glEnd()
            glDisable(GL_TEXTURE_2D)
            glDisable(GL_BLEND)
            
            # Clean up texture
            glDeleteTextures([texture])
            
            y_pos += 20
        
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
        
        print(">>> Editor starting...")
        
        running = True
        frame_count = 0
        
        while running:
            current_time = pygame.time.get_ticks()
            dt = (current_time - last_time) / 1000.0
            last_time = current_time
            dt = min(dt, 1/30.0)
            
            running = self.update(dt)
            if running:
                self.render()
                
            # Debug output every 60 frames
            frame_count += 1
            if frame_count % 60 == 0:
                print(f">>> Frame {frame_count}: Camera=({self.camera.x:.1f},{self.camera.y:.1f},{self.camera.z:.1f}), "
                      f"Objects={len(self.platforms)}P+{len(self.coins)}C")
                
            clock.tick(60)
        
        print(">>> Editor closing...")
        pygame.quit()

if __name__ == "__main__":
    try:
        editor = LevelEditor()
        editor.run()
    except Exception as e:
        print(f">>> Critical Error: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit() 