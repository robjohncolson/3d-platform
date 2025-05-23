"""
Level Integration Helper for 3D Platformer

This script helps you integrate custom levels created with the level editor
into your main platformer game.
"""

import json
import os

class LevelManager:
    def __init__(self, game_instance):
        self.game = game_instance
        self.custom_levels = []
        self.load_custom_levels()
    
    def load_custom_levels(self):
        """Load all custom level files from the current directory"""
        for filename in os.listdir('.'):
            if filename.endswith('.json') and filename != 'platformer_save.json':
                try:
                    with open(filename, 'r') as f:
                        level_data = json.load(f)
                    
                    # Validate level format
                    if 'platforms' in level_data and 'coins' in level_data:
                        self.custom_levels.append({
                            'filename': filename,
                            'name': filename.replace('.json', '').replace('_', ' ').title(),
                            'data': level_data
                        })
                        print(f"Loaded custom level: {filename}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
    
    def load_custom_level(self, level_index):
        """Load a custom level into the game"""
        if 0 <= level_index < len(self.custom_levels):
            level_data = self.custom_levels[level_index]['data']
            
            # Set platforms
            self.game.platforms = level_data['platforms']
            
            # Set platform colors
            if 'platform_colors' in level_data:
                self.game.platform_colors = level_data['platform_colors']
            else:
                # Default colors if not specified
                from main_game import GREEN
                self.game.platform_colors = [GREEN] * len(self.game.platforms)
            
            # Set coins
            self.game.coins = level_data['coins']
            
            # Reset player
            self.game.player.reset()
            
            print(f"Loaded custom level: {self.custom_levels[level_index]['name']}")
            return True
        return False
    
    def list_custom_levels(self):
        """Print all available custom levels"""
        if not self.custom_levels:
            print("No custom levels found. Create some with the level editor!")
            return
        
        print("\nAvailable Custom Levels:")
        for i, level in enumerate(self.custom_levels):
            platforms_count = len(level['data']['platforms'])
            coins_count = len(level['data']['coins'])
            print(f"{i}: {level['name']} ({platforms_count} platforms, {coins_count} coins)")

def add_custom_level_support_to_game():
    """
    Example of how to modify your main game to support custom levels.
    
    Add this code to your Game class __init__ method:
    
    # Add custom level support
    self.level_manager = LevelManager(self)
    
    And add this to your handle_events method:
    
    elif event.key == pygame.K_F3:
        # Load custom level menu
        self.level_manager.list_custom_levels()
        if self.level_manager.custom_levels:
            try:
                level_num = int(input("Enter custom level number: "))
                if self.level_manager.load_custom_level(level_num):
                    self.game_state = "playing"
            except:
                print("Invalid level number")
    """
    pass

# Example usage and testing
def test_level_loading():
    """Test function to demonstrate level loading"""
    
    # Create a sample level file for testing
    sample_level = {
        "platforms": [
            [0, -0.5, 0, 4, 0.5, 4],      # Base platform
            [2, 0.2, -2, 1, 0.3, 1],      # Jump platform
            [0, 0.8, -4, 1.5, 0.3, 1.5],  # Higher platform
            [-2, 1.4, -2, 1, 0.3, 1],     # Side platform
        ],
        "platform_colors": [
            [0.1, 0.4, 0.1],  # Dark green for base
            [0.2, 0.7, 0.2],  # Green
            [0.2, 0.2, 0.8],  # Blue
            [0.8, 0.2, 0.2],  # Red
        ],
        "coins": [
            [2, 0.9, -2],
            [0, 1.5, -4],
            [-2, 2.1, -2]
        ]
    }
    
    # Save sample level
    with open('sample_custom_level.json', 'w') as f:
        json.dump(sample_level, f, indent=2)
    
    print("Created sample_custom_level.json for testing")
    print("\nTo use custom levels in your game:")
    print("1. Create levels with level_editor.py")
    print("2. Save them as .json files")
    print("3. Add custom level support to your main game")
    print("4. Use F3 key (or your chosen key) to load custom levels")

if __name__ == "__main__":
    test_level_loading()
    add_custom_level_support_to_game()
    print(__doc__) 