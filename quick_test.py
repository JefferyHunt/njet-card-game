#!/usr/bin/env python3

import subprocess
import sys
import os
import signal
import threading
import time

def run_test():
    """Run the game briefly to check debug output"""
    print("Starting game...")
    
    # Change to the game directory
    os.chdir('/Users/jefferyhunt/Code/Njet')
    
    process = subprocess.Popen([sys.executable, 'njet-game-2.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT,
                              universal_newlines=True,
                              preexec_fn=os.setsid)
    
    lines_captured = 0
    max_lines = 50
    
    try:
        while lines_captured < max_lines:
            line = process.stdout.readline()
            if line:
                print(line.strip())
                lines_captured += 1
            elif process.poll() is not None:
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up process
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=2)
        except:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass

if __name__ == "__main__":
    run_test()