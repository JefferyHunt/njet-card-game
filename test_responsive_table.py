#!/usr/bin/env python3
"""Test responsive table background like the game implementation"""

import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✓ PIL/Pillow available")
except ImportError:
    PIL_AVAILABLE = False
    print("✗ PIL/Pillow not available")

def test_responsive_table():
    """Test the responsive table background implementation"""
    if not PIL_AVAILABLE:
        print("Cannot test without PIL/Pillow")
        return
    
    root = tk.Tk()
    root.title("Responsive Table Background Test - NJET")
    root.geometry("800x600")
    root.configure(bg="#2C3E50")
    
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
    
    def create_table_canvas(parent):
        """Create responsive canvas like the game implementation"""
        canvas = tk.Canvas(parent, highlightthickness=0, bg="#497B75")
        canvas.resize_pending = False
        
        def update_table_background(event=None):
            """Update table background when canvas size changes"""
            if table_source:
                try:
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    
                    if canvas_width > 1 and canvas_height > 1:
                        # Keep old image until new one is ready
                        table_img = table_source.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                        table_image = ImageTk.PhotoImage(table_img)
                        
                        # Atomically replace image
                        canvas.delete("table_bg")
                        canvas.create_image(canvas_width//2, canvas_height//2, image=table_image, tags="table_bg")
                        canvas.table_image_ref = table_image
                        canvas.tag_lower("table_bg")
                        print(f"✓ Table resized to: {canvas_width}x{canvas_height}")
                except Exception as e:
                    print(f"Error updating table: {e}")
            canvas.resize_pending = False
        
        def on_canvas_resize(event):
            """Handle canvas resize with debouncing"""
            if not canvas.resize_pending:
                canvas.resize_pending = True
                canvas.after(10, update_table_background)
        
        canvas.bind("<Configure>", on_canvas_resize)
        canvas.after(1, update_table_background)
        return canvas
    
    # Main container (transparent)
    main_container = tk.Frame(root)
    main_container.pack(fill=tk.BOTH, expand=True)
    
    # Game area (transparent)
    game_area = tk.Frame(main_container)
    game_area.pack(fill=tk.BOTH, expand=True)
    
    # Create responsive table canvas
    table_canvas = create_table_canvas(game_area)
    table_canvas.pack(fill=tk.BOTH, expand=True)
    
    # UI on top of table
    table_frame = tk.Frame(table_canvas, bg='', relief=tk.FLAT)
    table_frame.place(x=0, y=0, relwidth=1.0, relheight=1.0)
    
    # Test content
    title = tk.Label(table_frame, text="RESPONSIVE TABLE TEST", 
                    font=("Arial", 18, "bold"), bg="#2C3E50", fg="#F39C12")
    title.pack(pady=20)
    
    info = tk.Label(table_frame, text="✅ Table background scales with window size\n✅ Resize the window to test responsiveness", 
                   font=("Arial", 12), bg="#2C3E50", fg="white", justify=tk.CENTER)
    info.pack(pady=40)
    
    # Test panel in center
    test_panel = tk.Frame(table_frame, bg="#497B75", relief=tk.RAISED, bd=3)
    test_panel.pack(expand=True, padx=100, pady=100, fill=tk.BOTH)
    
    tk.Label(test_panel, text="TEST PANEL", font=("Arial", 14, "bold"), 
            bg="#497B75", fg="white").pack(pady=20)
    tk.Label(test_panel, text="The ornate table background should be visible\naround this panel and scale with window size", 
            font=("Arial", 10), bg="#497B75", fg="white", justify=tk.CENTER).pack(pady=10)
    
    print("✅ Responsive table test window created")
    print("  - Table background scales dynamically with window size")
    print("  - Try resizing, maximizing, or scaling the window")
    print("  - Table should always fill the entire background")
    print("  Window will auto-close in 15 seconds...")
    
    # Auto-close
    root.after(15000, root.destroy)
    root.mainloop()
    
    print("✅ Responsive table test completed!")

if __name__ == "__main__":
    test_responsive_table()