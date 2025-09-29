#!/usr/bin/env python3
"""
Test the dialog's test discovery method to see if it generates warnings
"""

import sys
from pathlib import Path

# Add scripts directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'scripts'))

def test_dialog_discovery():
    """Test the dialog's test discovery method"""
    print("Testing dialog test discovery...")

    try:
        from ui.dialogs.automated_testing.test_execution import TestExecutionManager

        # Create a mock dialog object
        class MockDialog:
            pass

        mock_dialog = MockDialog()
        manager = TestExecutionManager(mock_dialog)

        # Test discovery
        print("Running discovery...")
        tests = manager.discover_all_tests()
        print(f"Found {len(tests)} test files:")
        for test in tests:
            print(f"  {test.name}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_dialog_discovery()
