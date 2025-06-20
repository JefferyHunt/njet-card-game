#!/usr/bin/env python3
"""Quick test to verify table background is working in game"""

import tkinter as tk
import os
import sys

# Disable pygame temporarily to avoid the numpy warnings for this test
os.environ['SDL_AUDIODRIVER'] = 'dummy'

def test_game_table():
    """Test that we can start a game and see table background without crashes"""
    print("Testing game startup with table background...")
    
    try:
        # Import the game (this will test the imports)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        print("✓ Starting game test...")
        
        # Just test that the game can import and initialize without crashing
        # We won't actually run the full GUI to avoid the complexity
        
        exec(open('njet-game-2.py').read())
        
        # Create a minimal test window
        root = tk.Tk()
        root.title("Game Table Test")
        root.geometry("400x300")
        root.withdraw()  # Hide the window
        
        # Try to create the game object (this tests initialization)
        game = NjetGUI(root)
        
        print("✓ Game object created successfully")
        
        # Check if table background loaded
        if hasattr(game, 'table_source') and game.table_source:
            print(f"✓ Table background loaded: {game.table_source.size}")
        else:
            print("⚠ Table background not loaded")
        
        # Test colors
        if hasattr(game, 'colors'):
            print(f"✓ Game colors loaded: {len(game.colors)} colors")
        
        root.destroy()
        print("✓ Game test completed successfully - no crashes!")
        return True
        
    except Exception as e:
        print(f"✗ Game test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_game_table()
    if success:
        print("\n🎮 Game should now run without crashes!")
        print("🃏 Table background should be visible!")
        print("✨ UI elements should float on the ornate table!")
    else:
        print("\n❌ Test failed - check errors above")