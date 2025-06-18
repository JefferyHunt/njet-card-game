#!/usr/bin/env python3
import sys
sys.path.append('.')

# Import the game classes
import importlib.util
spec = importlib.util.spec_from_file_location("njet_game", "njet-game-2.py")
njet_game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(njet_game)
NjetGame = njet_game.NjetGame
Suit = njet_game.Suit
Card = njet_game.Card

def test_card_dealing():
    print("Testing card dealing...")
    
    # Create a game
    game = NjetGame(4)
    
    # Set player names
    for i in range(4):
        game.players[i].name = f"Player {i+1}"
        game.players[i].is_human = (i == 0)  # First player is human
    
    print(f"Created game with {len(game.players)} players")
    
    # Deal cards
    game.deal_cards()
    
    print("Cards dealt:")
    for i, player in enumerate(game.players):
        print(f"  {player.name}: {len(player.cards)} cards, human={player.is_human}")
        if player.is_human and len(player.cards) > 0:
            print(f"    First few cards: {[str(c) for c in player.cards[:5]]}")
    
    # Test card creation
    test_card = Card(Suit.RED, 7)
    print(f"Test card created: {test_card}")

if __name__ == "__main__":
    test_card_dealing()