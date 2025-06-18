#!/usr/bin/env python3

# Test just the AI sorting fix without GUI
from enum import Enum

class Suit(Enum):
    RED = "Red"
    BLUE = "Blue"
    YELLOW = "Yellow"
    GREEN = "Green"

def test_suit_sorting():
    """Test that Suit objects can be sorted in option_scores"""
    print("=== TESTING SUIT SORTING FIX ===")
    
    # Simulate the problematic option_scores list
    option_scores = [
        (0.8, "trump", Suit.RED),
        (0.6, "super_trump", Suit.BLUE),
        (0.8, "trump", Suit.YELLOW),  # Same score as first item
        (0.9, "points", "2"),
        (0.7, "discard", "1 card")
    ]
    
    print("Original option_scores:")
    for score, category, option in option_scores:
        print(f"  {score:.1f}: {category} = {option}")
    
    try:
        # This would fail with the old sort method
        # option_scores.sort(reverse=True)  # OLD WAY - FAILS
        
        # New way - only compare scores
        option_scores.sort(key=lambda x: x[0], reverse=True)
        
        print("\nSorted option_scores (by score only):")
        for score, category, option in option_scores:
            print(f"  {score:.1f}: {category} = {option}")
        
        print("\n✅ SUCCESS: Suit sorting fix works!")
        return True
        
    except TypeError as e:
        print(f"\n❌ FAILURE: {e}")
        return False

def test_old_method():
    """Test the old method to confirm it fails"""
    print("\n=== TESTING OLD METHOD (should fail) ===")
    
    option_scores = [
        (0.8, "trump", Suit.RED),
        (0.8, "trump", Suit.YELLOW),  # Same score, different Suit
    ]
    
    try:
        option_scores.sort(reverse=True)  # This should fail
        print("❌ UNEXPECTED: Old method didn't fail")
        return False
    except TypeError as e:
        print(f"✅ EXPECTED FAILURE: {e}")
        return True

if __name__ == "__main__":
    test_suit_sorting()
    test_old_method()
    print("\n=== ALL TESTS COMPLETE ===")