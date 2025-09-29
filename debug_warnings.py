#!/usr/bin/env python3
"""
Debug script to identify the source of 11 warnings
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def check_all_possible_warning_sources():
    """Check all possible sources of warnings"""

    print("DEBUGGING WARNING SOURCES")
    print("=" * 50)

    project_root = Path(__file__).parent
    warning_count = 0

    # 1. Check test runner output
    print("\n1. Checking test runner output...")
    try:
        result = subprocess.run([
            sys.executable, str(project_root / "test_runner.py")
        ], capture_output=True, text=True, cwd=project_root)

        warnings_in_output = result.stdout.count("WARNING") + result.stderr.count("WARNING")
        if warnings_in_output > 0:
            print(f"   [WARN] Found {warnings_in_output} warnings in test runner output")
            warning_count += warnings_in_output

            # Show the warnings
            lines = result.stdout.split('\n') + result.stderr.split('\n')
            for line in lines:
                if 'WARNING' in line.upper():
                    print(f"   → {line.strip()}")
    except Exception as e:
        print(f"   Error running test runner: {e}")

    # 2. Check pytest warnings
    print("\n2. Checking pytest warnings...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", str(project_root / "test_automated_suite.py"),
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=project_root, env={**os.environ, 'PYTHONWARNINGS': 'default'})

        warning_lines = [line for line in result.stdout.split('\n') if 'warning' in line.lower()]
        if warning_lines:
            print(f"   [WARN] Found {len(warning_lines)} pytest warnings")
            warning_count += len(warning_lines)
            for line in warning_lines[:5]:  # Show first 5
                print(f"   -> {line.strip()}")
    except Exception as e:
        print(f"   Error running pytest: {e}")

    # 3. Check for Python deprecation warnings
    print("\n3. Checking Python warnings...")
    try:
        result = subprocess.run([
            sys.executable, "-c", "import warnings; warnings.simplefilter('always'); import sys; sys.path.insert(0, 'scripts'); import scripts.ui.dialogs.automated_testing.dialog"
        ], capture_output=True, text=True, cwd=project_root)

        warning_lines = [line for line in result.stderr.split('\n') if line.strip()]
        if warning_lines:
            print(f"   [WARN] Found {len(warning_lines)} Python warnings during import")
            warning_count += len(warning_lines)
            for line in warning_lines[:5]:
                print(f"   -> {line.strip()}")
    except Exception as e:
        print(f"   Error checking imports: {e}")

    # 4. Check for archived files that might still be referenced
    print("\n4. Checking for archived file references...")
    archived_warnings = 0
    archived_files = [
        'archive/test_performance.py',
        'archive/test_ui_dialogs.py',
        'archive/test_workflow_transitions.py',
        'archive/test_database_optimization.py',
        'archive/test_import_validation.py',
        'archive/test_concurrent_users.py',
        'archive/test_edge_cases.py',
        'archive/test_memory_leaks.py',
        'archive/test_data_integrity.py',
        'archive/test_search_functionality.py',
        'archive/test_report_generation.py',
        'archive/test_export_validation.py',
        'archive/test_audit_trail.py',
        'archive/test_backup_recovery.py',
        'archive/test_configuration.py',
        'archive/test_logging.py',
        'archive/test_error_handling.py',
        'archive/test_input_validation.py',
        'archive/test_business_rules.py',
        'archive/test_financial_calculations.py',
    ]

    for archived_file in archived_files:
        if (project_root / archived_file).exists():
            archived_warnings += 1

    if archived_warnings > 0:
        print(f"   [WARN] Found {archived_warnings} archived files still present")
        warning_count += archived_warnings

    # 5. Check temp directory warnings
    print("\n5. Checking temp directory...")
    temp_dir = project_root / "temp"
    if temp_dir.exists():
        temp_files = list(temp_dir.glob("*"))
        non_test_files = [f for f in temp_files if not f.name.startswith("fwmis_test_") and not f.name.startswith("test_report_")]
        if non_test_files:
            print(f"   [WARN] Found {len(non_test_files)} non-test files in temp directory")
            warning_count += 1  # This generates the cleanup warning

    # Summary
    print(f"\n{'=' * 50}")
    print(f"WARNING SUMMARY: Found {warning_count} warnings total")
    print(f"{'=' * 50}")

    if warning_count == 0:
        print("[SUCCESS] No warnings found! The 11 warnings might be from:")
        print("   • IDE/editor warnings")
        print("   • Cached output from previous runs")
        print("   • Different test execution method")
        print("   • GUI dialog warnings (not console)")

    return warning_count

if __name__ == "__main__":
    check_all_possible_warning_sources()
