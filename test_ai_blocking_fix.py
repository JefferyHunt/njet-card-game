#!/usr/bin/env python3

# Test script to verify the AI blocking turn fix
import subprocess
import sys
import time
import threading

def test_ai_blocking_fix():
    """Test that AI players take their turns in blocking phase"""
    print("=== TESTING AI BLOCKING FIX ===")
    print("Starting game and monitoring debug output for 10 seconds...")
    
    try:
        # Start the game process
        proc = subprocess.Popen([sys.executable, 'njet-game-2.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT, 
                              text=True)
        
        # Monitor output for AI turn activity
        ai_turns_detected = 0
        blocking_turns_detected = 0
        start_time = time.time()
        
        def monitor_output():
            nonlocal ai_turns_detected, blocking_turns_detected
            while time.time() - start_time < 10:  # Monitor for 10 seconds
                line = proc.stdout.readline()
                if not line:
                    break
                
                print(line.rstrip())  # Show all output
                
                # Check for AI turn indicators
                if "ai_blocking_turn called for player" in line:
                    ai_turns_detected += 1
                    print(f">>> AI TURN DETECTED #{ai_turns_detected} <<<")
                
                if "next_blocking_turn" in line and "ENTRY" in line:
                    blocking_turns_detected += 1
                    print(f">>> BLOCKING TURN #{blocking_turns_detected} <<<")
        
        # Start monitoring in a thread
        monitor_thread = threading.Thread(target=monitor_output)
        monitor_thread.start()
        
        # Wait for monitoring to complete
        monitor_thread.join()
        
        # Terminate the game
        proc.terminate()
        proc.wait(timeout=2)
        
        # Analyze results
        print(f"\n=== TEST RESULTS ===")
        print(f"AI turns detected: {ai_turns_detected}")
        print(f"Blocking turns detected: {blocking_turns_detected}")
        
        if ai_turns_detected > 0:
            print("✅ SUCCESS: AI players are taking turns!")
        else:
            print("❌ FAILURE: No AI turns detected")
        
        if blocking_turns_detected > ai_turns_detected:
            print("✅ SUCCESS: Turn progression is working")
        else:
            print("⚠️  WARNING: Limited turn progression detected")
            
    except Exception as e:
        print(f"Error running test: {e}")
        if 'proc' in locals():
            proc.terminate()

if __name__ == "__main__":
    test_ai_blocking_fix()