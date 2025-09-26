#!/usr/bin/env python3
"""
Test script to verify performance report generation works without Unicode issues
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Set up minimal environment for testing
os.environ['FWMIS_TEST_DB'] = str(Path(__file__).parent / "data" / "fruitless.db")

try:
    from test_automated_suite import generate_performance_report
    print("[TEST] Calling generate_performance_report...")
    generate_performance_report()
    print("[SUCCESS] Performance report generated successfully!")
except Exception as e:
    print(f"[ERROR] Performance report generation failed: {e}")
    import traceback
    traceback.print_exc()
