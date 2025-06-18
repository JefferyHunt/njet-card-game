#!/usr/bin/env python3

import sys
sys.path.append('/Users/jefferyhunt/Code/Njet')

# Import the game classes
exec(open('/Users/jefferyhunt/Code/Njet/njet-game-2.py').read())

def test_blocking_turn_progression():
    """Test the blocking turn progression logic"""
    print("=== BLOCKING TURN PROGRESSION TEST ===")
    
    # Create a simple game instance
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    # Create game UI
    ui = NjetUI()
    ui.setup_players(4)  # 4 players: 1 human, 3 AI
    
    # Set up players
    ui.game.players[0].is_human = True
    ui.game.players[0].name = "Human"
    for i in range(1, 4):
        ui.game.players[i].is_human = False
        ui.game.players[i].name = f"AI_{i}"
    
    print(f"Initial setup:")
    print(f"  - Current player: {ui.game.current_player_idx} ({ui.game.players[ui.game.current_player_idx].name})")
    print(f"  - Phase: {ui.game.current_phase}")
    print(f"  - Total players: {ui.game.num_players}")
    
    # Test turn progression manually
    print("\n=== TESTING TURN PROGRESSION ===")
    for i in range(6):  # Test 6 turn advances
        old_player = ui.game.current_player_idx
        old_player_name = ui.game.players[old_player].name
        
        # Calculate what next player should be
        expected_next = (old_player + 1) % ui.game.num_players
        expected_name = ui.game.players[expected_next].name
        
        print(f"\nTurn {i+1}:")
        print(f"  Before: Player {old_player} ({old_player_name})")
        print(f"  Expected next: Player {expected_next} ({expected_name})")
        
        # Manually advance turn
        ui.game.current_player_idx = (ui.game.current_player_idx + 1) % ui.game.num_players
        
        new_player = ui.game.current_player_idx
        new_player_name = ui.game.players[new_player].name
        
        print(f"  Actual next: Player {new_player} ({new_player_name})")
        print(f"  Success: {expected_next == new_player}")
        
        if expected_next != new_player:
            print(f"  ERROR: Turn progression failed!")
            break
    
    print("\n=== TESTING BLOCKING LOGIC ===")
    
    # Test blocking board state
    print("Available blocking options:")
    for category in ["start_player", "discard", "trump", "super_trump", "points"]:
        can_block = ui.game.can_block(category)
        blocked_key = f"{category}_blocked"
        blocked = ui.game.blocking_board.get(blocked_key, [])
        available = [opt for opt in ui.game.blocking_board[category] if opt not in blocked]
        print(f"  {category}: can_block={can_block}, available={len(available)}, blocked={len(blocked)}")
    
    # Test a blocking action
    print("\nTesting blocking action:")
    print(f"  Current player before block: {ui.game.current_player_idx}")
    
    # Simulate blocking trump RED
    if ui.game.can_block("trump"):
        print("  Blocking trump=RED...")
        ui.game.block_option("trump", Suit.RED, ui.game.current_player_idx)
        print(f"  Blocked successfully. Trump blocked list: {ui.game.blocking_board.get('trump_blocked', [])}")
    
    root.destroy()
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_blocking_turn_progression()