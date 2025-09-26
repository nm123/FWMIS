#!/usr/bin/env python3
"""
Quick test to verify the automated testing dialog fix
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def test_path_calculation():
    """Test the path calculation used in the automated testing dialog"""
    print("Testing path calculation...")

    # Simulate the path calculation from automated_testing_dialog.py
    dialog_file = Path(__file__).parent / "scripts" / "ui" / "dialogs" / "automated_testing_dialog.py"
    working_dir = str(dialog_file.parent.parent.parent.parent)

    print(f"Dialog file: {dialog_file}")
    print(f"Calculated working dir: {working_dir}")
    print(f"Actual working dir: {Path.cwd()}")

    # Check if test_runner.py exists
    test_runner_path = Path(working_dir) / "test_runner.py"
    print(f"Test runner path: {test_runner_path}")
    print(f"Test runner exists: {test_runner_path.exists()}")

    # Test command construction
    command = ["python", "test_runner.py", "--help"]
    if command[0] == "python":
        command[0] = sys.executable
    command[1] = str(Path(working_dir) / command[1])

    print(f"Final command: {command}")

    return command, working_dir

def test_command_execution():
    """Test running the command"""
    command, working_dir = test_path_calculation()

    print("\nTesting command execution...")
    import subprocess

    try:
        result = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout[:200]}...")
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing automated testing dialog fix...")
    success = test_command_execution()
    print(f"\n✅ Test {'PASSED' if success else 'FAILED'}")
