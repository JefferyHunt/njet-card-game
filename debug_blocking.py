#!/usr/bin/env python3

# Test the blocking logic without GUI
import sys
sys.path.append('/Users/jefferyhunt/Code/Njet')

from enum import Enum

class Phase(Enum):
    BLOCKING = "Blocking"
    TEAM_SELECTION = "Team Selection"
    DISCARD = "Discard"
    TRICK_TAKING = "Trick Taking"
    ROUND_END = "Round End"

class Suit(Enum):
    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"

class Player:
    def __init__(self, name: str, is_human: bool = False):
        self.name = name
        self.is_human = is_human
        self.cards = []
        self.team = None
        self.total_score = 0
        self.sort_by_suit_first = True

class NjetGame:
    def __init__(self, num_players: int):
        self.num_players = num_players
        self.players = []
        self.current_phase = Phase.BLOCKING
        self.current_player_idx = 0
        self.blocking_board = self.init_blocking_board()
        self.game_params = {}

    def init_blocking_board(self):
        """Initialize the blocking board with all options"""
        board = {
            "start_player": list(range(self.num_players)),
            "discard": ["0 cards", "1 card", "2 cards", "2 non-zeros", "Pass 2 right"],
            "trump": [suit for suit in Suit],
            "points": [1, 2, 3, 4, 5]
        }
        if self.num_players >= 4:
            board["super_trump"] = [suit for suit in Suit]
        return board

    def can_block(self, category: str) -> bool:
        """Check if there are still unblocked options in a category"""
        available = [opt for opt in self.blocking_board[category] 
                    if opt not in self.blocking_board.get(f"{category}_blocked", [])]
        return len(available) > 1

    def block_option(self, category: str, option):
        """Block an option on the board"""
        blocked_key = f"{category}_blocked"
        if blocked_key not in self.blocking_board:
            self.blocking_board[blocked_key] = []
        self.blocking_board[blocked_key].append(option)

def test_blocking_logic():
    """Test the core blocking logic"""
    print("Testing blocking logic...")
    
    # Create game with 4 players
    game = NjetGame(4)
    
    # Add players
    game.players = [
        Player("Human", True),
        Player("AI 1", False),
        Player("AI 2", False),
        Player("AI 3", False)
    ]
    
    print(f"Initial state:")
    print(f"  Current player: {game.current_player_idx} ({game.players[game.current_player_idx].name})")
    print(f"  Phase: {game.current_phase}")
    
    # Check initial blocking state
    for category in ["start_player", "discard", "trump", "super_trump", "points"]:
        if category in game.blocking_board:
            print(f"  {category}: can_block = {game.can_block(category)}")
    
    print("\nSimulating human player blocking 'trump' = 'SPADES'...")
    
    # Simulate human player blocking trump spades
    game.block_option("trump", Suit.SPADES)
    
    print(f"After blocking:")
    for category in ["start_player", "discard", "trump", "super_trump", "points"]:
        if category in game.blocking_board:
            blocked = game.blocking_board.get(f"{category}_blocked", [])
            available = [opt for opt in game.blocking_board[category] if opt not in blocked]
            print(f"  {category}: {len(available)} available, {len(blocked)} blocked, can_block = {game.can_block(category)}")
    
    # Check total blockable
    total_blockable = sum(1 for category in ["start_player", "discard", "trump", "super_trump", "points"]
                         if game.can_block(category))
    print(f"\nTotal blockable categories: {total_blockable}")
    
    # Simulate advancing to next player (AI)
    print(f"\nAdvancing to next player...")
    game.current_player_idx = (game.current_player_idx + 1) % game.num_players
    print(f"  New current player: {game.current_player_idx} ({game.players[game.current_player_idx].name})")
    print(f"  Is AI: {not game.players[game.current_player_idx].is_human}")

if __name__ == "__main__":
    test_blocking_logic()