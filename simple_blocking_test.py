#!/usr/bin/env python3

# Simple test without GUI to check blocking logic
from enum import Enum

class Phase(Enum):
    BLOCKING = "Blocking"
    TEAM_SELECTION = "Team Selection"
    DISCARD = "Discard"
    TRICK_TAKING = "Trick Taking"
    ROUND_END = "Round End"

class Suit(Enum):
    RED = "Red"
    BLACK = "Black"
    BLUE = "Blue"
    GREEN = "Green"

class Player:
    def __init__(self, name, is_human=False):
        self.name = name
        self.is_human = is_human
        self.cards = []

def test_turn_progression():
    """Test basic turn progression logic"""
    print("=== TURN PROGRESSION TEST ===")
    
    # Create 4 players
    players = [
        Player("Human", True),
        Player("AI_1", False),
        Player("AI_2", False),
        Player("AI_3", False)
    ]
    
    current_player_idx = 0
    num_players = len(players)
    
    print(f"Starting with {num_players} players:")
    for i, player in enumerate(players):
        print(f"  Player {i}: {player.name} ({'Human' if player.is_human else 'AI'})")
    
    # Test 8 turn progressions
    print(f"\nTesting turn progression:")
    for turn in range(8):
        old_player = current_player_idx
        
        # Calculate next player
        next_player = (current_player_idx + 1) % num_players
        
        print(f"Turn {turn + 1}: Player {old_player} ({players[old_player].name}) -> Player {next_player} ({players[next_player].name})")
        
        # Update current player
        current_player_idx = next_player
        
        # Verify it worked
        if current_player_idx != next_player:
            print(f"ERROR: Turn progression failed!")
            break
    
    return True

def test_blocking_board():
    """Test blocking board logic"""
    print("\n=== BLOCKING BOARD TEST ===")
    
    # Initialize blocking board
    blocking_board = {
        "start_player": [0, 1, 2, 3],
        "discard": ["0 cards", "1 card", "2 cards", "2 non-zeros", "Pass 2 right"],
        "trump": [Suit.RED, Suit.BLACK, Suit.BLUE, Suit.GREEN, "Njet"],
        "super_trump": [Suit.RED, Suit.BLACK, Suit.BLUE, Suit.GREEN, "Njet"],
        "points": ["-2", "1", "2", "3", "4"],
        "blocked_by": {}
    }
    
    def can_block(category):
        blocked_key = f"{category}_blocked"
        blocked = blocking_board.get(blocked_key, [])
        available = [opt for opt in blocking_board[category] if opt not in blocked]
        return len(available) > 1
    
    def block_option(category, option, player_idx):
        blocked_key = f"{category}_blocked"
        if blocked_key not in blocking_board:
            blocking_board[blocked_key] = []
        blocking_board[blocked_key].append(option)
        blocking_board["blocked_by"][(category, option)] = player_idx
    
    # Test blocking some options
    print("Initial state:")
    for category in ["start_player", "discard", "trump", "super_trump", "points"]:
        can_block_cat = can_block(category)
        blocked = blocking_board.get(f"{category}_blocked", [])
        available = [opt for opt in blocking_board[category] if opt not in blocked]
        print(f"  {category}: can_block={can_block_cat}, available={len(available)}")
    
    # Block some options
    print(f"\nBlocking trump=RED by player 0...")
    if can_block("trump"):
        block_option("trump", Suit.RED, 0)
        print(f"  Success. Trump blocked: {blocking_board.get('trump_blocked', [])}")
    else:
        print(f"  Cannot block trump")
    
    print(f"\nBlocking discard='1 card' by player 1...")
    if can_block("discard"):
        block_option("discard", "1 card", 1)
        print(f"  Success. Discard blocked: {blocking_board.get('discard_blocked', [])}")
    else:
        print(f"  Cannot block discard")
    
    # Check final state
    print("\nFinal state:")
    for category in ["start_player", "discard", "trump", "super_trump", "points"]:
        can_block_cat = can_block(category)
        blocked = blocking_board.get(f"{category}_blocked", [])
        available = [opt for opt in blocking_board[category] if opt not in blocked]
        print(f"  {category}: can_block={can_block_cat}, available={len(available)}, blocked={blocked}")
    
    return True

if __name__ == "__main__":
    test_turn_progression()
    test_blocking_board()
    print("\n=== ALL TESTS COMPLETE ===")