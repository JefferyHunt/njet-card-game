#!/usr/bin/env python3

import tkinter as tk
from PIL import Image, ImageTk
import os

class TestBlockingPhase:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Blocking Phase Table Test")
        self.root.geometry("1000x700")
        self.root.configure(bg="#3C3C3C")  # Same as game
        
        # Configure root window grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create same structure as game
        self.main_container = tk.Frame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Configure main container grid
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Game area
        self.game_area = tk.Frame(self.root)
        self.game_area.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        
        # Control panel
        control_frame = tk.Frame(self.main_container, bg="#2C3E50")
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        tk.Button(control_frame, text="Apply Table to Main Container",
                 command=lambda: self.setup_table_background(self.main_container)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="Apply Table to Game Area", 
                 command=lambda: self.setup_table_background(self.game_area)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="Clear All",
                 command=self.clear_backgrounds).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = tk.Label(control_frame, text="Ready", bg="#2C3E50", fg="white")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Load table after UI is set up
        self.table_source = None
        self.load_table_background()
        
        # Add some dummy content to game area to see layering
        content_frame = tk.Frame(self.game_area, bg="#497B75", relief=tk.RAISED, bd=2)
        content_frame.place(x=100, y=100, width=200, height=150)
        
        tk.Label(content_frame, text="Game Content", bg="#497B75", fg="white", 
                font=('Arial', 12, 'bold')).pack(expand=True)
        
        print("Test initialized - click buttons to test table background")
    
    def load_table_background(self):
        """Load the table background image"""
        try:
            table_path = "Table.png"
            if os.path.exists(table_path):
                self.table_source = Image.open(table_path)
                print(f"✓ Table background loaded: {self.table_source.size}")
                self.status_label.config(text=f"Table loaded: {self.table_source.size}")
            else:
                print(f"✗ Table.png not found")
                self.status_label.config(text="Table not found")
        except Exception as e:
            print(f"✗ Error loading table: {e}")
            self.status_label.config(text=f"Load error: {e}")
    
    def setup_table_background(self, container):
        """Set up table background like the game does"""
        print(f"DEBUG: setup_table_background called for {container}")
        
        if not self.table_source:
            print("DEBUG: No table source available")
            container.configure(bg="#497B75")  # Fallback color
            self.status_label.config(text="No table - using fallback")
            return
        
        def update_container_background():
            try:
                print("DEBUG: Updating container background...")
                container.update_idletasks()
                width = container.winfo_width()
                height = container.winfo_height()
                
                print(f"DEBUG: Container size: {width}x{height}")
                
                if width > 1 and height > 1:
                    print("DEBUG: Creating resized table image...")
                    table_img = self.table_source.resize((width, height), Image.Resampling.LANCZOS)
                    
                    print("DEBUG: Creating PhotoImage...")
                    table_photo = ImageTk.PhotoImage(table_img)
                    
                    # Remove old background
                    if hasattr(container, 'table_bg_label'):
                        print("DEBUG: Destroying old table label")
                        container.table_bg_label.destroy()
                    
                    print("DEBUG: Creating and placing table label...")
                    container.table_bg_label = tk.Label(container, image=table_photo)
                    container.table_bg_label.image = table_photo  # Keep reference
                    container.table_bg_label.place(x=0, y=0, width=width, height=height)
                    container.table_bg_label.lower()  # Send to back
                    
                    print(f"DEBUG: ✓ Table background applied: {width}x{height}")
                    self.status_label.config(text=f"Applied: {width}x{height}")
                else:
                    print(f"DEBUG: Container too small: {width}x{height}")
                    self.status_label.config(text=f"Too small: {width}x{height}")
                    
            except Exception as e:
                print(f"ERROR: {e}")
                self.status_label.config(text=f"Error: {e}")
        
        # Delay like the game does
        self.root.after(200, update_container_background)
    
    def clear_backgrounds(self):
        """Clear all backgrounds"""
        for container in [self.main_container, self.game_area]:
            if hasattr(container, 'table_bg_label'):
                container.table_bg_label.destroy()
                delattr(container, 'table_bg_label')
            container.configure(bg="")  # Clear background
        self.status_label.config(text="Cleared")
        print("DEBUG: All backgrounds cleared")
    
    def run(self):
        print("Starting blocking phase test...")
        self.root.mainloop()

if __name__ == "__main__":
    test = TestBlockingPhase()
    test.run()