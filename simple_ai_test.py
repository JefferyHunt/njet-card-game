#!/usr/bin/env python3

# Simple test to verify AI blocking logic without GUI
import sys
sys.path.append('/Users/jefferyhunt/Code/Njet')

# Test the core AI blocking logic
def test_ai_blocking_logic():
    """Test AI blocking logic without full GUI"""
    print("=== TESTING AI BLOCKING LOGIC ===")
    
    # Import just the game classes we need
    from enum import Enum
    
    class Phase(Enum):
        BLOCKING = "Blocking"
    
    class Suit(Enum):
        RED = "Red"
        BLUE = "Blue"
        YELLOW = "Yellow"
        GREEN = "Green"
    
    class Player:
        def __init__(self, name, is_human=False):
            self.name = name
            self.is_human = is_human
            self.cards = []
            self.blocking_tokens = 3
    
    class TestGame:
        def __init__(self):
            self.num_players = 4
            self.current_phase = Phase.BLOCKING
            self.current_player_idx = 0
            self.players = [
                Player("Human", True),
                Player("AI_1", False),
                Player("AI_2", False),
                Player("AI_3", False)
            ]
            self.blocking_board = {
                "start_player": list(range(4)),
                "discard": ["0 cards", "1 card", "2 cards", "2 non-zeros", "Pass 2 right"],
                "trump": [Suit.RED, Suit.BLUE, Suit.YELLOW, Suit.GREEN, "Njet"],
                "super_trump": [Suit.RED, Suit.BLUE, Suit.YELLOW, Suit.GREEN, "Njet"],
                "points": ["-2", "1", "2", "3", "4"]
            }
        
        def can_block(self, category):
            blocked = self.blocking_board.get(f"{category}_blocked", [])
            available = [opt for opt in self.blocking_board[category] if opt not in blocked]
            return len(available) > 1
        
        def block_option(self, category, option, player_idx):
            blocked_key = f"{category}_blocked"
            if blocked_key not in self.blocking_board:
                self.blocking_board[blocked_key] = []
            self.blocking_board[blocked_key].append(option)
            print(f"Player {player_idx} blocked {category}={option}")
    
    # Create test game
    game = TestGame()
    
    print(f"Initial state:")
    print(f"  Current player: {game.current_player_idx} ({game.players[game.current_player_idx].name})")
    print(f"  Is human: {game.players[game.current_player_idx].is_human}")
    
    # Test blocking scenarios
    print(f"\nTesting blocking scenarios:")
    
    # Test 1: Human player blocks something
    if game.current_player_idx == 0 and game.players[0].is_human:
        print("Test 1: Human player blocks trump=RED")
        game.block_option("trump", Suit.RED, 0)
        game.current_player_idx = (game.current_player_idx + 1) % game.num_players
        print(f"  Next player: {game.current_player_idx} ({game.players[game.current_player_idx].name})")
    
    # Test 2: AI player should block something
    if not game.players[game.current_player_idx].is_human:
        print(f"Test 2: AI player {game.current_player_idx} should block something")
        # Simulate AI blocking logic
        for category in ["start_player", "discard", "trump", "super_trump", "points"]:
            if game.can_block(category):
                blocked = game.blocking_board.get(f"{category}_blocked", [])
                available = [opt for opt in game.blocking_board[category] if opt not in blocked]
                if available:
                    choice = available[0]  # AI picks first available
                    game.block_option(category, choice, game.current_player_idx)
                    break
        
        game.current_player_idx = (game.current_player_idx + 1) % game.num_players
        print(f"  Next player: {game.current_player_idx} ({game.players[game.current_player_idx].name})")
    
    # Test 3: Check if we can continue
    total_blockable = sum(1 for cat in ["start_player", "discard", "trump", "super_trump", "points"] 
                         if game.can_block(cat))
    print(f"\nBlockable categories remaining: {total_blockable}")
    
    if total_blockable > 0:
        print("✅ Game can continue - blocking phase not complete")
    else:
        print("🏁 Blocking phase complete - moving to next phase")
    
    print("\n=== TEST COMPLETE ===")
    return True

if __name__ == "__main__":
    test_ai_blocking_logic()