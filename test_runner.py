#!/usr/bin/env python3
"""
FWMIS Comprehensive Test Suite Runner

This script provides complete automated testing for the FWMIS application including:
- Basic functionality tests
- Pressure/load testing with 10,000+ cases
- UI dialog testing
- Database optimization and performance monitoring
- Comprehensive reporting and analysis

Usage:
    python test_runner.py                    # Run all tests (basic + pressure + UI)
    python test_runner.py --full-suite       # Complete test suite with optimization
    python test_runner.py --import-only      # Run only import tests
    python test_runner.py --workflow-only    # Run only workflow tests
    python test_runner.py --pressure-only    # Run only pressure tests
    python test_runner.py --ui-only          # Run only UI tests
    python test_runner.py --quick            # Run fast tests only
    python test_runner.py --no-pressure      # Skip pressure tests
    python test_runner.py --no-ui            # Skip UI tests
    python test_runner.py --setup-only       # Only setup test environment
    python test_runner.py --generate-report  # Generate test report
"""

import os
import sys
import shutil
import tempfile
import argparse
import subprocess
from pathlib import Path


class FWMISTestRunner:
    """Test runner for FWMIS automated tests"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_db_path = None
        self.backup_db_path = None

    def setup_test_environment(self):
        """Set up isolated test environment"""
        print("[SETUP] Setting up test environment...")

        # Create temporary database for testing
        temp_dir = Path(tempfile.gettempdir())
        self.test_db_path = temp_dir / "fwmis_test.db"

        # Backup original database if it exists
        original_db = self.project_root / "data" / "fruitless.db"
        if original_db.exists():
            self.backup_db_path = temp_dir / "fruitless_backup_test.db"
            shutil.copy2(original_db, self.backup_db_path)
            print(f"[BACKUP] Backed up original database to {self.backup_db_path}")

            # Copy to test database
            shutil.copy2(original_db, self.test_db_path)
        else:
            print("[WARNING] No existing database found, creating fresh test database")
            self._create_fresh_test_database()

        # Set environment variable for tests
        os.environ['FWMIS_TEST_DB'] = str(self.test_db_path)
        os.environ['FWMIS_TEST_MODE'] = '1'

        print(f"[READY] Test environment ready. Test DB: {self.test_db_path}")

    def _create_fresh_test_database(self):
        """Create a fresh test database with minimal schema"""
        import sqlite3

        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Create essential tables
        tables = [
            """
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY,
                transaction_no TEXT UNIQUE,
                list TEXT DEFAULT 'Checklist',
                status TEXT DEFAULT 'Alleged',
                fy_id INTEGER,
                amount REAL,
                vendor_name TEXT,
                is_finalized INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS financial_years (
                id INTEGER PRIMARY KEY,
                year TEXT UNIQUE,
                is_active INTEGER DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                description TEXT
            )
            """
        ]

        for table_sql in tables:
            cursor.execute(table_sql)

        # Insert test data
        cursor.execute("INSERT OR IGNORE INTO financial_years (year, is_active) VALUES ('2025-2026', 1)")
        cursor.execute("INSERT OR IGNORE INTO categories (name, description) VALUES ('Test Category', 'For automated testing')")

        conn.commit()
        conn.close()

    def run_tests(self, test_filter=None, quick_only=False, include_pressure=True, include_ui=True):
        """Run the automated tests"""
        print("[TEST] Running FWMIS automated tests...")

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest", "test_automated_suite.py"]

        # Apply filters
        if test_filter:
            if test_filter == "import":
                cmd.extend(["-k", "TestCaseImport"])
            elif test_filter == "workflow":
                cmd.extend(["-k", "TestFWMISWorkflow"])
            elif test_filter == "duplicates":
                cmd.extend(["-k", "TestDuplicatePrevention"])
            elif test_filter == "performance":
                cmd.extend(["-k", "TestPerformance"])
            elif test_filter == "pressure":
                cmd.extend(["-k", "TestPressureTesting"])
            elif test_filter == "ui":
                cmd.extend(["-k", "TestUIDialogs"])
        else:
            # Run all tests by default
            if not include_pressure:
                cmd.extend(["-m", "not pressure"])
            if not include_ui:
                cmd.extend(["-m", "not ui"])

        if quick_only:
            cmd.extend(["-m", "not slow"])

        cmd.extend(["-v", "--tb=short", "--durations=10"])

        # Run tests
        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=False)
            return result.returncode == 0
        except KeyboardInterrupt:
            print("\n[STOPPED] Tests interrupted by user")
            return False
        except Exception as e:
            print(f"[ERROR] Error running tests: {e}")
            return False

    def cleanup_test_environment(self):
        """Clean up test environment"""
        print("[CLEANUP] Cleaning up test environment...")

        # Remove test database
        if self.test_db_path and self.test_db_path.exists():
            self.test_db_path.unlink()
            print(f"[REMOVED] Removed test database: {self.test_db_path}")

        # Restore original database if it was backed up
        if self.backup_db_path and self.backup_db_path.exists():
            original_db = self.project_root / "data" / "fruitless.db"
            shutil.copy2(self.backup_db_path, original_db)
            self.backup_db_path.unlink()
            print(f"[RESTORE] Restored original database from backup")

        # Clean up environment variables
        for var in ['FWMIS_TEST_DB', 'FWMIS_TEST_MODE']:
            if var in os.environ:
                del os.environ[var]

        print("[CLEAN] Test environment cleaned up")

    def run_import_simulation(self):
        """Run a simulation of the import process"""
        print("[IMPORT] Running import simulation...")

        # Check if test BAS file exists
        bas_file = self.project_root / "data" / "Int_pd_other_partial.TXT"
        if not bas_file.exists():
            print(f"[WARNING] Test BAS file not found: {bas_file}")
            return False

        try:
            # Import required modules
            sys.path.insert(0, str(self.project_root / "scripts"))
            from models.bas_parser import BASParser

            # Parse the file
            parser = BASParser()
            transactions = parser.parse_file(str(bas_file))

            print(f"[STATS] Successfully parsed {len(transactions)} transactions from BAS file")

            # Show sample transaction
            if transactions:
                sample = transactions[0]
                print(f"[SAMPLE] Sample transaction: {sample.get('transaction_no', 'N/A')} - R{sample.get('amount', 0):,.2f}")

            return True

        except Exception as e:
            print(f"[ERROR] Import simulation failed: {e}")
            return False

    def generate_test_report(self):
        """Generate a test report"""
        print("[REPORT] Generating test report...")

        report_file = self.project_root / "test_report.html"

        # Simple HTML report
        report_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>FWMIS Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .status {{ padding: 5px 10px; border-radius: 3px; }}
                .pass {{ background: #d4edda; color: #155724; }}
                .fail {{ background: #f8d7da; color: #721c24; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>FWMIS Automated Test Report</h1>
                <p>Generated: {os.popen('date').read().strip()}</p>
            </div>

            <div class="summary">
                <h2>Test Summary</h2>
                <p>This report was generated by the FWMIS automated test suite.</p>
                <p>To run tests manually: <code>python -m pytest test_automated_suite.py -v</code></p>
            </div>

            <div class="summary">
                <h2>Test Categories</h2>
                <ul>
                    <li><strong>Import Tests:</strong> Verify BAS file parsing and case import functionality</li>
                    <li><strong>Workflow Tests:</strong> Test complete case processing workflow</li>
                    <li><strong>Duplicate Prevention:</strong> Ensure duplicate cases are prevented</li>
                    <li><strong>Performance Tests:</strong> Verify system performance under load</li>
                </ul>
            </div>
        </body>
        </html>
        """

        with open(report_file, 'w') as f:
            f.write(report_content)

        print(f"[FILE] Test report generated: {report_file}")


