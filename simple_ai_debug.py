#!/usr/bin/env python3

# Simple test of AI blocking logic without GUI dependencies
import random
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

class Player:
    def __init__(self, name, is_human=False):
        self.name = name
        self.is_human = is_human
        self.cards = []

def create_deck():
    """Create a simple deck for testing"""
    deck = []
    for suit in Suit:
        for value in range(10):  # 0-9
            for _ in range(3):  # 3 of each
                deck.append(Card(suit, value))
    return deck

def ai_evaluate_blocking_option(player, category, option):
    """Simplified AI evaluation"""
    if category == "trump":
        # Prefer to block suits we're weak in
        suit_cards = [c for c in player.cards if c.suit == option]
        if len(suit_cards) < 3:  # Few cards in this suit
            return 0.8  # High score to block it
        else:
            return 0.2  # Low score, don't block our strong suit
    elif category == "points":
        # Prefer higher point values
        try:
            points_val = int(option) if str(option).lstrip('-').isdigit() else 1
            return min(1.0, (points_val + 3) / 6)  # Normalize to 0-1
        except:
            return 0.5
    else:
        return random.uniform(0.3, 0.7)  # Random score for other categories

def test_ai_blocking_simple():
    """Test AI blocking with simplified logic"""
    print("=== SIMPLE AI BLOCKING TEST ===")
    
    # Create a player with some cards
    player = Player("AI_1", False)
    deck = create_deck()
    random.shuffle(deck)
    player.cards = deck[:15]  # Give them 15 cards
    
    print(f"Player {player.name} has {len(player.cards)} cards")
    
    # Show card distribution by suit
    for suit in Suit:
        suit_cards = [c for c in player.cards if c.suit == suit]
        print(f"  {suit.value}: {len(suit_cards)} cards")
    
    # Simulate blocking board
    blocking_board = {
        "start_player": [0, 1, 2, 3],
        "discard": ["0 cards", "1 card", "2 cards", "2 non-zeros", "Pass 2 right"],
        "trump": [Suit.RED, Suit.BLUE, Suit.YELLOW, Suit.GREEN, "Njet"],
        "super_trump": [Suit.RED, Suit.BLUE, Suit.YELLOW, Suit.GREEN, "Njet"],
        "points": ["-2", "1", "2", "3", "4"]
    }
    
    # Test evaluation and sorting
    option_scores = []
    
    print("\nEvaluating blocking options:")
    for category in ["start_player", "discard", "trump", "super_trump", "points"]:
        blocked = blocking_board.get(f"{category}_blocked", [])
        available = [opt for opt in blocking_board[category] if opt not in blocked]
        
        if len(available) > 1:  # Can only block if more than 1 option remains
            print(f"  {category}: {len(available)} options available")
            for option in available:
                score = ai_evaluate_blocking_option(player, category, option)
                option_scores.append((score, category, option))
                print(f"    {option}: {score:.2f}")
    
    print(f"\nTotal options to evaluate: {len(option_scores)}")
    
    if option_scores:
        # Test sorting (the key fix)
        print("\nTesting sort with key=lambda...")
        try:
            option_scores.sort(key=lambda x: x[0], reverse=True)
            print("✅ Sort successful!")
            
            print("\nTop 5 options:")
            for i, (score, category, option) in enumerate(option_scores[:5]):
                print(f"  {i+1}. {score:.2f}: {category} = {option}")
            
            # Simulate AI choice
            top_options = option_scores[:min(3, len(option_scores))]
            choice_score, choice_category, choice_option = random.choice(top_options)
            print(f"\n✅ AI would block: {choice_category} = {choice_option} (score: {choice_score:.2f})")
            
        except Exception as e:
            print(f"❌ Sort failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ No blockable options found")
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_ai_blocking_simple()