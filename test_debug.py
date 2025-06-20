#!/usr/bin/env python3

import subprocess
import sys
import threading
import time

def run_game():
    """Run the game and capture output"""
    process = subprocess.Popen([sys.executable, 'njet-game-2.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT,
                              universal_newlines=True)
    
    # Capture output for 10 seconds to see initial loading
    start_time = time.time()
    while time.time() - start_time < 10:
        output = process.stdout.readline()
        if output:
            print(output.strip())
        if process.poll() is not None:
            break
    
    # Kill the process if still running
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

if __name__ == "__main__":
    print("Starting game to capture debug output...")
    run_game()