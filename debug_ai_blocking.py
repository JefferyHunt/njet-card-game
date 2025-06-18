#!/usr/bin/env python3

# Debug the AI blocking by running the blocking logic directly
import sys
import random
sys.path.append('/Users/jefferyhunt/Code/Njet')

# Import what we need
exec(open('/Users/jefferyhunt/Code/Njet/njet-game-2.py').read())

def debug_ai_blocking():
    """Debug AI blocking logic step by step"""
    print("=== DEBUGGING AI BLOCKING LOGIC ===")
    
    # Create a minimal game instance
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create game and UI
        game = NjetGame(4)
        
        # Set up players: 1 human, 3 AI
        game.players[0].name = "Human"
        game.players[0].is_human = True
        for i in range(1, 4):
            game.players[i].name = f"AI_{i}"
            game.players[i].is_human = False
        
        # Deal cards so AI has something to evaluate
        game.deal_cards()
        
        print("Initial state:")
        for i, player in enumerate(game.players):
            print(f"  Player {i}: {player.name} ({'Human' if player.is_human else 'AI'}), {len(player.cards)} cards")
        
        print(f"Current player: {game.current_player_idx}")
        print(f"Phase: {game.current_phase}")
        
        # Test AI blocking evaluation for player 1 (first AI)
        player_idx = 1
        print(f"\nTesting AI blocking for player {player_idx} ({game.players[player_idx].name}):")
        
        # Check available options
        option_scores = []
        for category in ["start_player", "discard", "trump", "super_trump", "points"]:
            if game.can_block(category):
                blocked = game.blocking_board.get(f"{category}_blocked", [])
                available = [opt for opt in game.blocking_board[category] if opt not in blocked]
                print(f"  {category}: {len(available)} available options: {available}")
                
                if len(available) > 1:
                    for option in available:
                        try:
                            score = game.ai_evaluate_blocking_option(player_idx, category, option)
                            option_scores.append((score, category, option))
                            print(f"    {option}: score = {score:.2f}")
                        except Exception as e:
                            print(f"    {option}: ERROR evaluating - {e}")
        
        print(f"\nTotal blockable options: {len(option_scores)}")
        
        if option_scores:
            # Test sorting
            print("\nTesting sort...")
            try:
                option_scores.sort(key=lambda x: x[0], reverse=True)
                print("✅ Sort successful!")
                
                print("Sorted options:")
                for score, category, option in option_scores:
                    print(f"  {score:.2f}: {category} = {option}")
                
                # Test AI choice logic
                print("\nTesting AI choice...")
                strategy = game.ai_strategies[player_idx]
                print(f"Risk tolerance: {strategy['risk_tolerance']:.2f}")
                
                # Simulate choice
                if random.random() < strategy['risk_tolerance']:
                    top_options = option_scores[:min(3, len(option_scores))]
                    score, category, option = random.choice(top_options)
                    print(f"✅ AI would choose (top 3): {category} = {option} (score: {score:.2f})")
                else:
                    score, category, option = random.choice(option_scores)
                    print(f"✅ AI would choose (random): {category} = {option} (score: {score:.2f})")
                
            except Exception as e:
                print(f"❌ Sort failed: {e}")
        else:
            print("❌ No blockable options found!")
        
    finally:
        root.destroy()
    
    print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_ai_blocking()