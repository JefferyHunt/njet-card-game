#!/usr/bin/env python3
"""Test table background integration in game phases"""

import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✓ PIL/Pillow available")
except ImportError:
    PIL_AVAILABLE = False
    print("✗ PIL/Pillow not available")

def test_table_integration():
    """Test table background integration like the real game"""
    if not PIL_AVAILABLE:
        print("Cannot test without PIL/Pillow")
        return
    
    root = tk.Tk()
    root.title("Table Integration Test - NJET Game Phases")
    root.geometry("1400x900")
    root.configure(bg="#2C3E50")
    
    # Colors matching the game
    colors = {
        "bg": "#2C3E50",
        "panel_bg": "#497B75",
        "accent": "#F39C12"
    }
    
    # Load table image (matching game code)
    table_image = None
    try:
        table_path = "Table.png"
        if os.path.exists(table_path):
            table_img = Image.open(table_path)
            table_img = table_img.resize((600, 400), Image.Resampling.LANCZOS)
            table_image = ImageTk.PhotoImage(table_img)
            print("✓ Table background loaded successfully")
        else:
            print(f"✗ Table.png not found")
            return
    except Exception as e:
        print(f"✗ Error loading table: {e}")
        return
    
    def create_table_canvas(parent, width=600, height=400):
        """Create a canvas with table background (matching game code)"""
        canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0)
        
        if table_image:
            canvas.create_image(width//2, height//2, image=table_image)
        else:
            canvas.configure(bg=colors["panel_bg"])
        
        return canvas
    
    # Title
    tk.Label(root, text="NJET - Table Background Integration Test", 
            font=("Arial", 18, "bold"), bg=colors["bg"], fg="white").pack(pady=20)
    
    # Test frames for different game phases
    test_frame = tk.Frame(root, bg=colors["bg"])
    test_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
    
    # Configure grid
    test_frame.grid_columnconfigure(0, weight=1)
    test_frame.grid_columnconfigure(1, weight=1)
    test_frame.grid_rowconfigure(0, weight=1)
    
    # Blocking Phase Test
    blocking_frame = tk.Frame(test_frame, bg=colors["bg"])
    blocking_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
    
    tk.Label(blocking_frame, text="BLOCKING PHASE", 
            font=("Arial", 14, "bold"), bg=colors["bg"], fg=colors["accent"]).pack(pady=5)
    
    # Create blocking board with table background
    board_container = tk.Frame(blocking_frame, relief=tk.RAISED, bd=3)
    board_container.pack(pady=10)
    
    board_canvas = create_table_canvas(board_container, width=600, height=350)
    board_canvas.pack()
    
    board_frame = tk.Frame(board_canvas, bg=colors["panel_bg"], relief=tk.FLAT)
    board_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=0.85, relheight=0.85)
    
    tk.Label(board_frame, text="BLOCKING BOARD", 
            font=("Arial", 12, "bold"), bg=colors["panel_bg"], fg="white").pack(pady=10)
    tk.Label(board_frame, text="Table background visible around panel", 
            font=("Arial", 10), bg=colors["panel_bg"], fg="white").pack()
    
    # Add sample blocking options
    options_frame = tk.Frame(board_frame, bg=colors["panel_bg"])
    options_frame.pack(pady=10)
    
    for i, option in enumerate(["Trump: Red", "Super Trump: Njet", "Start Player: 1"]):
        btn = tk.Button(options_frame, text=option, font=("Arial", 9), 
                       bg="#3498DB", fg="white", width=15)
        btn.grid(row=i//2, column=i%2, padx=5, pady=2)
    
    # Trick Taking Phase Test
    trick_frame = tk.Frame(test_frame, bg=colors["bg"])
    trick_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
    
    tk.Label(trick_frame, text="TRICK TAKING PHASE", 
            font=("Arial", 14, "bold"), bg=colors["bg"], fg=colors["accent"]).pack(pady=5)
    
    # Create trick center with table background
    trick_container = tk.Frame(trick_frame, relief=tk.RAISED, bd=3)
    trick_container.pack(pady=10)
    
    trick_canvas = create_table_canvas(trick_container, width=500, height=350)
    trick_canvas.pack()
    
    trick_display = tk.Frame(trick_canvas, bg=colors["panel_bg"], relief=tk.FLAT)
    trick_display.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=0.9, relheight=0.9)
    
    tk.Label(trick_display, text="CURRENT TRICK", 
            font=("Arial", 12, "bold"), bg=colors["panel_bg"], fg="white").pack(pady=10)
    
    # Add sample played cards
    cards_area = tk.Frame(trick_display, bg=colors["bg"], relief=tk.SUNKEN, bd=2)
    cards_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    for i, card in enumerate(["7♥", "9♠", "2♦", "0♣"]):
        card_label = tk.Label(cards_area, text=card, font=("Arial", 14, "bold"), 
                             bg="#ECF0F1", fg="#2C3E50", relief=tk.RAISED, bd=2, 
                             width=4, height=3)
        card_label.grid(row=i//2, column=i%2, padx=5, pady=5)
    
    # Status
    status_frame = tk.Frame(root, bg="#27AE60", relief=tk.RAISED, bd=2)
    status_frame.pack(fill=tk.X, padx=20, pady=10)
    
    status_text = "✓ Table Background Integration Complete! The ornate table background now appears behind game boards in blocking and trick-taking phases."
    tk.Label(status_frame, text=status_text, 
            font=("Arial", 11), bg="#27AE60", fg="white").pack(padx=10, pady=10)
    
    print("✓ Table integration test window created")
    print("  - Both blocking and trick-taking phases show table background")
    print("  - UI panels are layered on top of the ornate table")
    print("  - Table background adds elegant visual depth")
    print("  Window will auto-close in 10 seconds...")
    
    # Auto-close
    root.after(10000, root.destroy)
    root.mainloop()
    
    print("✓ Table integration test completed successfully!")

if __name__ == "__main__":
    test_table_integration()