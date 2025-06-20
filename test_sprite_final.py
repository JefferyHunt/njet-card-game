#!/usr/bin/env python3
"""Final test of sprite sheet integration with larger cards"""

import tkinter as tk
from enum import Enum
from dataclasses import dataclass

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
    """Updated sprite manager with larger default card sizes"""
    
    def __init__(self, sprite_sheet_path):
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow is required for sprite sheet support")
            
        self.sprite_sheet = Image.open(sprite_sheet_path)
        self.sheet_width, self.sheet_height = self.sprite_sheet.size
        
        # Calculate card dimensions based on sprite sheet size
        self.card_width = self.sheet_width // 11  # 11 columns (0-9 + back)
        self.card_height = self.sheet_height // 4  # 4 rows (4 suits)
        
        print(f"✓ Sprite sheet loaded: {self.sheet_width}x{self.sheet_height}")
        print(f"✓ Native card size: {self.card_width}x{self.card_height}")
        
        # Suit mapping to row index
        self.suit_to_row = {
            Suit.RED: 0,     # Red Hearts (top row)
            Suit.GREEN: 1,   # Green Clubs
            Suit.YELLOW: 2,  # Yellow Diamonds  
            Suit.BLUE: 3     # Blue Spades (bottom row)
        }
        
        self.card_cache = {}
        self.card_back_cache = {}
        
    def get_card_image(self, card, width=150, height=225):
        """Get card image with new larger default size"""
        cache_key = f"{card.suit.value}_{card.value}_{width}_{height}"
        
        if cache_key not in self.card_cache:
            row = self.suit_to_row[card.suit]
            col = card.value
            
            left = col * self.card_width
            top = row * self.card_height
            right = left + self.card_width
            bottom = top + self.card_height
            
            card_image = self.sprite_sheet.crop((left, top, right, bottom))
            
            # High-quality resampling
            if width != self.card_width or height != self.card_height:
                card_image = card_image.resize((width, height), Image.Resampling.LANCZOS)
            
            self.card_cache[cache_key] = ImageTk.PhotoImage(card_image)
            
        return self.card_cache[cache_key]
    
    def get_card_back_image(self, width=150, height=225):
        """Get card back with new larger default size"""
        cache_key = f"back_{width}_{height}"
        
        if cache_key not in self.card_back_cache:
            row = 0
            col = 10  # Card back column
            
            left = col * self.card_width
            top = row * self.card_height
            right = left + self.card_width
            bottom = top + self.card_height
            
            back_image = self.sprite_sheet.crop((left, top, right, bottom))
            
            if width != self.card_width or height != self.card_height:
                back_image = back_image.resize((width, height), Image.Resampling.LANCZOS)
            
            self.card_back_cache[cache_key] = ImageTk.PhotoImage(back_image)
            
        return self.card_back_cache[cache_key]

def test_final_implementation():
    """Test the final large card implementation"""
    if not PIL_AVAILABLE:
        print("Cannot test without PIL/Pillow")
        return
        
    try:
        # Create sprite manager
        sprite_manager = CardSpriteManager("CardSpriteSheet.png")
        
        # Create window sized for large cards
        root = tk.Tk()
        root.title("Final Sprite Test - Large High-Quality Cards")
        root.geometry("1600x900")
        root.configure(bg="#2C3E50")
        
        # Add title
        title = tk.Label(root, text="NJET - High Quality Card Display", 
                        font=("Arial", 20, "bold"), bg="#2C3E50", fg="white")
        title.pack(pady=20)
        
        # Create frame for cards
        cards_frame = tk.Frame(root, bg="#2C3E50")
        cards_frame.pack(pady=20)
        
        # Test different sizes
        sizes = [
            ("Small", 100, 150),
            ("Normal", 150, 225), 
            ("Large", 200, 300)
        ]
        
        for size_name, w, h in sizes:
            size_frame = tk.Frame(cards_frame, bg="#34495E", relief=tk.RAISED, bd=2)
            size_frame.pack(side=tk.LEFT, padx=20, pady=10)
            
            tk.Label(size_frame, text=f"{size_name} ({w}x{h})", 
                    font=("Arial", 12, "bold"), bg="#34495E", fg="white").pack(pady=5)
            
            # Show one card of each suit
            test_cards = [
                Card(Suit.RED, 7),
                Card(Suit.GREEN, 3), 
                Card(Suit.YELLOW, 9),
                Card(Suit.BLUE, 0)
            ]
            
            card_row = tk.Frame(size_frame, bg="#34495E")
            card_row.pack(pady=5)
            
            for card in test_cards:
                card_frame = tk.Frame(card_row, relief=tk.RAISED, bd=1)
                card_frame.pack(side=tk.LEFT, padx=2)
                
                try:
                    card_image = sprite_manager.get_card_image(card, w, h)
                    card_label = tk.Label(card_frame, image=card_image, bd=0)
                    card_label.image = card_image  # Keep reference
                    card_label.pack()
                    
                except Exception as e:
                    tk.Label(card_frame, text="Error", bg="red", fg="white", 
                            width=8, height=4).pack()
                    print(f"Error loading card {card}: {e}")
            
            # Show card back
            back_frame = tk.Frame(size_frame, relief=tk.RAISED, bd=1)
            back_frame.pack(pady=5)
            
            try:
                back_image = sprite_manager.get_card_back_image(w, h)
                back_label = tk.Label(back_frame, image=back_image, bd=0)
                back_label.image = back_image
                back_label.pack()
                
            except Exception as e:
                tk.Label(back_frame, text="Back Error", bg="red", fg="white",
                        width=8, height=4).pack()
                print(f"Error loading card back: {e}")
        
        # Add info
        info = tk.Label(root, text="Cards are now larger and higher quality!\nDefault size: 150x225 pixels", 
                       font=("Arial", 12), bg="#2C3E50", fg="lightgreen")
        info.pack(pady=20)
        
        print("✓ Final sprite test window created")
        print("  Cards should appear larger and sharper than before")
        print("  Window will auto-close in 5 seconds...")
        
        # Auto-close after 5 seconds
        root.after(5000, root.destroy)
        root.mainloop()
        
        print("✓ Final sprite test completed successfully!")
        
    except Exception as e:
        print(f"✗ Final test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_implementation()