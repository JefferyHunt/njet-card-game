#!/usr/bin/env python3

import sys
import subprocess
import time
import signal

# Start the game and capture the first few seconds of output
print("Starting game to capture debug output...")

proc = subprocess.Popen(
    ['python3', 'njet-game-2.py'], 
    stdout=subprocess.PIPE, 
    stderr=subprocess.STDOUT, 
    universal_newlines=True,
    bufsize=1
)

# Let it run for a few seconds to see startup
output_lines = []
start_time = time.time()

while time.time() - start_time < 8:  # Wait 8 seconds
    try:
        line = proc.stdout.readline()
        if line:
            output_lines.append(line.strip())
            print(f"CAPTURED: {line.strip()}")
        time.sleep(0.1)
    except:
        break

# Terminate the process
try:
    proc.terminate()
    proc.wait(timeout=2)
except:
    proc.kill()

print("\n=== DEBUG OUTPUT ANALYSIS ===")
for line in output_lines:
    if "DEBUG:" in line:
        print(f"  {line}")

print(f"\nCaptured {len(output_lines)} lines total")