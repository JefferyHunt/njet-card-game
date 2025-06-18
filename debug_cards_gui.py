#!/usr/bin/env python3

# Minimal test to debug card display issue
import tkinter as tk
import importlib.util

# Import the game classes
spec = importlib.util.spec_from_file_location("njet_game", "njet-game-2.py")
njet_game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(njet_game)

class CardTestGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Card Display Test")
        self.root.geometry("800x600")
        self.root.configure(bg="#2C3E50")
        
        # Create a game to get cards
        self.game = njet_game.NjetGame(4)
        for i in range(4):
            self.game.players[i].name = f"Player {i+1}"
            self.game.players[i].is_human = (i == 0)
        self.game.deal_cards()
        
        # Create GUI components
        self.gui = njet_game.NjetGUI(self.root)
        self.gui.game = self.game
        
        # Test card display
        self.test_card_display()
    
    def test_card_display(self):
        print("Testing card display...")
        
        # Clear any existing content
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create test area
        test_frame = tk.Frame(self.root, bg="purple")
        test_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        tk.Label(test_frame, text="CARD DISPLAY TEST", 
                font=("Arial", 16, "bold"), bg="purple", fg="white").pack(pady=10)
        
        # Test individual card creation
        human_player = self.game.players[0]
        print(f"Human player has {len(human_player.cards)} cards")
        
        if len(human_player.cards) > 0:
            card = human_player.cards[0]
            print(f"Creating widget for card: {card}")
            
            card_widget = self.gui.create_card_widget(test_frame, card)
            card_widget.pack(pady=10)
            
            tk.Label(test_frame, text=f"Card: {card}", 
                    font=("Arial", 12), bg="purple", fg="white").pack()
        
        # Test player area display
        player_area_test = tk.Frame(test_frame, bg="green", height=100)
        player_area_test.pack(fill=tk.X, pady=10)
        
        tk.Label(player_area_test, text="PLAYER AREA TEST", 
                font=("Arial", 12, "bold"), bg="green", fg="white").pack()
        
        # Test calling show_player_cards
        print("Calling show_player_cards...")
        try:
            # Create the player area if not exists
            self.gui.player_area = player_area_test
            self.gui.show_player_cards()
            print("show_player_cards completed")
        except Exception as e:
            print(f"Error in show_player_cards: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    test = CardTestGUI()
    test.run()