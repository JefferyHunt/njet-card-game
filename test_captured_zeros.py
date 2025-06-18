#!/usr/bin/env python3

# Test captured 0s logic to ensure only opposing team 0s count
from enum import Enum

class Suit(Enum):
    RED = "Red"
    BLUE = "Blue"
    YELLOW = "Yellow"
    GREEN = "Green"

class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
    
    def __str__(self):
        return f"{self.value} of {self.suit.value}"

class Player:
    def __init__(self, name, team=None):
        self.name = name
        self.team = team
        self.captured_zeros = 0
        self.tricks_won = 0

def test_captured_zeros_logic():
    """Test captured 0s logic with various team scenarios"""
    print("=== TESTING CAPTURED 0s LOGIC ===")
    
    # Create test players
    players = [
        Player("Player 1", team=1),  # Team 1
        Player("Player 2", team=1),  # Team 1  
        Player("Player 3", team=2),  # Team 2
        Player("Player 4", team=2),  # Team 2
    ]
    
    print("Team assignments:")
    for i, p in enumerate(players):
        print(f"  Player {i}: {p.name}, Team {p.team}")
    
    # Test scenarios
    test_cases = [
        {
            "name": "Team 1 player wins, captures 0 from Team 2",
            "winner_idx": 0,  # Team 1
            "trick": [
                (0, Card(Suit.RED, 5)),    # Team 1 plays 5
                (1, Card(Suit.RED, 3)),    # Team 1 plays 3  
                (2, Card(Suit.RED, 0)),    # Team 2 plays 0 ← should be captured
                (3, Card(Suit.RED, 2)),    # Team 2 plays 2
            ],
            "expected_captured": 1
        },
        {
            "name": "Team 1 player wins, teammate's 0 in trick",
            "winner_idx": 0,  # Team 1
            "trick": [
                (0, Card(Suit.RED, 5)),    # Team 1 plays 5
                (1, Card(Suit.RED, 0)),    # Team 1 plays 0 ← should NOT be captured (same team)
                (2, Card(Suit.RED, 3)),    # Team 2 plays 3
                (3, Card(Suit.RED, 2)),    # Team 2 plays 2
            ],
            "expected_captured": 0
        },
        {
            "name": "Team 2 player wins, captures 0 from Team 1",
            "winner_idx": 2,  # Team 2
            "trick": [
                (0, Card(Suit.RED, 0)),    # Team 1 plays 0 ← should be captured
                (1, Card(Suit.RED, 3)),    # Team 1 plays 3
                (2, Card(Suit.RED, 5)),    # Team 2 plays 5  
                (3, Card(Suit.RED, 2)),    # Team 2 plays 2
            ],
            "expected_captured": 1
        },
        {
            "name": "Multiple 0s from opposing team",
            "winner_idx": 0,  # Team 1
            "trick": [
                (0, Card(Suit.RED, 5)),    # Team 1 plays 5
                (1, Card(Suit.RED, 3)),    # Team 1 plays 3
                (2, Card(Suit.RED, 0)),    # Team 2 plays 0 ← should be captured
                (3, Card(Suit.RED, 0)),    # Team 2 plays 0 ← should be captured
            ],
            "expected_captured": 2
        },
        {
            "name": "Mixed 0s - one from same team, one from opposing team",
            "winner_idx": 0,  # Team 1
            "trick": [
                (0, Card(Suit.RED, 5)),    # Team 1 plays 5
                (1, Card(Suit.RED, 0)),    # Team 1 plays 0 ← should NOT be captured (same team)
                (2, Card(Suit.RED, 0)),    # Team 2 plays 0 ← should be captured
                (3, Card(Suit.RED, 2)),    # Team 2 plays 2
            ],
            "expected_captured": 1
        }
    ]
    
    # Test each scenario
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: {test_case['name']}")
        
        # Reset captured zeros
        for p in players:
            p.captured_zeros = 0
        
        # Simulate the logic
        winner_idx = test_case["winner_idx"]
        trick = test_case["trick"]
        
        winner_team = players[winner_idx].team
        print(f"  Winner: Player {winner_idx} (Team {winner_team})")
        
        captured_count = 0
        for player_idx, card in trick:
            card_player_team = players[player_idx].team
            print(f"    Player {player_idx} (Team {card_player_team}) plays {card}")
            
            # Apply the fixed logic
            if (card.value == 0 and 
                winner_team is not None and 
                card_player_team is not None and
                card_player_team != winner_team):
                players[winner_idx].captured_zeros += 1
                captured_count += 1
                print(f"      → 0 captured from opposing team!")
            elif card.value == 0:
                print(f"      → 0 not captured (same team or invalid team)")
        
        # Check result
        actual = players[winner_idx].captured_zeros
        expected = test_case["expected_captured"]
        
        if actual == expected:
            print(f"  ✅ PASS: {actual} captured 0s (expected {expected})")
        else:
            print(f"  ❌ FAIL: {actual} captured 0s (expected {expected})")
    
    print("\n=== TESTING EDGE CASES ===")
    
    # Test with None teams
    edge_players = [
        Player("Player A", team=None),  # No team
        Player("Player B", team=1),     # Team 1
        Player("Player C", team=None),  # No team
        Player("Player D", team=2),     # Team 2
    ]
    
    print("Edge case: Players with None teams")
    for i, p in enumerate(edge_players):
        print(f"  Player {i}: {p.name}, Team {p.team}")
    
    edge_trick = [
        (0, Card(Suit.RED, 5)),    # None team plays 5
        (1, Card(Suit.RED, 0)),    # Team 1 plays 0
        (2, Card(Suit.RED, 0)),    # None team plays 0  
        (3, Card(Suit.RED, 2)),    # Team 2 plays 2
    ]
    
    # Test with winner having None team
    winner_idx = 0  # None team wins
    winner_team = edge_players[winner_idx].team
    print(f"\nWinner: Player {winner_idx} (Team {winner_team})")
    
    captured = 0
    for player_idx, card in edge_trick:
        card_player_team = edge_players[player_idx].team
        print(f"  Player {player_idx} (Team {card_player_team}) plays {card}")
        
        if (card.value == 0 and 
            winner_team is not None and 
            card_player_team is not None and
            card_player_team != winner_team):
            captured += 1
            print(f"    → 0 captured!")
        elif card.value == 0:
            print(f"    → 0 not captured (None team or same team)")
    
    print(f"Total captured by None team winner: {captured} (should be 0)")
    
    if captured == 0:
        print("✅ PASS: None team correctly captures 0 zeros")
    else:
        print("❌ FAIL: None team incorrectly captured zeros")
    
    print("\n=== ALL TESTS COMPLETE ===")

if __name__ == "__main__":
    test_captured_zeros_logic()