"""
Test Execution Module

Contains test execution and management functionality for the automated testing dialog.
"""

import subprocess
import sys
import glob
import os
import tempfile
import uuid
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtWidgets import QMessageBox, QProgressDialog


class TestExecutionManager:
    """
    Manages test execution operations for the automated testing dialog.
    """

    def __init__(self, dialog):
        """
        Initialize the test execution manager.

        Args:
            dialog: The parent AutomatedTestingDialog instance
        """
        self.dialog = dialog

    def run_complete_test_suite(self) -> None:
        """Run the complete test suite - all discovered tests."""
        self._run_all_discovered_tests()

    def run_daily_verification(self) -> None:
        """Run daily verification tests."""
        try:
            # Build verification command
            project_root = Path(
                __file__
            ).parent.parent.parent.parent.parent  # FWMIS directory
            script_path = project_root / "daily_test_verification.py"

            if not script_path.exists():
                QMessageBox.warning(
                    self.dialog,
                    "Script Not Found",
                    f"Daily verification script not found at:\n{script_path}\n\n"
                    "Please ensure daily_test_verification.py exists in the project root.",
                )
                return

            # Run the verification script
            command = [sys.executable, str(script_path)]
            working_dir = str(project_root)

            self._execute_test_command(command, working_dir, "Daily Verification")

        except Exception as e:
            QMessageBox.critical(
                self.dialog, "Error", f"Failed to run daily verification: {str(e)}"
            )

    def discover_all_tests(self) -> List[Path]:
        """
        Discover all test files in the project using improved logic that validates actual test content.

        Returns:
            List of test file paths
        """
        project_root = self._get_project_root()

        # Find all test files using same patterns as daily verification
        test_files = []
        for pattern in ["test_*.py", "*_test.py", "test*.py"]:
            test_files.extend(glob.glob(str(project_root / "**" / pattern), recursive=True))

        # Filter out common non-test files and duplicates (same as daily verification)
        exclude_patterns = [
            "test_runner.py",  # This is the runner, not a test file
            "daily_test_verification.py",  # This is the verifier itself
            "archive/",  # Archived tests with outdated imports
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".git"
        ]

        # Use a set to eliminate duplicates and filter
        unique_files = set()
        for test_file in test_files:
            test_path = Path(test_file)
            # Skip files in archive folder entirely
            if "archive" in str(test_path):
                continue
            if not any(excl in test_file for excl in exclude_patterns):
                # Additional check: verify file actually contains pytest test functions
                if self._file_contains_tests(test_path):
                    unique_files.add(test_path.resolve())

        return sorted(list(unique_files))

    def _file_contains_tests(self, file_path):
        """Check if a file actually contains pytest test functions"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Only include files that are clearly pytest test files
            filename = file_path.name.lower()
            path_str = str(file_path).lower()

            # Exclude module files that happen to contain "test" in names
            if filename in ['test_execution.py', 'test_worker.py']:
                return False

            # Exclude dialog-related files that aren't actual tests
            if 'dialog' in path_str and 'test_' not in filename:
                return False

            # Exclude utility/debug scripts that are not proper application tests
            utility_scripts = [
                'test_automated_testing_fix.py',
                'test_discovery_improved.py',
                'test_dialog_discovery.py',
                'test_dialog_env.py',
                'test_dialog_full.py',
                'test_dialog_simulation.py'
            ]
            if filename in utility_scripts:
                return False

            # Only include files in the tests/ directory or files that have proper pytest structure
            if 'tests/' in path_str:
                return True

            # For files outside tests/, require them to have pytest-style test classes or multiple test functions
            import re
            test_function_pattern = r'\bdef\s+test_'
            test_class_pattern = r'\bclass\s+Test.*:'

            has_test_functions = bool(re.search(test_function_pattern, content))
            has_test_classes = bool(re.search(test_class_pattern, content))

            # Must have test classes OR at least one test function to be considered a pytest file
            return has_test_classes or has_test_functions
        except Exception:
            return False

    def _run_all_discovered_tests(self) -> None:
        """
        Run all tests that are automatically discovered in the project.
        This implements the self-healing functionality with proper database isolation.
        """
        test_db_path = None
        try:
            # Discover all test files
            test_files = self.discover_all_tests()

            if not test_files:
                QMessageBox.warning(
                    self.dialog,
                    "No Tests Found",
                    "No test files were discovered in the project.\n\n"
                    "Please ensure you have test files following the naming convention:\n"
                    "- test_*.py\n- *_test.py\n- test*.py"
                )
                return

            # Set up isolated test database
            test_db_path = self._setup_test_database()

            # Build pytest command to run all discovered test files
            project_root = self._get_project_root()
            test_paths = [str(f.relative_to(project_root)) for f in test_files]

            # Run all tests with pytest, setting environment variables
            env_vars = {
                'FWMIS_TEST_DB': test_db_path,
                'FWMIS_TEST_MODE': '1',
                'FWMIS_DEBUG': '1'
            }

            command = [sys.executable, "-m", "pytest"] + test_paths + ["-v", "--tb=short"]
            working_dir = str(project_root)

            self._execute_test_command_with_env(command, working_dir, f"Complete Test Suite ({len(test_files)} files)", env_vars)

        except Exception as e:
            QMessageBox.critical(
                self.dialog, "Error", f"Failed to run complete test suite: {str(e)}"
            )
        finally:
            # Clean up test database
            self._cleanup_test_database(test_db_path)

    def _setup_test_database(self) -> str:
        """
        Set up an isolated test database for testing.
        Returns the path to the test database.
        """
        # Create unique temporary database for testing
        unique_id = str(uuid.uuid4())[:8]
        test_db_path = os.path.join(tempfile.gettempdir(), f"fwmis_test_{unique_id}.db")

        # Set environment variables for isolated testing
        os.environ['FWMIS_TEST_DB'] = test_db_path
        os.environ['FWMIS_TEST_MODE'] = '1'
        os.environ['FWMIS_DEBUG'] = '1'

        # Create the test database with schema
        self._create_test_database(test_db_path)

        return test_db_path

    def _create_test_database(self, test_db_path: str) -> None:
        """Create the test database with schema and dummy data"""
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        # Create complete schema for all tests (union of all test schemas)
        conn.execute("""
            CREATE TABLE cases (
                id INTEGER PRIMARY KEY,
                transaction_no TEXT UNIQUE,
                base_transaction_no TEXT,
                description TEXT,
                amount REAL,
                status TEXT DEFAULT 'Active',
                fy_id INTEGER,
                responsibility_id INTEGER,
                created_date TEXT,
                updated_date TEXT,
                assessment_status TEXT,
                suffixes TEXT,
                date_reported TEXT,
                reference_no TEXT,
                lc_status TEXT,
                debtor_name TEXT,
                category TEXT,
                list TEXT,
                is_finalized INTEGER DEFAULT 0,
                finalized_date TEXT,
                finalization_reason TEXT,
                evidence_paths TEXT,
                write_off_group_id TEXT,
                FOREIGN KEY (fy_id) REFERENCES financial_years (id),
                FOREIGN KEY (responsibility_id) REFERENCES responsibilities (id)
            )
        """)

        conn.execute("""
            CREATE TABLE financial_years (
                id INTEGER PRIMARY KEY,
                start_year INTEGER,
                end_year INTEGER,
                status TEXT DEFAULT 'closed',
                active_period INTEGER
            )
        """)

        conn.execute("""
            CREATE TABLE periods (
                id INTEGER PRIMARY KEY,
                period_number INTEGER,
                start_date TEXT,
                end_date TEXT,
                fy_id INTEGER,
                is_open INTEGER DEFAULT 0,
                FOREIGN KEY (fy_id) REFERENCES financial_years (id)
            )
        """)

        conn.execute("""
            CREATE TABLE responsibilities (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                parent_id INTEGER,
                is_posting_level INTEGER DEFAULT 0,
                FOREIGN KEY (parent_id) REFERENCES responsibilities (id)
            )
        """)

        # Additional tables needed by various tests
        conn.execute("""
            CREATE TABLE write_off_annexures (
                id INTEGER PRIMARY KEY,
                annexure_no TEXT UNIQUE,
                status TEXT DEFAULT 'Draft',
                role TEXT,
                decline_reason TEXT,
                created_date TEXT,
                updated_date TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE write_off_annexure_cases (
                id INTEGER PRIMARY KEY,
                annexure_id INTEGER,
                case_id INTEGER,
                added_date TEXT,
                FOREIGN KEY (annexure_id) REFERENCES write_off_annexures (id),
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """)

        conn.execute("""
            CREATE TABLE installments (
                id INTEGER PRIMARY KEY,
                case_id INTEGER,
                amount REAL,
                payment_date TEXT,
                description TEXT,
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """)

        # Add comprehensive test data that all tests can use
        # Financial years
        financial_years = [
            (1, 2024, 2025, 'open'),
            (2, 2023, 2024, 'closed'),
            (3, 2025, 2026, 'open'),
        ]
        cursor.executemany("INSERT INTO financial_years (id, start_year, end_year, status) VALUES (?, ?, ?, ?)", financial_years)

        # Responsibilities
        responsibilities = [
            (1, 'Test Responsibility', 1),
            (2, 'Provincial Department', 1),
            (3, 'Municipal Department', 1),
        ]
        cursor.executemany("INSERT INTO responsibilities (id, name, is_posting_level) VALUES (?, ?, ?)", responsibilities)

        # Test cases with all columns
        cases = [
            (1, 'TEST001', 'TEST001', 'Test case 1', 10000.00, 'Active', 1, 1, 'Alleged', 'Test Debtor', 'Test Category'),
            (2, 'TEST002', 'TEST002', 'Test case 2', 25000.00, 'Active', 1, 2, 'Alleged', 'Test Debtor 2', 'Test Category 2'),
            (3, 'TEST003', 'TEST003', 'Test case 3', 5000.00, 'Active', 1, 3, 'Alleged', 'Test Debtor 3', 'Test Category 3'),
        ]
        cursor.executemany("""
            INSERT INTO cases (id, transaction_no, base_transaction_no, description, amount, status, fy_id, responsibility_id, assessment_status, debtor_name, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, cases)

        conn.commit()
        conn.close()

    def _cleanup_test_database(self, test_db_path: Optional[str]) -> None:
        """Clean up the test database and environment variables"""
        if test_db_path and os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except Exception as e:
                print(f"Warning: Could not remove test database {test_db_path}: {e}")

        # Clean up environment variables
        for var in ['FWMIS_TEST_DB', 'FWMIS_TEST_MODE', 'FWMIS_DEBUG']:
            os.environ.pop(var, None)

    def _execute_test_command_with_env(
        self, command: List[str], working_dir: str, title: str, env_vars: Dict[str, str]
    ) -> None:
        """
        Execute a test command with progress dialog and specific environment variables.

        Args:
            command: Command to execute
            working_dir: Working directory
            title: Title for progress dialog
            env_vars: Environment variables to set
        """
        from .test_worker import TestRunnerWorker

        # Show progress dialog
        progress = QProgressDialog(f"Running {title}...", "Cancel", 0, 0, self.dialog)
        progress.setWindowModality(2)  # Qt.WindowModal
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.show()

        # Create and start worker thread with environment variables
        self.dialog.current_worker = TestRunnerWorker(command, working_dir, env_vars)
        self.dialog.current_worker.progress_updated.connect(
            lambda msg: progress.setLabelText(msg)
        )
        self.dialog.current_worker.output_updated.connect(
            self.dialog.update_test_output
        )
        self.dialog.current_worker.test_completed.connect(
            lambda results: self._on_test_completed(results, progress, title)
        )

        self.dialog.current_worker.start()

    def run_test_suite(self, suite_type: str) -> None:
        """
        Run a specific test suite.

        Args:
            suite_type: Type of test suite to run
        """
        self._run_test_suite(suite_type)

    def _run_test_suite(self, suite_type: str) -> None:
        """
        Internal method to run test suites.

        Args:
            suite_type: Type of test suite to run
        """
        try:
            # Build test command based on suite type
            command = self._build_test_command(suite_type)
            if not command:
                return

            # Get project root directory
            project_root = self._get_project_root()
            working_dir = str(project_root)

            self._execute_test_command(
                command, working_dir, f"{suite_type.title()} Test Suite"
            )

        except Exception as e:
            QMessageBox.critical(
                self.dialog, "Error", f"Failed to run {suite_type} test suite: {str(e)}"
            )

    def _build_test_command(self, suite_type: str) -> Optional[List[str]]:
        """
        Build the test command based on suite type.

        Args:
            suite_type: Type of test suite

        Returns:
            List of command arguments or None if invalid
        """
        if suite_type == "unit":
            return [sys.executable, "-m", "pytest", "tests/unit/", "-v"]
        elif suite_type == "integration":
            return [sys.executable, "-m", "pytest", "tests/integration/", "-v"]
        elif suite_type == "performance":
            return [
                sys.executable,
                "-m",
                "pytest",
                "tests/performance/",
                "-v",
                "--durations=10",
            ]
        elif suite_type == "complete":
            return [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
        else:
            QMessageBox.warning(
                self.dialog,
                "Invalid Suite Type",
                f"Unknown test suite type: {suite_type}",
            )
            return None

    def _get_project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent.parent.parent  # FWMIS directory

    def _execute_test_command(
        self, command: List[str], working_dir: str, title: str
    ) -> None:
        """
        Execute a test command with progress dialog.

        Args:
            command: Command to execute
            working_dir: Working directory
            title: Title for progress dialog
        """
        from .test_worker import TestRunnerWorker

        # Show progress dialog
        progress = QProgressDialog(f"Running {title}...", "Cancel", 0, 0, self.dialog)
        progress.setWindowModality(2)  # Qt.WindowModal
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.show()

        # Create and start worker thread with environment variables
        env_vars = {}
        if 'FWMIS_TEST_DB' in os.environ:
            env_vars['FWMIS_TEST_DB'] = os.environ['FWMIS_TEST_DB']
        if 'FWMIS_TEST_MODE' in os.environ:
            env_vars['FWMIS_TEST_MODE'] = os.environ['FWMIS_TEST_MODE']
        if 'FWMIS_DEBUG' in os.environ:
            env_vars['FWMIS_DEBUG'] = os.environ['FWMIS_DEBUG']

        self.dialog.current_worker = TestRunnerWorker(command, working_dir, env_vars)
        self.dialog.current_worker.progress_updated.connect(
            lambda msg: progress.setLabelText(msg)
        )
        self.dialog.current_worker.output_updated.connect(
            self.dialog.update_test_output
        )
        self.dialog.current_worker.test_completed.connect(
            lambda results: self._on_test_completed(results, progress, title)
        )

        self.dialog.current_worker.start()

    def _on_test_completed(self, results: Dict, progress, title: str) -> None:
        """
        Handle test completion.

        Args:
            results: Test execution results
            progress: Progress dialog to close
            title: Title of the test execution
        """
        progress.close()
        self.dialog.test_suite_completed(results)
