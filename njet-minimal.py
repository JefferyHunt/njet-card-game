#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from enum import Enum

class Phase(Enum):
    BLOCKING = "Blocking"

class MinimalNjetGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Minimal Njet Test")
        self.root.geometry("800x600")
        self.root.configure(bg="#2C3E50")
        
        # Start with player selection
        self.show_player_selection()
    
    def show_player_selection(self):
        """Show player count selection screen"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = tk.Frame(self.root, bg="#2C3E50")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        tk.Label(main_frame, text="NJET TEST", 
                font=('Arial', 24, 'bold'), bg="#2C3E50", fg="white").pack(pady=20)
        
        tk.Button(main_frame, text="Start 4 Player Game", 
                 font=('Arial', 14), command=self.start_test_game,
                 width=20, height=2).pack(pady=20)
    
    def start_test_game(self):
        """Start a test game"""
        print("Starting test game...")
        self.setup_test_ui()
    
    def setup_test_ui(self):
        """Setup test UI"""
        print("Setting up test UI...")
        
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create simple layout
        main_container = tk.Frame(self.root, bg="#2C3E50")
        main_container.pack(expand=True, fill=tk.BOTH)
        
        # Top area
        top_frame = tk.Frame(main_container, bg="#34495E", height=100)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        top_frame.pack_propagate(False)
        
        tk.Label(top_frame, text="Round 1 - Phase: Blocking", 
                font=('Arial', 16), bg="#34495E", fg="white").pack(pady=30)
        
        # Game area
        game_area = tk.Frame(main_container, bg="#2C3E50")
        game_area.pack(expand=True, fill=tk.BOTH, padx=10)
        
        # Show blocking phase
        self.show_test_blocking(game_area)
        
        print("Test UI setup complete")
    
    def show_test_blocking(self, parent):
        """Show test blocking phase"""
        print("Showing test blocking phase...")
        
        # Title
        tk.Label(parent, text="BLOCKING PHASE", 
                font=('Arial', 24, 'bold'), bg="#2C3E50", fg="#F1C40F").pack(pady=30)
        
        # Instructions
        tk.Label(parent, text="Player 1, choose ONE option to block", 
                font=('Arial', 16), bg="#2C3E50", fg="white").pack(pady=20)
        
        # Simple blocking board
        board_frame = tk.Frame(parent, bg="#34495E", relief=tk.RAISED, bd=3)
        board_frame.pack(pady=20, padx=50, fill=tk.BOTH, expand=True)
        
        tk.Label(board_frame, text="Blocking Board", 
                font=('Arial', 18, 'bold'), bg="#34495E", fg="white").pack(pady=20)
        
        # Simple grid
        grid_frame = tk.Frame(board_frame, bg="#34495E")
        grid_frame.pack(pady=20)
        
        # Test categories
        categories = ["Start Player", "Trump Suit", "Points"]
        for row, category in enumerate(categories):
            tk.Label(grid_frame, text=category, font=('Arial', 12), 
                    bg="#34495E", fg="white", width=15).grid(row=row, column=0, padx=10, pady=5)
            
            # Test buttons
            for col in range(1, 4):
                btn = tk.Button(grid_frame, text=f"Option {col}", width=10, 
                               font=('Arial', 10), command=lambda: print("Button clicked!"))
                btn.grid(row=row, column=col, padx=5, pady=5)
        
        print("Test blocking phase created")

if __name__ == "__main__":
    root = tk.Tk()
    app = MinimalNjetGUI(root)
    root.mainloop()