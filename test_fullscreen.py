#!/usr/bin/env python3
"""Test fullscreen functionality and responsive layout"""

import tkinter as tk
import sys
import os

def test_fullscreen():
    """Test the fullscreen functionality"""
    root = tk.Tk()
    root.title("Fullscreen Test - Press F11 to toggle")
    
    # Get screen size
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    print(f"Screen resolution: {screen_width}x{screen_height}")
    
    # Set window size based on screen
    if screen_width >= 1920:
        window_width, window_height = 1600, 900
    else:
        window_width, window_height = 1200, 800
    
    # Center window
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Fullscreen state
    is_fullscreen = False
    
    def toggle_fullscreen(event=None):
        nonlocal is_fullscreen
        is_fullscreen = not is_fullscreen
        root.attributes('-fullscreen', is_fullscreen)
        
        if is_fullscreen:
            status_label.config(text="FULLSCREEN MODE - Press ESC or F11 to exit", 
                               fg="green", font=("Arial", 14, "bold"))
            print("Entered fullscreen mode")
        else:
            status_label.config(text="WINDOWED MODE - Press F11 for fullscreen", 
                               fg="blue", font=("Arial", 12))
            print("Exited fullscreen mode")
    
    def exit_fullscreen(event=None):
        nonlocal is_fullscreen
        if is_fullscreen:
            is_fullscreen = False
            root.attributes('-fullscreen', False)
            status_label.config(text="WINDOWED MODE - Press F11 for fullscreen", 
                               fg="blue", font=("Arial", 12))
            print("Exited fullscreen mode")
    
    # Bind keys
    root.bind('<F11>', toggle_fullscreen)
    root.bind('<Escape>', exit_fullscreen)
    
    # Make resizable
    root.resizable(True, True)
    
    # Create test layout
    root.configure(bg="#2C3E50")
    
    # Main container that should expand
    main_container = tk.Frame(root, bg="#34495E")
    main_container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
    
    # Title
    title = tk.Label(main_container, text="NJET Fullscreen Test", 
                    font=("Arial", 24, "bold"), bg="#34495E", fg="white")
    title.pack(pady=20)
    
    # Status
    status_label = tk.Label(main_container, text="WINDOWED MODE - Press F11 for fullscreen",
                           font=("Arial", 12), bg="#34495E", fg="blue")
    status_label.pack(pady=10)
    
    # Center area with game-like layout
    center_frame = tk.Frame(main_container, bg="#2C3E50", relief=tk.RAISED, bd=2)
    center_frame.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)
    
    # Simulate blocking board area
    board_frame = tk.Frame(center_frame, bg="#34495E", relief=tk.SUNKEN, bd=2)
    board_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
    
    tk.Label(board_frame, text="BLOCKING PHASE", 
            font=("Arial", 18, "bold"), bg="#34495E", fg="yellow").pack(pady=20)
    
    # Player areas around the board
    players_frame = tk.Frame(board_frame, bg="#34495E")
    players_frame.pack(expand=True, fill=tk.BOTH)
    
    # Configure grid
    players_frame.grid_rowconfigure(1, weight=1)
    players_frame.grid_columnconfigure(1, weight=1)
    
    # Top player
    top_player = tk.Frame(players_frame, bg="#1A237E", relief=tk.RAISED, bd=2)
    top_player.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    tk.Label(top_player, text="Player 2 (AI)", bg="#1A237E", fg="white").pack(pady=5)
    tk.Label(top_player, text="♠ ♠ ♠ ♠", bg="#1A237E", fg="white").pack()
    
    # Left player  
    left_player = tk.Frame(players_frame, bg="#1A237E", relief=tk.RAISED, bd=2)
    left_player.grid(row=1, column=0, padx=10, pady=10, sticky="ns")
    tk.Label(left_player, text="Player 3", bg="#1A237E", fg="white").pack(pady=5)
    tk.Label(left_player, text="♣\n♣\n♣", bg="#1A237E", fg="white").pack()
    
    # Center game area
    center_game = tk.Frame(players_frame, bg="#A0522D", relief=tk.SUNKEN, bd=3)
    center_game.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
    tk.Label(center_game, text="NJET", font=("Arial", 16, "bold"), 
            bg="#A0522D", fg="white").pack(expand=True)
    
    # Right player
    right_player = tk.Frame(players_frame, bg="#1A237E", relief=tk.RAISED, bd=2)
    right_player.grid(row=1, column=2, padx=10, pady=10, sticky="ns")
    tk.Label(right_player, text="Player 4", bg="#1A237E", fg="white").pack(pady=5)
    tk.Label(right_player, text="♦\n♦\n♦", bg="#1A237E", fg="white").pack()
    
    # Bottom player (human)
    bottom_player = tk.Frame(players_frame, bg="#27AE60", relief=tk.RAISED, bd=2)
    bottom_player.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
    tk.Label(bottom_player, text="Player 1 (Human)", bg="#27AE60", fg="white").pack(pady=5)
    tk.Label(bottom_player, text="♥ ♥ ♥ ♥ ♥", bg="#27AE60", fg="white").pack()
    
    # Instructions
    instructions = tk.Label(main_container, 
                           text="F11: Toggle Fullscreen | ESC: Exit Fullscreen | This window should fill the entire screen",
                           font=("Arial", 10), bg="#34495E", fg="lightgray", justify=tk.CENTER)
    instructions.pack(pady=10)
    
    print("✓ Fullscreen test window created")
    print("  - Press F11 to toggle fullscreen")
    print("  - Press ESC to exit fullscreen")
    print("  - Check that layout expands to fill screen properly")
    print("  - Window will close in 15 seconds")
    
    # Auto-close after 15 seconds
    root.after(15000, root.destroy)
    
    try:
        root.mainloop()
        print("✓ Fullscreen test completed")
    except Exception as e:
        print(f"✗ Test error: {e}")

if __name__ == "__main__":
    test_fullscreen()