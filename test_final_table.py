#!/usr/bin/env python3
"""Test final table background implementation"""

import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def test_final_table():
    """Test the final table background implementation like the game"""
    root = tk.Tk()
    root.title("Final Table Background Test")
    root.geometry("1000x700")
    root.configure(bg="#3C3C3C")
    
    colors = {
        "bg": "#3C3C3C",
        "panel_bg": "#497B75",
        "accent": "#F39C12"
    }
    
    # Load table
    table_source = None
    if PIL_AVAILABLE and os.path.exists("Table.png"):
        table_source = Image.open("Table.png")
        print(f"✓ Table loaded: {table_source.size}")
    
    def setup_table_background(container):
        """Setup table background like the game does"""
        if not table_source:
            container.configure(bg=colors["panel_bg"])
            return
        
        def update_background():
            try:
                container.update_idletasks()
                width = container.winfo_width()
                height = container.winfo_height()
                
                if width > 1 and height > 1:
                    table_img = table_source.resize((width, height), Image.Resampling.LANCZOS)
                    table_photo = ImageTk.PhotoImage(table_img)
                    
                    if hasattr(container, 'table_bg_label'):
                        container.table_bg_label.destroy()
                    
                    container.table_bg_label = tk.Label(container, image=table_photo)
                    container.table_bg_label.image = table_photo
                    container.table_bg_label.place(x=0, y=0, width=width, height=height)
                    container.table_bg_label.lower()
                    
                    print(f"✓ Table background set: {width}x{height}")
            except Exception as e:
                print(f"Error: {e}")
                container.configure(bg=colors["panel_bg"])
        
        container.after(1, update_background)
    
    # Create layout like the game
    main_container = tk.Frame(root, bg=colors["bg"])
    main_container.pack(fill=tk.BOTH, expand=True)
    
    # Info panel (top)
    info_panel = tk.Frame(main_container, bg=colors["bg"], height=80)
    info_panel.pack(fill=tk.X, padx=20, pady=5)
    info_panel.pack_propagate(False)
    
    tk.Label(info_panel, text="FINAL TABLE BACKGROUND TEST", 
            font=("Arial", 16, "bold"), bg=colors["bg"], fg=colors["accent"]).pack(pady=10)
    
    # Game area with table background
    game_area = tk.Frame(main_container, bg=colors["bg"])
    game_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    # Set up table background
    setup_table_background(game_area)
    
    # Add game UI elements on top
    game_area.after(100, lambda: add_game_elements(game_area, colors))
    
    def add_game_elements(container, colors):
        """Add game UI elements like the actual game"""
        # Configure grid
        for i in range(5):
            container.grid_rowconfigure(i, weight=1 if i == 2 else 0)
            container.grid_columnconfigure(i, weight=1)
        
        # Title
        title = tk.Label(container, text="BLOCKING PHASE", 
                        font=("Arial", 16, "bold"), bg=colors["bg"], fg=colors["accent"])
        title.grid(row=0, column=0, columnspan=5, pady=5)
        
        # Player areas (like the game)
        positions = [(3, 2), (2, 1), (1, 2), (2, 3)]  # Bottom, Left, Top, Right
        names = ["Player 1", "Player 2", "Player 3", "Player 4"]
        
        for i, ((row, col), name) in enumerate(zip(positions, names)):
            player_frame = tk.Frame(container, bg=colors["panel_bg"], relief=tk.RIDGE, bd=2)
            player_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            tk.Label(player_frame, text=name, font=("Arial", 10, "bold"), 
                    bg=colors["panel_bg"], fg="white").pack(pady=5)
            tk.Label(player_frame, text="Score: 0", 
                    bg=colors["panel_bg"], fg=colors["accent"]).pack()
        
        # Central blocking board
        board_frame = tk.Frame(container, bg=colors["panel_bg"], relief=tk.RAISED, bd=3)
        board_frame.grid(row=2, column=2, padx=30, pady=30, sticky="nsew")
        
        tk.Label(board_frame, text="BLOCKING BOARD", font=("Arial", 12, "bold"), 
                bg=colors["panel_bg"], fg="white").pack(pady=10)
        
        # Sample options
        for category in ["Start Player", "Trump Suit", "Points per Trick"]:
            cat_frame = tk.Frame(board_frame, bg=colors["panel_bg"])
            cat_frame.pack(fill=tk.X, padx=10, pady=2)
            
            tk.Label(cat_frame, text=category, bg=colors["panel_bg"], fg="white", 
                    font=("Arial", 9, "bold"), width=12).pack(side=tk.LEFT)
            
            for option in ["Option 1", "Option 2", "Option 3"]:
                btn = tk.Button(cat_frame, text=option, font=("Arial", 8), width=8,
                               bg="#3498DB", fg="white")
                btn.pack(side=tk.LEFT, padx=2)
        
        print("✓ Game elements added on top of table background")
    
    print("✅ Final table test created - should show ornate table background")
    print("  with game UI elements properly layered on top")
    print("  Window will auto-close in 12 seconds...")
    
    root.after(12000, root.destroy)
    root.mainloop()
    
    print("✅ Final table test completed!")

if __name__ == "__main__":
    test_final_table()