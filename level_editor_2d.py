import pygame
import json
import math
import os

# Initialize pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
GRID_SIZE = 20  # pixels per unit
GRID_OFFSET_X = WINDOW_WIDTH // 2
GRID_OFFSET_Y = WINDOW_HEIGHT // 2

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
BLUE = (100, 100, 255)
YELLOW = (255, 255, 100)
DARK_GREEN = (50, 150, 50)
PURPLE = (200, 100, 200)
ORANGE = (255, 150, 50)
CYAN = (100, 255, 255)
PINK = (255, 150, 150)

# Platform colors (matching the game)
PLATFORM_COLORS = [
    (50, 200, 50),    # Green
    (25, 100, 25),    # Dark Green  
    (50, 50, 200),    # Blue
    (200, 50, 50),    # Red
    (230, 230, 230),  # White
    (230, 200, 25),   # Yellow
    (180, 50, 180),   # Purple
    (230, 125, 25),   # Orange
    (50, 200, 200),   # Cyan
]

COLOR_NAMES = ["Green", "Dark Green", "Blue", "Red", "White", "Yellow", "Purple", "Orange", "Cyan"]

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.zoom = 1.0
    
    def screen_to_world(self, screen_x, screen_y):
        world_x = (screen_x - GRID_OFFSET_X) / (GRID_SIZE * self.zoom) + self.x
        world_y = (screen_y - GRID_OFFSET_Y) / (GRID_SIZE * self.zoom) + self.y
        return world_x, world_y
    
    def world_to_screen(self, world_x, world_y):
        screen_x = (world_x - self.x) * GRID_SIZE * self.zoom + GRID_OFFSET_X
        screen_y = (world_y - self.y) * GRID_SIZE * self.zoom + GRID_OFFSET_Y
        return int(screen_x), int(screen_y)

