#!/usr/bin/env python3

# Quick test to validate the fix
import subprocess
import sys
import time

def test_game():
    """Test the game briefly to see debug output"""
    print("Testing the blocking turn fix...")
    
    # Start the game and kill it after a few seconds to see initial debug output
    try:
        proc = subprocess.Popen([sys.executable, 'njet-game-2.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT, 
                              text=True)
        
        # Let it run for 3 seconds to see initial output
        time.sleep(3)
        proc.terminate()
        
        # Get the output
        output, _ = proc.communicate(timeout=2)
        
        print("Debug output from game startup:")
        print(output)
        
    except Exception as e:
        print(f"Error running test: {e}")

if __name__ == "__main__":
    test_game()