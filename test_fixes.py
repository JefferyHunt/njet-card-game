#!/usr/bin/env python3

import subprocess
import sys
import time
import signal

def test_ai_fixes():
    """Test the AI blocking fixes"""
    print("=== TESTING AI BLOCKING FIXES ===")
    
    try:
        # Start the game
        proc = subprocess.Popen([sys.executable, 'njet-game-2.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT, 
                              text=True)
        
        # Monitor for specific success indicators
        ai_blocks_successful = 0
        sort_errors = 0
        tcl_errors = 0
        start_time = time.time()
        
        print("Monitoring game for 8 seconds...")
        
        while time.time() - start_time < 8:
            line = proc.stdout.readline()
            if not line:
                break
                
            # Look for successful AI blocks
            if "AI Player" in line and "blocking" in line and "score:" in line:
                ai_blocks_successful += 1
                print(f"✅ AI BLOCK SUCCESS #{ai_blocks_successful}: {line.strip()}")
            
            # Look for errors we fixed
            if "not supported between instances of 'Suit'" in line:
                sort_errors += 1
                print(f"❌ SORT ERROR: {line.strip()}")
            
            if "TclError" in line:
                tcl_errors += 1
                print(f"❌ TCL ERROR: {line.strip()}")
            
            # Show critical debug lines
            if any(keyword in line for keyword in ["ai_blocking_turn called", "next_blocking_turn ENTRY", "SUCCESS: Player changed"]):
                print(f"DEBUG: {line.strip()}")
        
        # Terminate the process
        proc.terminate()
        proc.wait(timeout=2)
        
        # Results
        print(f"\n=== TEST RESULTS ===")
        print(f"✅ Successful AI blocks: {ai_blocks_successful}")
        print(f"❌ Sort errors: {sort_errors}")
        print(f"❌ TCL errors: {tcl_errors}")
        
        if ai_blocks_successful > 0 and sort_errors == 0:
            print("🎉 SUCCESS: AI blocking is working and errors are fixed!")
        elif sort_errors == 0 and tcl_errors == 0:
            print("✅ ERRORS FIXED: No more sort or TCL errors")
        else:
            print("⚠️ PARTIAL SUCCESS: Some issues may remain")
            
    except Exception as e:
        print(f"Test error: {e}")
        if 'proc' in locals():
            proc.terminate()

if __name__ == "__main__":
    test_ai_fixes()