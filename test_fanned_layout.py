#!/usr/bin/env python3
"""Test the new fanned card layout and improved sprite quality"""

import tkinter as tk
from enum import Enum
from dataclasses import dataclass
import random

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✓ PIL/Pillow available")
except ImportError:
    PIL_AVAILABLE = False
    print("✗ PIL/Pillow not available")

# Define necessary classes
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
    """Updated sprite manager with native resolution defaults"""
    
    def __init__(self, sprite_sheet_path):
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow is required for sprite sheet support")
            
        self.sprite_sheet = Image.open(sprite_sheet_path)
        self.sheet_width, self.sheet_height = self.sprite_sheet.size
        
        self.card_width = self.sheet_width // 11
        self.card_height = self.sheet_height // 4
        
        print(f"✓ Sprite sheet loaded: {self.sheet_width}x{self.sheet_height}")
        print(f"✓ Native card size: {self.card_width}x{self.card_height}")
        
        self.suit_to_row = {
            Suit.RED: 0,     # Red Hearts (top row)
            Suit.GREEN: 1,   # Green Clubs
            Suit.YELLOW: 2,  # Yellow Diamonds  
            Suit.BLUE: 3     # Blue Spades (bottom row)
        }
        
        self.card_cache = {}
        self.card_back_cache = {}
        
    def get_card_image(self, card, width=None, height=None):
        """Get card image - defaults to native resolution for best quality"""
        if width is None:
            width = self.card_width
        if height is None:
            height = self.card_height
            
        cache_key = f"{card.suit.value}_{card.value}_{width}_{height}"
        
        if cache_key not in self.card_cache:
            row = self.suit_to_row[card.suit]
            col = card.value
            
            left = col * self.card_width
            top = row * self.card_height
            right = left + self.card_width
            bottom = top + self.card_height
            
            card_image = self.sprite_sheet.crop((left, top, right, bottom))
            
            if width != self.card_width or height != self.card_height:
                card_image = card_image.resize((width, height), Image.Resampling.LANCZOS)
            
            self.card_cache[cache_key] = ImageTk.PhotoImage(card_image)
            
        return self.card_cache[cache_key]
    
    def get_card_back_image(self, width=None, height=None):
        """Get card back - defaults to native resolution"""
        if width is None:
            width = self.card_width
        if height is None:
            height = self.card_height
            
        cache_key = f"back_{width}_{height}"
        
        if cache_key not in self.card_back_cache:
            row = 0
            col = 10
            
            left = col * self.card_width
            top = row * self.card_height
            right = left + self.card_width
            bottom = top + self.card_height
            
            back_image = self.sprite_sheet.crop((left, top, right, bottom))
            
            if width != self.card_width or height != self.card_height:
                back_image = back_image.resize((width, height), Image.Resampling.LANCZOS)
            
            self.card_back_cache[cache_key] = ImageTk.PhotoImage(back_image)
            
        return self.card_back_cache[cache_key]