class LevelEditor2D:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("2D Level Editor - Top Down View")
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        self.camera = Camera()
        self.platforms = []  # [x, y, z, width, height, depth, color_index]
        self.coins = []      # [x, y, z]
        
        self.selected_platform = None
        self.selected_coin = None
        self.mode = "platform"  # "platform" or "coin"
        self.color_index = 0
        
        self.dragging = False
        self.drag_offset = (0, 0)
        
        self.snap_to_grid = True
        self.grid_snap = 0.5
        
        self.current_level_name = "my_level"
        self.save_slot = 1
        
        # Create a default platform
        self.platforms = [[0, 0.25, 0, 2, 0.5, 2, 0]]
        
        print("=== 2D Level Editor ===")
        print("Mouse: Left click - Select/Place, Right drag - Pan camera, Wheel - Zoom")
        print("F1 - Platform mode, F2 - Coin mode")
        print("WASD/Arrow Keys - Move selected object")
        print("Q/E - Lower/Raise Y position")
        print("R/T - Shrink/Grow selected platform")
        print("C - Change color, G - Toggle grid snap")
        print("S - Save, L - Load, 1-5 - Change save slot")
        print("Delete - Remove selected, ESC - Exit")
        print("======================")
    
    def snap_position(self, x, y):
        if self.snap_to_grid:
            x = round(x / self.grid_snap) * self.grid_snap
            y = round(y / self.grid_snap) * self.grid_snap
        return x, y
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_F1:
                    self.mode = "platform"
                    self.selected_coin = None
                    print("Platform mode")
                elif event.key == pygame.K_F2:
                    self.mode = "coin"
                    self.selected_platform = None
                    print("Coin mode")
                elif event.key == pygame.K_c:
                    self.change_color()
                elif event.key == pygame.K_g:
                    self.snap_to_grid = not self.snap_to_grid
                    print(f"Grid snap: {'ON' if self.snap_to_grid else 'OFF'}")
                elif event.key == pygame.K_s:
                    self.save_level()
                elif event.key == pygame.K_l:
                    self.load_level()
                elif event.key == pygame.K_DELETE:
                    self.delete_selected()
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    self.save_slot = event.key - pygame.K_0
                    print(f"Save slot: {self.save_slot}")
                
                # Movement keys
                elif event.key in (pygame.K_w, pygame.K_UP):
                    self.move_selected(0, -0.5)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    self.move_selected(0, 0.5)
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    self.move_selected(-0.5, 0)
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.move_selected(0.5, 0)
                elif event.key == pygame.K_q:
                    self.move_selected_y(-0.5)
                elif event.key == pygame.K_e:
                    self.move_selected_y(0.5)
                
                # Resize keys (for platforms)
                elif event.key == pygame.K_r:
                    self.resize_selected(-0.5)
                elif event.key == pygame.K_t:
                    self.resize_selected(0.5)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_left_click(event.pos)
                elif event.button == 3:  # Right click (start panning)
                    self.dragging = True
                    self.drag_offset = event.pos
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:  # Right click release
                    self.dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    # Pan camera
                    dx = event.pos[0] - self.drag_offset[0]
                    dy = event.pos[1] - self.drag_offset[1]
                    self.camera.x -= dx / (GRID_SIZE * self.camera.zoom)
                    self.camera.y -= dy / (GRID_SIZE * self.camera.zoom)
                    self.drag_offset = event.pos
            
            elif event.type == pygame.MOUSEWHEEL:
                # Zoom
                old_zoom = self.camera.zoom
                if event.y > 0:
                    self.camera.zoom *= 1.1
                else:
                    self.camera.zoom /= 1.1
                self.camera.zoom = max(0.1, min(5.0, self.camera.zoom))
        
        return True
    
    def handle_left_click(self, pos):
        world_x, world_z = self.camera.screen_to_world(pos[0], pos[1])
        
        # Check for selection
        selected_something = False
        
        # Check platforms
        for i, platform in enumerate(self.platforms):
            px, py, pz, pw, ph, pd = platform[:6]
            if (abs(world_x - px) < pw/2 and abs(world_z - pz) < pd/2):
                self.selected_platform = i
                self.selected_coin = None
                selected_something = True
                print(f"Selected platform {i}")
                break
        
        # Check coins if no platform selected
        if not selected_something:
            for i, coin in enumerate(self.coins):
                cx, cy, cz = coin
                if (abs(world_x - cx) < 0.3 and abs(world_z - cz) < 0.3):
                    self.selected_coin = i
                    self.selected_platform = None
                    selected_something = True
                    print(f"Selected coin {i}")
                    break
        
        # Place new object if nothing selected
        if not selected_something:
            world_x, world_z = self.snap_position(world_x, world_z)
            
            if self.mode == "platform":
                self.platforms.append([world_x, 0.25, world_z, 1.0, 0.5, 1.0, self.color_index])
                self.selected_platform = len(self.platforms) - 1
                self.selected_coin = None
                print(f"Placed platform at ({world_x:.1f}, {world_z:.1f})")
            elif self.mode == "coin":
                self.coins.append([world_x, 0.5, world_z])
                self.selected_coin = len(self.coins) - 1
                self.selected_platform = None
                print(f"Placed coin at ({world_x:.1f}, {world_z:.1f})")
    
    def move_selected(self, dx, dz):
        if self.selected_platform is not None:
            self.platforms[self.selected_platform][0] += dx
            self.platforms[self.selected_platform][2] += dz
            if self.snap_to_grid:
                x, z = self.snap_position(self.platforms[self.selected_platform][0], self.platforms[self.selected_platform][2])
                self.platforms[self.selected_platform][0] = x
                self.platforms[self.selected_platform][2] = z
        elif self.selected_coin is not None:
            self.coins[self.selected_coin][0] += dx
            self.coins[self.selected_coin][2] += dz
            if self.snap_to_grid:
                x, z = self.snap_position(self.coins[self.selected_coin][0], self.coins[self.selected_coin][2])
                self.coins[self.selected_coin][0] = x
                self.coins[self.selected_coin][2] = z
    
    def move_selected_y(self, dy):
        if self.selected_platform is not None:
            self.platforms[self.selected_platform][1] += dy
        elif self.selected_coin is not None:
            self.coins[self.selected_coin][1] += dy
    
    def resize_selected(self, delta):
        if self.selected_platform is not None:
            platform = self.platforms[self.selected_platform]
            platform[3] = max(0.5, platform[3] + delta)  # width
            platform[5] = max(0.5, platform[5] + delta)  # depth
            print(f"Platform size: {platform[3]:.1f} x {platform[5]:.1f}")
    
    def change_color(self):
        if self.selected_platform is not None:
            platform = self.platforms[self.selected_platform]
            platform[6] = (platform[6] + 1) % len(PLATFORM_COLORS)
            print(f"Platform color: {COLOR_NAMES[platform[6]]}")
        else:
            self.color_index = (self.color_index + 1) % len(PLATFORM_COLORS)
            print(f"Next color: {COLOR_NAMES[self.color_index]}")
    
    def delete_selected(self):
        if self.selected_platform is not None:
            del self.platforms[self.selected_platform]
            self.selected_platform = None
            print("Deleted platform")
        elif self.selected_coin is not None:
            del self.coins[self.selected_coin]
            self.selected_coin = None
            print("Deleted coin")
    
    def save_level(self):
        filename = f"{self.current_level_name}_{self.save_slot}.json"
        
        platforms_data = []
        platform_colors_data = []
        
        for platform in self.platforms:
            platforms_data.append(platform[:6])  # x, y, z, w, h, d
            color_index = platform[6]
            # Convert to game format (0-1 range)
            game_color = tuple(c / 255.0 for c in PLATFORM_COLORS[color_index])
            platform_colors_data.append(list(game_color))
        
        level_data = {
            "platforms": platforms_data,
            "platform_colors": platform_colors_data,
            "coins": self.coins
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(level_data, f, indent=2)
            print(f"Saved: {filename}")
        except Exception as e:
            print(f"Save error: {e}")
    
    def load_level(self):
        filename = f"{self.current_level_name}_{self.save_slot}.json"
        
        try:
            with open(filename, 'r') as f:
                level_data = json.load(f)
            
            self.platforms = []
            self.coins = level_data.get("coins", [])
            
            platforms_data = level_data.get("platforms", [])
            platform_colors_data = level_data.get("platform_colors", [])
            
            for i, platform_geom in enumerate(platforms_data):
                color_index = 0
                if i < len(platform_colors_data):
                    game_color = platform_colors_data[i]
                    # Convert from game format and find closest match
                    editor_color = tuple(int(c * 255) for c in game_color)
                    
                    min_dist = float('inf')
                    for j, palette_color in enumerate(PLATFORM_COLORS):
                        dist = sum((a - b) ** 2 for a, b in zip(editor_color, palette_color))
                        if dist < min_dist:
                            min_dist = dist
                            color_index = j
                
                self.platforms.append(list(platform_geom) + [color_index])
            
            self.selected_platform = None
            self.selected_coin = None
            print(f"Loaded: {filename} ({len(self.platforms)} platforms, {len(self.coins)} coins)")
            
        except FileNotFoundError:
            print(f"File not found: {filename}")
        except Exception as e:
            print(f"Load error: {e}")
    
    def draw_grid(self):
        # Calculate grid bounds
        screen_bounds = [
            self.camera.screen_to_world(0, 0),
            self.camera.screen_to_world(WINDOW_WIDTH, WINDOW_HEIGHT)
        ]
        
        min_x = int(min(screen_bounds[0][0], screen_bounds[1][0]) - 1)
        max_x = int(max(screen_bounds[0][0], screen_bounds[1][0]) + 1)
        min_y = int(min(screen_bounds[0][1], screen_bounds[1][1]) - 1)
        max_y = int(max(screen_bounds[0][1], screen_bounds[1][1]) + 1)
        
        # Draw grid lines
        for x in range(min_x, max_x + 1):
            screen_x, _ = self.camera.world_to_screen(x, 0)
            if 0 <= screen_x <= WINDOW_WIDTH:
                color = GRAY if x % 5 == 0 else LIGHT_GRAY
                pygame.draw.line(self.screen, color, (screen_x, 0), (screen_x, WINDOW_HEIGHT))
        
        for y in range(min_y, max_y + 1):
            _, screen_y = self.camera.world_to_screen(0, y)
            if 0 <= screen_y <= WINDOW_HEIGHT:
                color = GRAY if y % 5 == 0 else LIGHT_GRAY
                pygame.draw.line(self.screen, color, (0, screen_y), (WINDOW_WIDTH, screen_y))
        
        # Draw axes
        origin_x, origin_y = self.camera.world_to_screen(0, 0)
        if 0 <= origin_x <= WINDOW_WIDTH:
            pygame.draw.line(self.screen, RED, (origin_x, 0), (origin_x, WINDOW_HEIGHT), 2)
        if 0 <= origin_y <= WINDOW_HEIGHT:
            pygame.draw.line(self.screen, BLUE, (0, origin_y), (WINDOW_WIDTH, origin_y), 2)
    
    def draw_platforms(self):
        for i, platform in enumerate(self.platforms):
            x, y, z, w, h, d, color_idx = platform
            color = PLATFORM_COLORS[color_idx]
            
            # Convert to screen coordinates
            screen_x, screen_y = self.camera.world_to_screen(x, z)
            screen_w = int(w * GRID_SIZE * self.camera.zoom)
            screen_h = int(d * GRID_SIZE * self.camera.zoom)
            
            # Draw platform rectangle
            rect = pygame.Rect(screen_x - screen_w//2, screen_y - screen_h//2, screen_w, screen_h)
            pygame.draw.rect(self.screen, color, rect)
            
            # Draw selection outline
            if i == self.selected_platform:
                pygame.draw.rect(self.screen, YELLOW, rect, 3)
            else:
                pygame.draw.rect(self.screen, BLACK, rect, 1)
            
            # Draw Y position indicator
            if screen_w > 20 and screen_h > 20:
                y_text = self.small_font.render(f"Y:{y:.1f}", True, BLACK)
                text_rect = y_text.get_rect(center=(screen_x, screen_y))
                self.screen.blit(y_text, text_rect)
    
    def draw_coins(self):
        for i, coin in enumerate(self.coins):
            x, y, z = coin
            
            # Convert to screen coordinates
            screen_x, screen_y = self.camera.world_to_screen(x, z)
            radius = max(3, int(6 * self.camera.zoom))
            
            # Draw coin circle
            pygame.draw.circle(self.screen, YELLOW, (screen_x, screen_y), radius)
            
            # Draw selection outline
            if i == self.selected_coin:
                pygame.draw.circle(self.screen, RED, (screen_x, screen_y), radius + 2, 2)
            else:
                pygame.draw.circle(self.screen, BLACK, (screen_x, screen_y), radius, 1)
    
    def draw_ui(self):
        # Background panel
        ui_rect = pygame.Rect(10, 10, 300, 150)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), ui_rect)
        pygame.draw.rect(self.screen, WHITE, ui_rect, 2)
        
        # UI text
        y_pos = 20
        texts = [
            f"Mode: {self.mode.title()}",
            f"Color: {COLOR_NAMES[self.color_index]}",
            f"Save Slot: {self.save_slot}",
            f"Platforms: {len(self.platforms)}",
            f"Coins: {len(self.coins)}",
            f"Grid Snap: {'ON' if self.snap_to_grid else 'OFF'}",
            f"Zoom: {self.camera.zoom:.1f}x"
        ]
        
        for text in texts:
            surface = self.font.render(text, True, WHITE)
            self.screen.blit(surface, (20, y_pos))
            y_pos += 20
    
    def run(self):
        running = True
        
        while running:
            running = self.handle_events()
            
            # Clear screen
            self.screen.fill(WHITE)
            
            # Draw everything
            self.draw_grid()
            self.draw_platforms()
            self.draw_coins()
            self.draw_ui()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    try:
        editor = LevelEditor2D()
        editor.run()
    except Exception as e:
        print(f"Error: {e}")
        pygame.quit() 