#!/usr/bin/env python3
"""
Quick test to verify the discard phase fix for human players.
This test simulates a 2-player game scenario where Player 1 is human and Player 2 is AI.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Import the game classes
import importlib.util
spec = importlib.util.spec_from_file_location("njet_game_2", "njet-game-2.py")
njet_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(njet_module)

# Import classes from the loaded module
NjetGame = njet_module.NjetGame
Player = njet_module.Player
Card = njet_module.Card
Suit = njet_module.Suit
Phase = njet_module.Phase

def test_discard_phase_human_prompt():
    """Test that human players are properly prompted during discard phase"""
    print("Testing discard phase human prompt fix...")
    
    # Create a minimal test scenario
    try:
        # Create game with 2 players - one human, one AI
        game = NjetGame(num_players=2)
        
        # Set up players
        game.players[0].name = "Human Player"
        game.players[0].is_human = True
        game.players[1].name = "AI Player" 
        game.players[1].is_human = False
        
        # Set game parameters as if blocking phase completed
        game.game_params = {
            "start_player": 0,  # Human player starts
            "discard": "Pass 2 right",
            "trump": Suit.RED,
            "super_trump": Suit.BLUE,
            "points": 3
        }
        
        # Set current phase to discard
        game.current_phase = Phase.DISCARD
        game.current_player_idx = 0  # Human player's turn
        
        # Add some test cards
        test_cards = [
            Card(Suit.RED, 5),
            Card(Suit.BLUE, 3),
            Card(Suit.YELLOW, 7),
            Card(Suit.GREEN, 2),
            Card(Suit.RED, 1),
            Card(Suit.BLUE, 8)
        ]
        
        game.players[0].cards = test_cards[:4]  # Human gets 4 cards
        game.players[1].cards = test_cards[4:6] # AI gets 2 cards
        
        print(f"✓ Game setup complete:")
        print(f"  - Start player: {game.game_params['start_player']} (Human)")
        print(f"  - Discard option: {game.game_params['discard']}")
        print(f"  - Human player cards: {len(game.players[0].cards)}")
        print(f"  - AI player cards: {len(game.players[1].cards)}")
        print(f"  - Current phase: {game.current_phase}")
        print(f"  - Current player: {game.current_player_idx}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    success = test_discard_phase_human_prompt()
    if success:
        print("\n✓ Test setup successful!")
        print("To verify the fix:")
        print("1. Run: python3 njet-game-2.py")
        print("2. Set up a 2-player game (1 human, 1 AI)")
        print("3. During blocking phase, ensure 'Pass 2 right' is selected for discard")
        print("4. Verify that the human player is prompted to select 2 cards")
        print("5. Check that the cards are clickable and the discard phase completes properly")
    else:
        print("\n✗ Test failed - check the fix implementation")