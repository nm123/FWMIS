#!/usr/bin/env python3
"""Debug script to test path construction in automated testing dialog"""

from pathlib import Path
import sys

# Simulate the path construction from automated_testing_dialog.py
script_file = "scripts/ui/dialogs/automated_testing_dialog.py"
print(f"Simulating __file__ = {script_file}")

# This is what the code does:
working_dir = str(Path(script_file).parent.parent.parent.parent)
script_path = str(Path(working_dir) / "daily_test_verification.py")
command = [sys.executable, script_path]

print(f"working_dir = {working_dir}")
print(f"script_path = {script_path}")
print(f"script exists = {Path(script_path).exists()}")
print(f"command = {command}")

# Test if the script can be executed
try:
    import subprocess
    result = subprocess.run([sys.executable, script_path, "--help"],
                          capture_output=True, text=True, timeout=10)
    print(f"Script execution test: exit code {result.returncode}")
    if result.returncode == 0:
        print("Script can be executed successfully!")
    else:
        print(f"Script execution failed: {result.stderr}")
except Exception as e:
    print(f"Script execution error: {e}")
