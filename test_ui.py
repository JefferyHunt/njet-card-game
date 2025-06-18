#!/usr/bin/env python3
import tkinter as tk

def test_basic_ui():
    root = tk.Tk()
    root.title("UI Test")
    root.geometry("800x600")
    
    # Test basic layout
    main_frame = tk.Frame(root, bg="green")
    main_frame.pack(expand=True, fill=tk.BOTH)
    
    # Top section
    top_frame = tk.Frame(main_frame, bg="yellow", height=100)
    top_frame.pack(fill=tk.X, pady=10)
    top_frame.pack_propagate(False)
    
    tk.Label(top_frame, text="TOP SECTION", font=('Arial', 16), bg="yellow").pack(pady=20)
    
    # Middle section
    middle_frame = tk.Frame(main_frame, bg="red")
    middle_frame.pack(expand=True, fill=tk.BOTH, pady=10)
    
    tk.Label(middle_frame, text="MIDDLE SECTION", font=('Arial', 24), bg="red", fg="white").pack(pady=50)
    
    # Bottom section
    bottom_frame = tk.Frame(main_frame, bg="blue", height=200)
    bottom_frame.pack(fill=tk.X, pady=10)
    bottom_frame.pack_propagate(False)
    
    tk.Label(bottom_frame, text="BOTTOM SECTION", font=('Arial', 16), bg="blue", fg="white").pack(pady=50)
    
    print("UI components created")
    root.mainloop()

if __name__ == "__main__":
    test_basic_ui()