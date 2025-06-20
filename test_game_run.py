#!/usr/bin/env python3

import subprocess
import sys
import time
import signal
import os

def test_game():
    print("Starting game to test table background...")
    
    # Start the game
    process = subprocess.Popen([sys.executable, 'njet-game-2.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT,
                              universal_newlines=True,
                              cwd='/Users/jefferyhunt/Code/Njet')
    
    # Let it run for 15 seconds to see initialization
    time.sleep(15)
    
    # Terminate the process
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    
    print("Game test completed.")

if __name__ == "__main__":
    test_game()