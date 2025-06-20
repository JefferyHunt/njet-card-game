#!/usr/bin/env python3

import os
import sys

# Test if table loading works
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✓ PIL/Pillow is available")
except ImportError:
    PIL_AVAILABLE = False
    print("✗ PIL/Pillow not available")

# Check if Table.png exists
table_path = "Table.png"
if os.path.exists(table_path):
    print(f"✓ Table.png found at {table_path}")
    try:
        img = Image.open(table_path)
        print(f"✓ Table.png loaded successfully - Size: {img.size}")
        
        # Test resizing
        resized = img.resize((800, 600), Image.Resampling.LANCZOS)
        print(f"✓ Resize test successful - New size: {resized.size}")
        
    except Exception as e:
        print(f"✗ Error loading Table.png: {e}")
else:
    print(f"✗ Table.png not found at {table_path}")

print("\nChecking PIL dependencies...")
try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    if PIL_AVAILABLE and os.path.exists(table_path):
        img = Image.open(table_path)
        photo = ImageTk.PhotoImage(img)
        print("✓ PhotoImage creation successful")
    
    root.destroy()
except Exception as e:
    print(f"✗ PhotoImage test failed: {e}")

print("\nTable loading test complete.")