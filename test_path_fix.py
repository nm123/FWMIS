#!/usr/bin/env python3
"""
Quick test to verify the path fix
"""

import sys
from pathlib import Path

# Simulate the automated testing dialog path calculation
dialog_file = Path("scripts/ui/dialogs/automated_testing_dialog.py")
working_dir = str(dialog_file.parent.parent.parent.parent)

print(f"Dialog file: {dialog_file}")
print(f"Working dir: {working_dir}")

# Check if test_runner.py exists in working dir
test_runner_path = Path(working_dir) / "test_runner.py"
print(f"Test runner path: {test_runner_path}")
print(f"Test runner exists: {test_runner_path.exists()}")

# Test command construction
command = ["python", "test_runner.py", "--help"]
if command[0] == "python":
    command[0] = sys.executable
command[1] = str(Path(working_dir) / command[1])

print(f"Final command: {command}")
print(f"Python executable: {sys.executable}")
print(f"Test runner absolute path: {command[1]}")
print(f"Test runner file exists: {Path(command[1]).exists()}")
