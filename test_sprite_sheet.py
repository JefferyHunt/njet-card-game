#!/usr/bin/env python3
"""Test script for sprite sheet functionality"""

import tkinter as tk
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✓ PIL/Pillow available")
except ImportError:
    PIL_AVAILABLE = False
    print("✗ PIL/Pillow not available")

# Define necessary classes (copied from main game)
class Suit(Enum):
    RED = "Red"
    BLUE = "Blue"
    YELLOW = "Yellow"
    GREEN = "Green"

@dataclass
class Card:
    suit: Suit
    value: int
    
    def __str__(self):
        return f"{self.value} of {self.suit.value}"

class CardSpriteManager:
    """Manages card sprite sheet for rendering cards from a sprite sheet image."""
    
    def __init__(self, sprite_sheet_path):
        """Initialize the sprite manager with the sprite sheet image."""
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow is required for sprite sheet support")
            
        # Load the sprite sheet
        self.sprite_sheet = Image.open(sprite_sheet_path)
        self.sheet_width, self.sheet_height = self.sprite_sheet.size
        
        # Calculate card dimensions based on sprite sheet size
        self.card_width = self.sheet_width // 11  # 11 columns (0-9 + back)
        self.card_height = self.sheet_height // 4  # 4 rows (4 suits)
        
        print(f"✓ Sprite sheet loaded: {self.sheet_width}x{self.sheet_height}")
        print(f"✓ Card dimensions: {self.card_width}x{self.card_height}")
        
        # Suit mapping to row index
        self.suit_to_row = {
            Suit.RED: 0,     # Red Hearts (top row)
            Suit.GREEN: 1,   # Green Clubs
            Suit.YELLOW: 2,  # Yellow Diamonds  
            Suit.BLUE: 3     # Blue Spades (bottom row)
        }
        
        # Cache for rendered card images
        self.card_cache = {}
        self.card_back_cache = {}
        
    def get_card_image(self, card, width=60, height=80):
        """Get a tkinter PhotoImage for the specified card."""
        cache_key = f"{card.suit.value}_{card.value}_{width}_{height}"
        
        if cache_key not in self.card_cache:
            # Calculate crop coordinates
            row = self.suit_to_row[card.suit]
            col = card.value  # Values 0-9 map directly to columns 0-9
            
            left = col * self.card_width
            top = row * self.card_height
            right = left + self.card_width
            bottom = top + self.card_height
            
            # Crop the card from sprite sheet
            card_image = self.sprite_sheet.crop((left, top, right, bottom))
            
            # Resize to desired dimensions
            card_image = card_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.card_cache[cache_key] = ImageTk.PhotoImage(card_image)
            
        return self.card_cache[cache_key]
    
    def get_card_back_image(self, width=60, height=80):
        """Get a tkinter PhotoImage for the card back."""
        cache_key = f"back_{width}_{height}"
        
        if cache_key not in self.card_back_cache:
            # Card back is in column 10 (rightmost), any row works
            row = 0  # Use top row
            col = 10  # Card back column
            
            left = col * self.card_width
            top = row * self.card_height
            right = left + self.card_width
            bottom = top + self.card_height
            
            # Crop the card back
            back_image = self.sprite_sheet.crop((left, top, right, bottom))
            
            # Resize to desired dimensions
            back_image = back_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.card_back_cache[cache_key] = ImageTk.PhotoImage(back_image)
            
        return self.card_back_cache[cache_key]

def test_sprite_sheet():
    """Test sprite sheet loading and display some sample cards"""
    if not PIL_AVAILABLE:
        print("Cannot test sprite sheet without PIL/Pillow")
        return
        
    try:
        # Create sprite manager
        sprite_manager = CardSpriteManager("CardSpriteSheet.png")
        
        # Create test window
        root = tk.Tk()
        root.title("Sprite Sheet Test - Full Size Cards")
        root.geometry("1200x800")
        
        # Create some test cards
        test_cards = [
            Card(Suit.RED, 0),
            Card(Suit.GREEN, 5),
            Card(Suit.YELLOW, 9),
            Card(Suit.BLUE, 3)
        ]
        
        # Display cards
        for i, card in enumerate(test_cards):
            frame = tk.Frame(root, relief=tk.RAISED, bd=2)
            frame.pack(side=tk.LEFT, padx=10, pady=10)
            
            # Get card image - using new default size
            card_image = sprite_manager.get_card_image(card)
            
            # Display image
            label = tk.Label(frame, image=card_image)
            label.image = card_image  # Keep reference
            label.pack()
            
            # Add text label
            tk.Label(frame, text=str(card)).pack()
        
        # Display card back
        back_frame = tk.Frame(root, relief=tk.RAISED, bd=2)
        back_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        back_image = sprite_manager.get_card_back_image()
        back_label = tk.Label(back_frame, image=back_image)
        back_label.image = back_image
        back_label.pack()
        
        tk.Label(back_frame, text="Card Back").pack()
        
        print("✓ Sprite sheet test window created")
        print("  Close the window to continue...")
        
        # Run for a short time then close
        root.after(3000, root.destroy)  # Auto-close after 3 seconds
        root.mainloop()
        
        print("✓ Sprite sheet test completed successfully!")
        
    except Exception as e:
        print(f"✗ Sprite sheet test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sprite_sheet()