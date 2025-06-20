#!/usr/bin/env python3
"""Test all SFX integration"""

import tkinter as tk
import os
import pygame

# Initialize pygame mixer for testing
pygame.mixer.init()

class SFXTester:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NJET SFX Integration Test")
        self.root.geometry("600x400")
        self.root.configure(bg="#2C3E50")
        
        # Load sound effects
        self.sounds = {}
        self.load_sfx()
        
        self.create_ui()
    
    def load_sfx(self):
        """Load all SFX files"""
        sfx_dir = "SFX"
        sfx_files = {
            'button_press': 'ButtonPress.mp3',
            'shuffle_deal': 'ShuffleDeal.mp3', 
            'discard_select': 'DiscardSelect.mp3',
            'card_play': 'PlayCard.mp3'
        }
        
        loaded_count = 0
        
        if not os.path.exists(sfx_dir):
            print(f"SFX directory '{sfx_dir}' not found")
            return
        
        for sound_name, filename in sfx_files.items():
            file_path = os.path.join(sfx_dir, filename)
            try:
                if os.path.exists(file_path):
                    sound = pygame.mixer.Sound(file_path)
                    sound.set_volume(0.7)
                    self.sounds[sound_name] = sound
                    loaded_count += 1
                    print(f"✓ Loaded SFX: {filename}")
                else:
                    print(f"✗ SFX file not found: {file_path}")
            except Exception as e:
                print(f"✗ Error loading SFX {filename}: {e}")
        
        print(f"Successfully loaded {loaded_count}/{len(sfx_files)} SFX files")
    
    def play_sound(self, sound_name):
        """Play a sound effect"""
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
                print(f"♪ Playing: {sound_name}")
            except Exception as e:
                print(f"Error playing sound {sound_name}: {e}")
        else:
            print(f"Sound not found: {sound_name}")
    
    def create_ui(self):
        """Create test UI"""
        # Title
        title = tk.Label(self.root, text="NJET SFX Integration Test", 
                        font=("Arial", 18, "bold"), bg="#2C3E50", fg="white")
        title.pack(pady=20)
        
        # Instructions
        instructions = tk.Label(self.root, text="Click buttons below to test each sound effect:", 
                               font=("Arial", 12), bg="#2C3E50", fg="lightgray")
        instructions.pack(pady=10)
        
        # Sound test buttons
        button_frame = tk.Frame(self.root, bg="#2C3E50")
        button_frame.pack(expand=True)
        
        test_buttons = [
            ("🔘 Button Press", "button_press", "For UI navigation buttons"),
            ("🃏 Shuffle Deal", "shuffle_deal", "For card dealing animation"),
            ("✋ Discard Select", "discard_select", "For card selection in discard phase"),
            ("🎯 Play Card", "card_play", "For all card plays (AI and human)")
        ]
        
        for i, (text, sound_name, description) in enumerate(test_buttons):
            # Button container
            btn_container = tk.Frame(button_frame, bg="#34495E", relief=tk.RAISED, bd=2)
            btn_container.pack(pady=10, padx=40, fill=tk.X)
            
            # Test button
            test_btn = tk.Button(btn_container, text=text, font=("Arial", 14, "bold"),
                               command=lambda sn=sound_name: self.play_sound(sn),
                               width=20, height=2, 
                               bg="#3498DB", fg="white",
                               activebackground="#2980B9", activeforeground="white",
                               relief=tk.RAISED, bd=3, cursor="hand2")
            test_btn.pack(side=tk.LEFT, padx=10, pady=10)
            
            # Description
            desc_label = tk.Label(btn_container, text=description, 
                                 font=("Arial", 10), bg="#34495E", fg="white")
            desc_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Status
        status_frame = tk.Frame(self.root, bg="#27AE60", relief=tk.RAISED, bd=2)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        
        loaded_count = len(self.sounds)
        status_text = f"✓ SFX Integration Complete! {loaded_count}/4 sound effects loaded successfully."
        
        if loaded_count == 4:
            status_text += "\\n• ButtonPress.mp3: UI navigation buttons\\n• ShuffleDeal.mp3: Card dealing with animation\\n• DiscardSelect.mp3: Card selection during discard phase\\n• PlayCard.mp3: All card plays (AI and human)"
        
        status_label = tk.Label(status_frame, text=status_text, 
                               font=("Arial", 10), bg="#27AE60", fg="white", justify=tk.LEFT)
        status_label.pack(padx=10, pady=10)
        
        # Exit button
        exit_btn = tk.Button(self.root, text="Exit Test", font=("Arial", 12, "bold"),
                           command=self.root.destroy, 
                           bg="#E74C3C", fg="white", relief=tk.RAISED, bd=2)
        exit_btn.pack(pady=10)
    
    def run(self):
        """Run the test"""
        print("🎵 Starting SFX Integration Test...")
        self.root.mainloop()
        print("✓ SFX test completed")

if __name__ == "__main__":
    try:
        tester = SFXTester()
        tester.run()
    except Exception as e:
        print(f"✗ SFX test failed: {e}")
        import traceback
        traceback.print_exc()