#!/usr/bin/env python3
"""Test transparent frames on table background"""

import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def test_transparent_frames():
    """Test making frames truly transparent over table background"""
    if not PIL_AVAILABLE or not os.path.exists("Table.png"):
        print("Need PIL and Table.png")
        return
    
    root = tk.Tk()
    root.title("Transparent Frames Test")
    root.geometry("800x600")
    
    # Don't set root background - let table show
    
    # Load table
    table_source = Image.open("Table.png")
    
    # Create main container
    main_container = tk.Frame(root)
    main_container.pack(fill=tk.BOTH, expand=True)
    
    def setup_table_background():
        """Set up table background"""
        try:
            main_container.update_idletasks()
            width = main_container.winfo_width()
            height = main_container.winfo_height()
            
            if width > 1 and height > 1:
                table_img = table_source.resize((width, height), Image.Resampling.LANCZOS)
                table_photo = ImageTk.PhotoImage(table_img)
                
                if hasattr(main_container, 'table_bg_label'):
                    main_container.table_bg_label.destroy()
                
                main_container.table_bg_label = tk.Label(main_container, image=table_photo)
                main_container.table_bg_label.image = table_photo
                main_container.table_bg_label.place(x=0, y=0, width=width, height=height)
                main_container.table_bg_label.lower()
                
                print(f"✓ Table background set: {width}x{height}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Set table background
    main_container.after(100, setup_table_background)
    
    # Test different frame approaches
    main_container.after(200, lambda: test_frame_approaches(main_container))
    
    def test_frame_approaches(container):
        """Test different ways to make frames transparent"""
        
        # Approach 1: No bg parameter
        frame1 = tk.Frame(container)
        frame1.place(x=50, y=50, width=200, height=100)
        tk.Label(frame1, text="Frame 1: No bg", fg="white", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(frame1, text="Default background", fg="yellow").pack()
        
        # Approach 2: bg='' (empty string)
        frame2 = tk.Frame(container, bg='')
        frame2.place(x=300, y=50, width=200, height=100)
        tk.Label(frame2, text="Frame 2: bg=''", fg="white", font=("Arial", 12, "bold"), bg='').pack(pady=10)
        tk.Label(frame2, text="Empty bg", fg="yellow", bg='').pack()
        
        # Approach 3: Configure after creation
        frame3 = tk.Frame(container)
        frame3.configure(bg='')
        frame3.place(x=50, y=200, width=200, height=100)
        tk.Label(frame3, text="Frame 3: configure", fg="white", font=("Arial", 12, "bold"), bg='').pack(pady=10)
        tk.Label(frame3, text="Configured bg", fg="yellow", bg='').pack()
        
        # Approach 4: Labels directly on container
        tk.Label(container, text="Direct on container", fg="white", font=("Arial", 12, "bold"), bg='').place(x=300, y=200)
        tk.Label(container, text="No frame wrapper", fg="yellow", bg='').place(x=300, y=230)
        
        print("✓ Frame approaches tested")
    
    print("✅ Testing transparent frames on table background")
    print("  Window will auto-close in 15 seconds...")
    
    root.after(15000, root.destroy)
    root.mainloop()
    
    print("✅ Transparent frames test completed!")

if __name__ == "__main__":
    test_transparent_frames()