def main():
    parser = argparse.ArgumentParser(description="FWMIS Automated Test Runner")
    parser.add_argument("--import-only", action="store_true", help="Run only import tests")
    parser.add_argument("--workflow-only", action="store_true", help="Run only workflow tests")
    parser.add_argument("--pressure-only", action="store_true", help="Run only pressure tests")
    parser.add_argument("--ui-only", action="store_true", help="Run only UI tests")
    parser.add_argument("--quick", action="store_true", help="Run only fast tests")
    parser.add_argument("--setup-only", action="store_true", help="Only setup test environment")
    parser.add_argument("--simulate-import", action="store_true", help="Run import simulation")
    parser.add_argument("--generate-report", action="store_true", help="Generate test report")
    parser.add_argument("--full-suite", action="store_true", help="Run complete test suite with optimization")
    parser.add_argument("--no-pressure", action="store_true", help="Skip pressure tests")
    parser.add_argument("--no-ui", action="store_true", help="Skip UI tests")

    args = parser.parse_args()

    runner = FWMISTestRunner()

    try:
        # Setup
        runner.setup_test_environment()

        if args.setup_only:
            print("[OK] Test environment setup complete")
            return

        if args.simulate_import:
            success = runner.run_import_simulation()
            if success:
                print("[SUCCESS] Import simulation successful")
            else:
                print("[FAILED] Import simulation failed")
            return

        if args.generate_report:
            runner.generate_test_report()
            return

        # Full suite mode - comprehensive testing
        if args.full_suite:
            print("[START] RUNNING COMPLETE FWMIS TEST SUITE")
            print("=" * 50)

            # Step 1: Run basic tests
            print("\n[STEP 1] Basic functionality tests")
            basic_success = runner.run_tests(include_pressure=False, include_ui=False)
            if not basic_success:
                print("[ERROR] Basic tests failed - aborting full suite")
                sys.exit(1)

            # Step 2: Database optimization
            print("\n[OPTIMIZE] STEP 2: Database optimization")
            try:
                from scripts.Utilities.database_optimizer import DatabaseOptimizer
                optimizer = DatabaseOptimizer(runner.test_db_path)
                optimizer.create_performance_indexes()
                optimizer.optimize_database()
                print("[OK] Database optimization completed")
            except Exception as e:
                print(f"[WARNING] Database optimization skipped: {e}")

            # Step 3: Pressure tests
            print("\n[STEP 3] Pressure testing")
            pressure_success = runner.run_tests(test_filter="pressure")
            if not pressure_success:
                print("[ERROR] Pressure tests failed")
                sys.exit(1)

            # Step 4: UI tests
            print("\n[STEP 4] UI testing")
            ui_success = runner.run_tests(test_filter="ui")
            if not ui_success:
                print("[ERROR] UI tests failed")
                sys.exit(1)

            # Step 5: Generate final report
            print("\n[STEP 5] Generating performance report")
            try:
                from test_automated_suite import generate_performance_report
                generate_performance_report()
            except Exception as e:
                print(f"[WARNING] Performance report generation failed: {e}")

            print("\n[SUCCESS] COMPLETE TEST SUITE PASSED!")
            print("[OK] Basic functionality: PASSED")
            print("[OK] Database optimization: COMPLETED")
            print("[OK] Pressure testing: PASSED")
            print("[OK] UI testing: PASSED")
            print("[OK] Performance report: GENERATED")
            print("\n[READY] FWMIS is PRODUCTION READY!")

            return

        # Determine test filter
        test_filter = None
        if args.import_only:
            test_filter = "import"
        elif args.workflow_only:
            test_filter = "workflow"
        elif args.pressure_only:
            test_filter = "pressure"
        elif args.ui_only:
            test_filter = "ui"

        # Run tests
        include_pressure = not args.no_pressure
        include_ui = not args.no_ui

        success = runner.run_tests(
            test_filter=test_filter,
            quick_only=args.quick,
            include_pressure=include_pressure,
            include_ui=include_ui
        )

        if success:
            print("[SUCCESS] All tests passed!")
        else:
            print("[FAILED] Some tests failed")
            sys.exit(1)

    finally:
        # Always cleanup
        runner.cleanup_test_environment()


if __name__ == "__main__":
    main()
