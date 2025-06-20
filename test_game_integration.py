#!/usr/bin/env python3
"""Test integration of sprite sheets in main game"""

import tkinter as tk
import sys
import os

# Add current directory to path
sys.path.append('.')

# Import classes from main game file
try:
    # Read and execute the main game file to get classes
    with open('njet-game-2.py', 'r') as f:
        game_code = f.read()
    
    # Create a namespace to execute the code
    game_namespace = {}
    exec(game_code, game_namespace)
    
    # Extract the classes we need
    CardSpriteManager = game_namespace['CardSpriteManager']
    Suit = game_namespace['Suit'] 
    Card = game_namespace['Card']
    
    print("✓ Successfully imported game classes")
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def test_gui_integration():
    """Test that the GUI can load and display cards with sprite sheet"""
    
    # Create a minimal test
    root = tk.Tk()
    root.title("Game Integration Test")
    root.geometry("800x600")
    
    try:
        # Test sprite manager creation
        sprite_manager = CardSpriteManager("CardSpriteSheet.png")
        print("✓ Sprite manager created successfully")
        
        # Test GUI creation (partial - just the sprite loading part)
        gui = NjetGUI(root)
        if gui.sprite_manager:
            print("✓ GUI has sprite manager loaded")
            
            # Test card widget creation
            test_card = Card(Suit.RED, 5)
            test_frame = tk.Frame(root)
            test_frame.pack(pady=20)
            
            # Create a card widget using the GUI method
            card_widget = gui.create_card_widget(test_frame, test_card)
            card_widget.pack()
            
            print("✓ Card widget created successfully with sprite")
            
            # Test card back
            back_frame = tk.Frame(root)
            back_frame.pack(pady=20)
            
            back_widget = gui.create_card_back(back_frame)
            back_widget.pack()
            
            print("✓ Card back widget created successfully")
            
        else:
            print("✗ GUI does not have sprite manager")
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Show briefly then close
    root.after(3000, root.destroy)
    root.mainloop()
    
    print("✓ GUI integration test completed successfully")
    return True

if __name__ == "__main__":
    test_gui_integration()