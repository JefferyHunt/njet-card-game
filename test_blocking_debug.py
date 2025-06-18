#!/usr/bin/env python3

import sys
import tkinter as tk

# Import the classes directly from the file
sys.path.append('/Users/jefferyhunt/Code/Njet')
exec(open('/Users/jefferyhunt/Code/Njet/njet-game-2.py').read())

def test_blocking_turn_logic():
    """Test the blocking turn logic with debug output"""
    
    print("Starting Njet game with debug logging...")
    
    # Create a tkinter root
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Create the game UI
    ui = NjetUI()
    
    # Setup 4 players: Human, AI, AI, AI
    ui.setup_players(4)
    
    # Set player types manually
    ui.game.players[0].is_human = True
    ui.game.players[0].name = "Human Player"
    ui.game.players[1].is_human = False
    ui.game.players[1].name = "AI Player 1"
    ui.game.players[2].is_human = False
    ui.game.players[2].name = "AI Player 2"
    ui.game.players[3].is_human = False
    ui.game.players[3].name = "AI Player 3"
    
    print("Players setup:")
    for i, player in enumerate(ui.game.players):
        print(f"  Player {i}: {player.name} ({'Human' if player.is_human else 'AI'})")
    
    print(f"\nInitial current_player_idx: {ui.game.current_player_idx}")
    print(f"Initial phase: {ui.game.current_phase}")
    
    # Show the blocking phase
    ui.update_display()
    
    print("\nBlocking board state:")
    for category in ["start_player", "discard", "trump", "super_trump", "points"]:
        blocked = ui.game.blocking_board.get(f"{category}_blocked", [])
        available = [opt for opt in ui.game.blocking_board[category] if opt not in blocked]
        print(f"  {category}: {len(available)} available, {len(blocked)} blocked")
        print(f"    Can block: {ui.game.can_block(category)}")
    
    # Don't start the main loop, just show setup info
    print("\nGame setup complete. Debug logging active.")
    
    # If you want to run the UI for testing, uncomment the next line:
    # root.mainloop()
    
    root.destroy()

if __name__ == "__main__":
    test_blocking_turn_logic()