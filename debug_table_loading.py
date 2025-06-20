#!/usr/bin/env python3
"""Debug table loading specifically"""

import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✓ PIL/Pillow available")
except ImportError:
    PIL_AVAILABLE = False
    print("✗ PIL/Pillow not available")

def debug_table_loading():
    """Debug the table loading like the game does"""
    
    # Check if table file exists
    table_path = "Table.png"
    print(f"Checking for {table_path}...")
    if os.path.exists(table_path):
        print(f"✓ {table_path} exists")
        
        # Try to load it
        if PIL_AVAILABLE:
            try:
                table_source = Image.open(table_path)
                print(f"✓ Table loaded successfully: {table_source.size}, mode: {table_source.mode}")
                
                # Test window with table first
                root = tk.Tk()
                
                # Test creating PhotoImage after root window exists
                test_img = table_source.resize((200, 200), Image.Resampling.LANCZOS)
                test_photo = ImageTk.PhotoImage(test_img)
                print("✓ PhotoImage creation successful")
                root.title("Debug Table Loading")
                root.geometry("400x300")
                
                # Test the setup_table_background logic
                print("\n=== Testing table background setup ===")
                
                # Simulate the game's approach
                container = tk.Frame(root, bg="#3C3C3C")  # Match game root color
                container.pack(fill=tk.BOTH, expand=True)
                
                def setup_table_background(container, table_source):
                    print(f"setup_table_background called for {container}")
                    print(f"PIL_AVAILABLE = {PIL_AVAILABLE}")
                    print(f"table_source = {table_source}")
                    
                    if not PIL_AVAILABLE or not table_source:
                        print("Using fallback color")
                        container.configure(bg="#497B75")  # panel_bg color
                        return
                    
                    def update_container_background():
                        try:
                            container.update_idletasks()
                            width = container.winfo_width()
                            height = container.winfo_height()
                            
                            print(f"Container size: {width}x{height}")
                            
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
                                
                                # Add test elements on top
                                test_label = tk.Label(container, text="TEST: Table background should be visible", 
                                                     fg="white", font=("Arial", 14, "bold"))
                                test_label.place(x=50, y=50)
                                
                            else:
                                print(f"Container size too small: {width}x{height}")
                                
                        except Exception as e:
                            print(f"Error in update_container_background: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    container.after(1, update_container_background)
                
                # Set up table background
                setup_table_background(container, table_source)
                
                print("Window will auto-close in 8 seconds...")
                root.after(8000, root.destroy)
                root.mainloop()
                
                print("✓ Table background test completed")
                return True
                
            except Exception as e:
                print(f"✗ Error loading table: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("✗ PIL not available")
            return False
    else:
        print(f"✗ {table_path} not found")
        return False

if __name__ == "__main__":
    success = debug_table_loading()
    if success:
        print("\n✅ Table loading should work in the game!")
    else:
        print("\n❌ Table loading has issues that need fixing")