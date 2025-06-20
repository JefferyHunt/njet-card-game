#!/usr/bin/env python3
"""Test table background using Label approach"""

import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✓ PIL/Pillow available")
except ImportError:
    PIL_AVAILABLE = False
    print("✗ PIL/Pillow not available")

def test_label_background():
    """Test using a Label as background"""
    if not PIL_AVAILABLE:
        print("Cannot test without PIL/Pillow")
        return
    
    root = tk.Tk()
    root.title("Table Label Background Test")
    root.geometry("800x600")
    root.configure(bg="#2C3E50")
    
    # Colors
    colors = {
        "bg": "#2C3E50",
        "panel_bg": "#497B75",
        "accent": "#F39C12"
    }
    
    # Load table
    table_source = None
    try:
        if os.path.exists("Table.png"):
            table_source = Image.open("Table.png")
            print(f"✓ Table loaded: {table_source.size}")
        else:
            print("✗ Table.png not found")
            return
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Create container
    container = tk.Frame(root, bg=colors["bg"])
    container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    def setup_table_background():
        """Set up table as background label"""
        try:
            container.update_idletasks()
            width = container.winfo_width()
            height = container.winfo_height()
            
            if width > 1 and height > 1:
                # Resize table
                table_img = table_source.resize((width, height), Image.Resampling.LANCZOS)
                table_photo = ImageTk.PhotoImage(table_img)
                
                # Create background label
                if hasattr(container, 'table_bg_label'):
                    container.table_bg_label.destroy()
                
                container.table_bg_label = tk.Label(container, image=table_photo)
                container.table_bg_label.image = table_photo
                container.table_bg_label.place(x=0, y=0, width=width, height=height)
                container.table_bg_label.lower()
                
                print(f"✓ Table background label created: {width}x{height}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    # Set up background
    container.after(100, setup_table_background)
    
    # Add some UI elements on top
    container.after(200, lambda: add_ui_elements())
    
    def add_ui_elements():
        """Add UI elements on top of table background"""
        # Title
        title = tk.Label(container, text="TABLE BACKGROUND TEST", 
                        font=("Arial", 16, "bold"), bg=colors["bg"], fg=colors["accent"])
        title.pack(pady=10)
        
        # Test panel
        test_panel = tk.Frame(container, bg=colors["panel_bg"], relief=tk.RAISED, bd=3)
        test_panel.pack(expand=True, padx=50, pady=50, fill=tk.BOTH)
        
        tk.Label(test_panel, text="TEST PANEL", font=("Arial", 14, "bold"), 
                bg=colors["panel_bg"], fg="white").pack(pady=20)
        tk.Label(test_panel, text="The ornate table should be visible\nbehind and around this panel", 
                font=("Arial", 10), bg=colors["panel_bg"], fg="white", justify=tk.CENTER).pack()
        
        print("✓ UI elements added on top of table background")
    
    print("✅ Label background test window created")
    print("  - Table should be visible as background")
    print("  - UI elements should be on top")
    print("  Window will auto-close in 15 seconds...")
    
    root.after(15000, root.destroy)
    root.mainloop()
    
    print("✅ Label background test completed!")

if __name__ == "__main__":
    test_label_background()