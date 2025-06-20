#!/usr/bin/env python3

# Simple test to check debug output without GUI
import sys
import os

# Add the current directory to the path
sys.path.insert(0, '/Users/jefferyhunt/Code/Njet')

# Import the parts we need
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

print(f"PIL_AVAILABLE = {PIL_AVAILABLE}")

# Test table loading
table_path = "Table.png"
table_source = None

if not PIL_AVAILABLE:
    print("PIL not available - cannot load table background")
else:
    try:
        if os.path.exists(table_path):
            table_source = Image.open(table_path)
            print(f"✓ Table background loaded successfully - Original size: {table_source.size}")
        else:
            print(f"✗ Table.png not found at {table_path}")
            table_source = None
    except Exception as e:
        print(f"✗ Error loading table background: {e}")
        table_source = None

# Simulate the container setup logic
print(f"DEBUG: PIL_AVAILABLE = {PIL_AVAILABLE}")
print(f"DEBUG: has table_source = {table_source is not None}")

if table_source is not None:
    print(f"DEBUG: table_source is not None = {table_source is not None}")
else:
    print("DEBUG: table_source is None")

if not PIL_AVAILABLE or not table_source:
    print("DEBUG: Using fallback color - table not available")
else:
    print("DEBUG: Proceeding with table background setup")

print("Debug check complete.")