#!/usr/bin/env python3
"""
Test the improved test discovery logic
"""

import sys
from pathlib import Path

# Add scripts directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'scripts'))

def test_discovery():
    """Test the improved discovery logic"""
    print("Testing improved test discovery...")

    try:
        from ui.dialogs.automated_testing.test_execution import TestExecutionManager

        # Create a mock dialog object
        class MockDialog:
            pass

        mock_dialog = MockDialog()
        manager = TestExecutionManager(mock_dialog)

        # Test discovery
        tests = manager.discover_all_tests()
        print(f'Found {len(tests)} test files:')
        total_tests = 0

        for test in tests:
            # Count actual test functions in each file
            try:
                with open(test, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    test_count = content.count('def test_')
                    total_tests += test_count
                    print(f'  {test.name}: {test_count} tests')
            except Exception as e:
                print(f'  {test.name}: error reading ({e})')

        print(f'\nTotal test functions: {total_tests}')

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_discovery()
