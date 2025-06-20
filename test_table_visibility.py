#!/usr/bin/env python3
"""Test table background visibility with UI elements"""

import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✓ PIL/Pillow available")
except ImportError:
    PIL_AVAILABLE = False
    print("✗ PIL/Pillow not available")

def test_table_visibility():
    """Test that table background is visible behind UI elements"""
    if not PIL_AVAILABLE:
        print("Cannot test without PIL/Pillow")
        return
    
    root = tk.Tk()
    root.title("Table Visibility Test - NJET")
    root.geometry("1000x700")
    root.configure(bg="#2C3E50")
    
    # Colors
    colors = {
        "bg": "#2C3E50",
        "panel_bg": "#497B75",
        "accent": "#F39C12",
        "light_text": "#BDC3C7"
    }
    
    # Load table image
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
    
    def create_table_canvas(parent):
        """Create canvas with table background like the game"""
        canvas = tk.Canvas(parent, highlightthickness=0, bg=colors["panel_bg"])
        canvas.resize_pending = False
        
        def update_table_background(event=None):
            if table_source:
                try:
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    
                    if canvas_width > 1 and canvas_height > 1:
                        table_img = table_source.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                        table_image = ImageTk.PhotoImage(table_img)
                        
                        canvas.delete("table_bg")
                        canvas.create_image(canvas_width//2, canvas_height//2, image=table_image, tags="table_bg")
                        canvas.table_image_ref = table_image
                        canvas.tag_lower("table_bg")
                        print(f"✓ Table background updated: {canvas_width}x{canvas_height}")
                except Exception as e:
                    print(f"Error updating table: {e}")
            canvas.resize_pending = False
        
        def on_canvas_resize(event):
            if not canvas.resize_pending:
                canvas.resize_pending = True
                canvas.after(10, update_table_background)
        
        canvas.bind("<Configure>", on_canvas_resize)
        canvas.after(1, update_table_background)
        return canvas
    
    # Main setup
    main_container = tk.Frame(root)
    main_container.pack(fill=tk.BOTH, expand=True)
    
    game_area = tk.Frame(main_container)
    game_area.pack(fill=tk.BOTH, expand=True)
    
    # Create table canvas
    table_canvas = create_table_canvas(game_area)
    table_canvas.pack(fill=tk.BOTH, expand=True)
    
    # Test different frame approaches
    print("\\n=== Testing Frame Approaches ===")
    
    # Approach 1: Frame with no bg parameter
    print("1. Testing Frame(canvas) with no bg parameter...")
    table_frame = tk.Frame(table_canvas, relief=tk.FLAT)
    table_frame.place(x=20, y=20, width=300, height=200)
    
    # Add some content to see if it's truly transparent
    tk.Label(table_frame, text="FRAME TEST 1", font=("Arial", 12, "bold"), 
            bg=colors["bg"], fg=colors["accent"]).pack(pady=10)
    tk.Label(table_frame, text="Is table visible behind this?", 
            bg=colors["bg"], fg="white").pack(pady=5)
    
    # Approach 2: Direct canvas widgets
    print("2. Testing direct canvas widgets...")
    canvas_label = tk.Label(table_canvas, text="DIRECT ON CANVAS", 
                           font=("Arial", 12, "bold"), bg=colors["panel_bg"], fg="white")
    table_canvas.create_window(350, 50, window=canvas_label)
    
    canvas_button = tk.Button(table_canvas, text="Canvas Button", 
                             bg=colors["accent"], fg="white")
    table_canvas.create_window(350, 100, window=canvas_button)
    
    # Approach 3: Semi-transparent widgets
    print("3. Testing semi-transparent approach...")
    semi_frame = tk.Frame(table_canvas, bg=colors["panel_bg"], relief=tk.RAISED, bd=2)
    semi_frame.place(x=500, y=20, width=250, height=150)
    
    tk.Label(semi_frame, text="SEMI-TRANSPARENT", font=("Arial", 11, "bold"), 
            bg=colors["panel_bg"], fg="white").pack(pady=10)
    tk.Label(semi_frame, text="Panel with background", 
            bg=colors["panel_bg"], fg="white").pack()
    
    # Status info
    info_frame = tk.Frame(root, bg="#27AE60", relief=tk.RAISED, bd=2)
    info_frame.pack(fill=tk.X, padx=10, pady=5)
    
    info_text = ("✓ Table Background Test: Check if the ornate table pattern is visible\\n"
                "   • Behind Frame Test 1 (should be transparent)\\n"
                "   • Around Direct Canvas Widgets\\n"
                "   • Behind Semi-Transparent Panel")
    
    tk.Label(info_frame, text=info_text, font=("Arial", 10), 
            bg="#27AE60", fg="white", justify=tk.LEFT).pack(padx=10, pady=5)
    
    print("✅ Table visibility test window created")
    print("  - Look for the ornate table background pattern")
    print("  - Check if UI elements properly layer on top")
    print("  - Window will auto-close in 20 seconds...")
    
    # Auto-close
    root.after(20000, root.destroy)
    root.mainloop()
    
    print("✅ Table visibility test completed!")

if __name__ == "__main__":
    test_table_visibility()