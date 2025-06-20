#!/usr/bin/env python3

import tkinter as tk
import os
from PIL import Image, ImageTk

class MinimalTableTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Minimal Table Test")
        self.root.geometry("800x600")
        
        # Create containers like the game
        self.main_container = tk.Frame(self.root, bg="#2C3E50")
        self.main_container.pack(expand=True, fill=tk.BOTH)
        
        self.game_area = tk.Frame(self.main_container, bg="#2C3E50") 
        self.game_area.pack(expand=True, fill=tk.BOTH)
        
        # Status label
        self.status = tk.Label(self.main_container, text="Ready", 
                              fg="white", bg="#2C3E50")
        self.status.pack(pady=5)
        
        # Load table
        self.table_source = None
        self.load_table_background()
        
        # Test button
        btn = tk.Button(self.main_container, text="Apply Table Background", 
                       command=self.apply_table)
        btn.pack(pady=10)
        
    def load_table_background(self):
        """Load the table background image"""
        try:
            table_path = "Table.png"
            if os.path.exists(table_path):
                self.table_source = Image.open(table_path)
                print(f"✓ Table background loaded successfully - Original size: {self.table_source.size}")
                self.status.config(text=f"Table loaded: {self.table_source.size}")
            else:
                print(f"✗ Table.png not found at {table_path}")
                self.status.config(text="Table not found")
                self.table_source = None
        except Exception as e:
            print(f"✗ Error loading table background: {e}")
            self.status.config(text=f"Error: {e}")
            self.table_source = None
    
    def apply_table(self):
        """Apply table background to main container"""
        if not self.table_source:
            self.status.config(text="No table source available")
            return
            
        try:
            print("DEBUG: Applying table background...")
            
            # Get container size
            self.main_container.update_idletasks()
            width = self.main_container.winfo_width()
            height = self.main_container.winfo_height()
            
            print(f"DEBUG: Container size: {width}x{height}")
            
            if width > 1 and height > 1:
                # Resize table image
                table_img = self.table_source.resize((width, height), Image.Resampling.LANCZOS)
                print("DEBUG: Image resized")
                
                # Create PhotoImage
                table_photo = ImageTk.PhotoImage(table_img)
                print("DEBUG: PhotoImage created")
                
                # Remove old background if exists
                if hasattr(self.main_container, 'table_bg_label'):
                    self.main_container.table_bg_label.destroy()
                    print("DEBUG: Old background removed")
                
                # Create and place background label
                self.main_container.table_bg_label = tk.Label(self.main_container, image=table_photo)
                self.main_container.table_bg_label.image = table_photo  # Keep reference
                self.main_container.table_bg_label.place(x=0, y=0, width=width, height=height)
                self.main_container.table_bg_label.lower()  # Send to back
                
                print(f"DEBUG: ✓ Table background applied: {width}x{height}")
                self.status.config(text=f"Table applied: {width}x{height}")
                
            else:
                print(f"DEBUG: Container size too small: {width}x{height}")
                self.status.config(text=f"Container too small: {width}x{height}")
                
        except Exception as e:
            print(f"DEBUG: Error applying table background: {e}")
            self.status.config(text=f"Apply error: {e}")
    
    def run(self):
        print("Starting minimal table test...")
        self.root.mainloop()

if __name__ == "__main__":
    test = MinimalTableTest()
    test.run()