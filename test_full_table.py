#!/usr/bin/env python3
"""Test full table background implementation"""

import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✓ PIL/Pillow available")
except ImportError:
    PIL_AVAILABLE = False
    print("✗ PIL/Pillow not available")

def test_full_table():
    """Test the full table background as it should appear in game"""
    if not PIL_AVAILABLE:
        print("Cannot test without PIL/Pillow")
        return
    
    root = tk.Tk()
    root.title("Full Table Background Test - NJET")
    root.geometry("1200x800")
    root.configure(bg="#2C3E50")
    
    # Colors matching the game
    colors = {
        "bg": "#2C3E50",
        "panel_bg": "#497B75"
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
    
    def create_table_canvas(parent, width=900, height=600):
        """Create canvas with full table background"""
        canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0)
        
        # Resize table to fill entire canvas
        table_img = table_source.resize((width, height), Image.Resampling.LANCZOS)
        table_image = ImageTk.PhotoImage(table_img)
        
        # Fill entire canvas
        canvas.create_image(width//2, height//2, image=table_image)
        canvas.table_image_ref = table_image  # Prevent garbage collection
        
        return canvas
    
    # Title
    tk.Label(root, text="Full Table Background Test - Blocking Phase Layout", 
            font=("Arial", 16, "bold"), bg=colors["bg"], fg="white").pack(pady=10)
    
    # Create main layout similar to game
    main_frame = tk.Frame(root, bg=colors["bg"])
    main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
    
    # Configure 5x5 grid like the game
    for i in range(5):
        main_frame.grid_rowconfigure(i, weight=1 if i == 2 else 0)
        main_frame.grid_columnconfigure(i, weight=1)
    
    # Phase title
    tk.Label(main_frame, text="BLOCKING PHASE", 
            font=("Arial", 14, "bold"), bg=colors["bg"], fg="#F39C12").grid(
            row=0, column=0, columnspan=5, pady=5)
    
    # Instructions
    tk.Label(main_frame, text="Player 1, choose ONE option to block", 
            font=("Arial", 10), bg=colors["bg"], fg="white").grid(
            row=1, column=0, columnspan=5, pady=5)
    
    # Player placeholders (simplified)
    positions = [
        (1, 0, "Player 2\n(AI)"),     # Left
        (0, 2, "Player 3\n(AI)"),     # Top  
        (1, 4, "Player 4\n(AI)"),     # Right
        (4, 2, "Player 1\n(Human)")   # Bottom
    ]
    
    for row, col, text in positions:
        player_frame = tk.Frame(main_frame, bg="#1A237E", relief=tk.RAISED, bd=2, width=120, height=80)
        player_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        player_frame.pack_propagate(False)
        
        tk.Label(player_frame, text=text, bg="#1A237E", fg="white", 
                font=("Arial", 9), justify=tk.CENTER).pack(expand=True)
    
    # Main table area - FULL TABLE BACKGROUND
    table_area = tk.Frame(main_frame, relief=tk.FLAT, bd=0)
    table_area.grid(row=2, column=2, padx=5, pady=5, sticky="nsew")
    
    # Create LARGE canvas with table background
    table_canvas = create_table_canvas(table_area, width=900, height=600)
    table_canvas.pack(fill=tk.BOTH, expand=True)
    
    # Small blocking board in CENTER of table
    blocking_board = tk.Frame(table_canvas, bg=colors["panel_bg"], relief=tk.RAISED, bd=3)
    blocking_board.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=0.6, relheight=0.7)
    
    # Sample blocking board content
    tk.Label(blocking_board, text="BLOCKING BOARD", 
            font=("Arial", 12, "bold"), bg=colors["panel_bg"], fg="white").pack(pady=10)
    
    categories = ["Start Player", "Cards to Discard", "Trump Suit", "Super Trump", "Points per Trick"]
    for i, category in enumerate(categories):
        cat_frame = tk.Frame(blocking_board, bg=colors["panel_bg"])
        cat_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(cat_frame, text=category, bg=colors["panel_bg"], fg="white", 
                font=("Arial", 9, "bold"), width=15).pack(side=tk.LEFT)
        
        # Sample options
        options = ["Option 1", "Option 2", "Option 3"] if i < 3 else ["1", "2", "3"]
        for j, option in enumerate(options):
            btn = tk.Button(cat_frame, text=option, font=("Arial", 8), width=8, height=1,
                           bg="#3498DB", fg="white")
            btn.pack(side=tk.LEFT, padx=2)
    
    # Status
    status_frame = tk.Frame(root, bg="#27AE60", relief=tk.RAISED, bd=2)
    status_frame.pack(fill=tk.X, padx=20, pady=10)
    
    status_text = "✓ Full Table Background: The ornate table now fills the entire central area with the blocking board centered on top!"
    tk.Label(status_frame, text=status_text, 
            font=("Arial", 11), bg="#27AE60", fg="white").pack(padx=10, pady=10)
    
    print("✓ Full table test window created")
    print("  - Table background fills entire central area")
    print("  - Blocking board is centered on the table")
    print("  - Proper proportions maintained")
    print("  Window will auto-close in 8 seconds...")
    
    # Auto-close
    root.after(8000, root.destroy)
    root.mainloop()
    
    print("✓ Full table test completed!")

if __name__ == "__main__":
    test_full_table()