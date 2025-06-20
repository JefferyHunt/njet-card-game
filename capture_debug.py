#!/usr/bin/env python3

import sys
import subprocess
import time
import signal
import os

def capture_debug():
    """Capture debug output from game startup"""
    
    print("Starting game to capture debug output...")
    
    # Start the game process
    env = os.environ.copy()
    process = subprocess.Popen(
        [sys.executable, 'njet-game-2.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
        cwd='/Users/jefferyhunt/Code/Njet'
    )
    
    # Capture output for a limited time
    captured_lines = []
    start_time = time.time()
    
    try:
        while time.time() - start_time < 30:  # 30 seconds max
            line = process.stdout.readline()
            if line:
                print(line.strip())
                captured_lines.append(line.strip())
                
                # Stop if we see blocking phase debug output
                if "DEBUG:" in line and "table" in line.lower():
                    print("Found table debug output!")
                    break
                    
            if process.poll() is not None:
                break
                
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        # Clean up
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    
    print("\nCapture complete.")
    return captured_lines

if __name__ == "__main__":
    lines = capture_debug()