#!/usr/bin/env python3
"""Test the table background loading"""

import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✓ PIL/Pillow available")
except ImportError:
    PIL_AVAILABLE = False
    print("✗ PIL/Pillow not available")

def test_table_background():
    """Test loading and displaying the table background"""
    if not PIL_AVAILABLE:
        print("Cannot test without PIL/Pillow")
        return
    
    root = tk.Tk()
    root.title("Table Background Test")
    root.geometry("800x600")
    root.configure(bg="#2C3E50")
    
    # Load table image
    table_image = None
    try:
        table_path = "Table.png"
        if os.path.exists(table_path):
            print(f"✓ Found Table.png")
            table_img = Image.open(table_path)
            print(f"✓ Original size: {table_img.size}")
            
            # Resize for display
            table_img = table_img.resize((700, 500), Image.Resampling.LANCZOS)
            table_image = ImageTk.PhotoImage(table_img)
            print(f"✓ Resized to: 700x500")
        else:
            print(f"✗ Table.png not found")
            return
    except Exception as e:
        print(f"✗ Error loading table: {e}")
        return
    
    # Create canvas and display table
    canvas = tk.Canvas(root, width=700, height=500, highlightthickness=0)
    canvas.pack(expand=True, pady=50)
    
    # Display the table image
    canvas.create_image(350, 250, image=table_image)
    
    # Add some test UI elements on top
    test_frame = tk.Frame(canvas, bg="#497B75", relief=tk.RAISED, bd=2)
    test_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=400, height=200)
    
    tk.Label(test_frame, text="BLOCKING PHASE", 
            font=("Arial", 16, "bold"), bg="#497B75", fg="white").pack(pady=10)
    
    tk.Label(test_frame, text="Table background is now visible behind this panel", 
            font=("Arial", 12), bg="#497B75", fg="white").pack(pady=20)
    
    tk.Button(test_frame, text="Test Button", 
             font=("Arial", 12, "bold"), bg="#3498DB", fg="white").pack(pady=10)
    
    print("✓ Table background test window created")
    print("You should see the ornate table background with UI elements on top")
    print("Window will auto-close in 8 seconds...")
    
    # Auto-close
    root.after(8000, root.destroy)
    root.mainloop()
    
    print("✓ Table background test completed")

if __name__ == "__main__":
    test_table_background()