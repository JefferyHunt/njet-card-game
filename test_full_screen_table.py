#!/usr/bin/env python3
"""Test full screen table background implementation"""

import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✓ PIL/Pillow available")
except ImportError:
    PIL_AVAILABLE = False
    print("✗ PIL/Pillow not available")

def test_full_screen_table():
    """Test the full screen table background as it should appear in game"""
    if not PIL_AVAILABLE:
        print("Cannot test without PIL/Pillow")
        return
    
    root = tk.Tk()
    root.title("Full Screen Table Background Test - NJET")
    root.geometry("1400x900")
    root.configure(bg="#2C3E50")
    
    # Colors matching the game
    colors = {
        "bg": "#2C3E50",
        "panel_bg": "#497B75",
        "accent": "#F39C12",
        "light_text": "#BDC3C7"
    }
    
    # Load table image like the game does
    table_source = None
    try:
        table_path = "Table.png"
        if os.path.exists(table_path):
            table_source = Image.open(table_path)
            print(f"✓ Table loaded: {table_source.size}")
        else:
            print("✗ Table.png not found")
            return
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    def create_table_canvas(parent, width=1200, height=800):
        """Create canvas with full table background covering entire screen"""
        canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0)
        
        # Resize table to fill entire canvas (full screen)
        table_img = table_source.resize((width, height), Image.Resampling.LANCZOS)
        table_image = ImageTk.PhotoImage(table_img)
        
        # Fill entire canvas
        canvas.create_image(width//2, height//2, image=table_image)
        canvas.table_image_ref = table_image  # Prevent garbage collection
        
        return canvas
    
    # Create game area container
    game_area = tk.Frame(root, bg=colors["bg"])
    game_area.pack(fill=tk.BOTH, expand=True)
    
    # Create FULL SCREEN table canvas covering everything
    table_canvas = create_table_canvas(game_area, width=1400, height=900)
    table_canvas.pack(fill=tk.BOTH, expand=True)
    
    # Create transparent frame on top for all UI elements
    table_frame = tk.Frame(table_canvas, bg='', relief=tk.FLAT)
    table_frame.place(x=0, y=0, relwidth=1.0, relheight=1.0)
    
    # Configure 5x5 grid like the game
    table_frame.grid_rowconfigure(0, weight=0)  # Title
    table_frame.grid_rowconfigure(1, weight=0)  # Instructions
    table_frame.grid_rowconfigure(2, weight=3)  # Main area
    table_frame.grid_rowconfigure(3, weight=0)  # Status
    table_frame.grid_rowconfigure(4, weight=1)  # Bottom
    
    for i in range(5):
        table_frame.grid_columnconfigure(i, weight=1)
    
    # Title at top
    title_label = tk.Label(table_frame, text="BLOCKING PHASE", 
                          font=("Arial", 16, "bold"), bg=colors["bg"], fg=colors["accent"])
    title_label.grid(row=0, column=0, columnspan=5, pady=5, sticky="ew")
    
    # Instructions
    instruction = tk.Label(table_frame, text="Player 1, choose ONE option to block  •  5 options remaining",
                          font=("Arial", 10), bg=colors["bg"], fg=colors["light_text"])
    instruction.grid(row=1, column=0, columnspan=5, pady=5, sticky="ew")
    
    # Players positioned around the table (on top of table background)
    player_positions = [
        (1, 0, "Player 2\n(AI)\nScore: 0"),      # Left
        (0, 2, "Player 3\n(AI)\nScore: 0"),      # Top  
        (1, 4, "Player 4\n(AI)\nScore: 0"),      # Right
        (4, 2, "Player 1\n(Human)\nScore: 0")    # Bottom
    ]
    
    for row, col, text in player_positions:
        player_frame = tk.Frame(table_frame, bg="#1A237E", relief=tk.RAISED, bd=2)
        player_frame.grid(row=row, column=col, padx=20, pady=20, sticky="nsew")
        
        tk.Label(player_frame, text=text, bg="#1A237E", fg="white", 
                font=("Arial", 9), justify=tk.CENTER).pack(expand=True, pady=10)
        
        # Add sample cards
        cards_text = "🂠 🂠 🂠" if "AI" in text else "♠7 ♥3 ♦9 ♣2 ♠0"
        tk.Label(player_frame, text=cards_text, bg="#1A237E", fg="white", 
                font=("Arial", 8)).pack()
    
    # Blocking board in CENTER of table (floating on table background)
    board_frame = tk.Frame(table_frame, bg=colors["panel_bg"], relief=tk.RAISED, bd=3)
    board_frame.grid(row=2, column=2, padx=50, pady=50, sticky="nsew")
    
    # Player colors legend
    legend_frame = tk.Frame(board_frame, bg=colors["panel_bg"])
    legend_frame.pack(fill=tk.X, padx=10, pady=5)
    
    tk.Label(legend_frame, text="Player Colors:", 
            font=("Arial", 9, "bold"), bg=colors["panel_bg"], fg="white").pack(side=tk.LEFT)
    
    colors_list = ["#E74C3C", "#3498DB", "#2ECC71", "#F39C12"]
    for i, color in enumerate(colors_list):
        color_frame = tk.Frame(legend_frame, bg=color, width=12, height=12, relief=tk.RAISED, bd=1)
        color_frame.pack(side=tk.LEFT, padx=2)
        color_frame.pack_propagate(False)
    
    # Sample blocking categories
    categories = ["Start Player", "Cards to Discard", "Trump Suit", "Super Trump", "Points per Trick"]
    for i, category in enumerate(categories):
        cat_frame = tk.Frame(board_frame, bg=colors["panel_bg"])
        cat_frame.pack(fill=tk.X, padx=10, pady=3)
        
        tk.Label(cat_frame, text=category, bg=colors["panel_bg"], fg="white", 
                font=("Arial", 9, "bold"), width=15).pack(side=tk.LEFT)
        
        # Sample options
        options = ["Player 1", "Player 2", "Player 3"] if i == 0 else ["Red", "Blue", "Green"]
        for j, option in enumerate(options):
            btn = tk.Button(cat_frame, text=option, font=("Arial", 8), width=8, height=1,
                           bg="#3498DB", fg="white")
            btn.pack(side=tk.LEFT, padx=2)
    
    # Status
    status_frame = tk.Frame(root, bg="#27AE60", relief=tk.RAISED, bd=2)
    status_frame.pack(fill=tk.X, padx=20, pady=5)
    
    status_text = "✅ FULL SCREEN TABLE: The ornate table background now covers the ENTIRE screen! All players and UI elements float on top of the table."
    tk.Label(status_frame, text=status_text, 
            font=("Arial", 11, "bold"), bg="#27AE60", fg="white").pack(padx=10, pady=8)
    
    print("✅ Full screen table test window created")
    print("  - Table background covers the ENTIRE screen")
    print("  - All players hover over the table background")
    print("  - Blocking board floats in the center")
    print("  - Authentic card table experience!")
    print("  Window will auto-close in 10 seconds...")
    
    # Auto-close
    root.after(10000, root.destroy)
    root.mainloop()
    
    print("✅ Full screen table test completed!")

if __name__ == "__main__":
    test_full_screen_table()