def create_fanned_layout_test(canvas, cards, x_start, y_start, orientation="horizontal", card_size=(80, 120)):
    """Create fanned card layout on canvas"""
    card_w, card_h = card_size
    overlap_spacing = 20
    
    if orientation == "horizontal":
        for i, card in enumerate(cards):
            x_pos = x_start + i * overlap_spacing
            y_pos = y_start
            
            try:
                card_image = sprite_manager.get_card_image(card, card_w, card_h)
                canvas.create_image(x_pos + card_w//2, y_pos + card_h//2, image=card_image)
                
                # Store reference
                if not hasattr(canvas, 'card_images'):
                    canvas.card_images = []
                canvas.card_images.append(card_image)
                
            except Exception as e:
                print(f"Error creating card: {e}")
                
    else:  # vertical
        for i, card in enumerate(cards):
            x_pos = x_start
            y_pos = y_start + i * overlap_spacing
            
            try:
                card_image = sprite_manager.get_card_image(card, card_w, card_h)
                canvas.create_image(x_pos + card_w//2, y_pos + card_h//2, image=card_image)
                
                if not hasattr(canvas, 'card_images'):
                    canvas.card_images = []
                canvas.card_images.append(card_image)
                
            except Exception as e:
                print(f"Error creating card: {e}")

def test_fanned_layouts():
    """Test the fanned layout system and high-quality sprites"""
    if not PIL_AVAILABLE:
        print("Cannot test without PIL/Pillow")
        return
        
    global sprite_manager
    
    try:
        sprite_manager = CardSpriteManager("CardSpriteSheet.png")
        
        root = tk.Tk()
        root.title("Fanned Layout Test - High Quality Cards")
        root.geometry("1400x900")
        root.configure(bg="#2C3E50")
        
        # Title
        title = tk.Label(root, text="NJET - Fanned Card Layout Test", 
                        font=("Arial", 18, "bold"), bg="#2C3E50", fg="white")
        title.pack(pady=10)
        
        # Create main canvas
        main_canvas = tk.Canvas(root, width=1300, height=800, bg="#34495E")
        main_canvas.pack(pady=10)
        
        # Create test hands
        suits = [Suit.RED, Suit.GREEN, Suit.YELLOW, Suit.BLUE]
        
        # Bottom player - horizontal fan (human player view)
        bottom_cards = [Card(random.choice(suits), random.randint(0, 9)) for _ in range(10)]
        create_fanned_layout_test(main_canvas, bottom_cards, 50, 650, "horizontal", (100, 150))
        main_canvas.create_text(50, 630, text="Bottom Player (Human)", anchor="w", 
                               fill="white", font=("Arial", 12, "bold"))
        
        # Top player - horizontal fan  
        top_cards = [Card(random.choice(suits), random.randint(0, 9)) for _ in range(8)]
        create_fanned_layout_test(main_canvas, top_cards, 800, 50, "horizontal", (80, 120))
        main_canvas.create_text(800, 30, text="Top Player (AI)", anchor="w",
                               fill="white", font=("Arial", 12, "bold"))
        
        # Left player - vertical fan
        left_cards = [Card(random.choice(suits), random.randint(0, 9)) for _ in range(7)]
        create_fanned_layout_test(main_canvas, left_cards, 50, 200, "vertical", (80, 120))
        main_canvas.create_text(20, 180, text="Left\\nPlayer\\n(AI)", anchor="w",
                               fill="white", font=("Arial", 10, "bold"))
        
        # Right player - vertical fan
        right_cards = [Card(random.choice(suits), random.randint(0, 9)) for _ in range(9)]
        create_fanned_layout_test(main_canvas, right_cards, 1150, 300, "vertical", (80, 120))
        main_canvas.create_text(1120, 280, text="Right\\nPlayer\\n(AI)", anchor="w",
                               fill="white", font=("Arial", 10, "bold"))
        
        # Center area - show single high-quality cards
        center_cards = [
            Card(Suit.RED, 7),
            Card(Suit.GREEN, 0),
            Card(Suit.YELLOW, 9),
            Card(Suit.BLUE, 3)
        ]
        
        main_canvas.create_text(650, 320, text="Trick Center - Full Quality", 
                               fill="white", font=("Arial", 14, "bold"))
        
        for i, card in enumerate(center_cards):
            x_pos = 500 + i * 100
            y_pos = 350
            
            try:
                # Use native resolution for center cards
                card_image = sprite_manager.get_card_image(card, 120, 180)
                main_canvas.create_image(x_pos, y_pos, image=card_image)
                
                if not hasattr(main_canvas, 'center_images'):
                    main_canvas.center_images = []
                main_canvas.center_images.append(card_image)
                
            except Exception as e:
                print(f"Error creating center card: {e}")
        
        # Add card backs
        main_canvas.create_text(200, 580, text="Card Backs (Fanned)", 
                               fill="white", font=("Arial", 12, "bold"))
        
        for i in range(5):
            x_pos = 200 + i * 15
            y_pos = 600
            
            try:
                back_image = sprite_manager.get_card_back_image(60, 90)
                main_canvas.create_image(x_pos, y_pos, image=back_image)
                
                if not hasattr(main_canvas, 'back_images'):
                    main_canvas.back_images = []
                main_canvas.back_images.append(back_image)
                
            except Exception as e:
                print(f"Error creating card back: {e}")
        
        # Info text
        info = tk.Label(root, 
                       text="Fanned layouts save space while maintaining card visibility!\nCards now use native resolution for perfect quality.",
                       font=("Arial", 11), bg="#2C3E50", fg="lightgreen", justify=tk.CENTER)
        info.pack(pady=5)
        
        print("✓ Fanned layout test window created")
        print("  - Bottom: Human player with larger fanned cards")
        print("  - Sides: AI players with vertical fans")
        print("  - Center: Full quality cards in trick area")
        print("  Window will auto-close in 8 seconds...")
        
        root.after(8000, root.destroy)
        root.mainloop()
        
        print("✓ Fanned layout test completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fanned_layouts()