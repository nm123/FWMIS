"""
Automated Testing Dialog Module

Main dialog class for automated testing integration, refactored into modular components.
"""

from typing import Dict

from PyQt5.QtWidgets import QDialog

from .results_handling import ResultsHandler
from .test_execution import TestExecutionManager
from .ui_setup import UISetupManager


class AutomatedTestingDialog(QDialog):
    """
    Main dialog for automated testing integration.

    This dialog provides a comprehensive UI for running automated tests,
    CI/CD integration, test result analysis, and test scheduling.
    """

    def __init__(self, parent=None):
        """
        Initialize the automated testing dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize managers
        self.ui_manager = UISetupManager(self)
        self.test_manager = TestExecutionManager(self)
        self.results_handler = ResultsHandler(self)

        # Initialize attributes
        self.current_worker = None
        self.test_history = []

        # Setup UI
        self.ui_manager.setup_ui()

        # Load initial data
        self.load_test_history()
        self.refresh_discovered_tests()

    def update_test_options(self) -> None:
        """Update test options based on selected test type."""
        # This method can be implemented to update UI based on test type selection
        pass

    # Delegate test execution methods to test manager
    def run_complete_test_suite(self) -> None:
        """Run the complete test suite."""
        self.test_manager.run_complete_test_suite()

    def run_daily_verification(self) -> None:
        """Run daily verification tests."""
        self.test_manager.run_daily_verification()

    def run_test_suite(self, suite_type: str) -> None:
        """
        Run a specific test suite.

        Args:
            suite_type: Type of test suite to run
        """
        self.test_manager.run_test_suite(suite_type)

    # Delegate results handling methods to results handler
    def verification_completed(self, results: Dict) -> None:
        """
        Handle completion of verification tests.

        Args:
            results: Verification test results
        """
        self.results_handler.verification_completed(results)

    def record_verification_result(self, results: Dict) -> None:
        """
        Record verification results.

        Args:
            results: Verification test results
        """
        self.results_handler.record_verification_result(results)

    def test_suite_completed(self, results: Dict) -> None:
        """
        Handle completion of test suite execution.

        Args:
            results: Test suite execution results
        """
        self.results_handler.test_suite_completed(results)

    def record_test_result(self, results: Dict) -> None:
        """
        Record test suite results.

        Args:
            results: Test suite execution results
        """
        self.results_handler.record_test_result(results)

    def load_test_history(self) -> None:
        """Load test history from database."""
        self.results_handler.load_test_history()

    def refresh_discovered_tests(self) -> None:
        """Refresh and display the list of discovered test files."""
        try:
            discovered_tests = self.test_manager.discover_all_tests()

            # Update UI with discovered test count
            if hasattr(self, "discovered_tests_label"):
                self.discovered_tests_label.setText(f"Discovered: {len(discovered_tests)} test files")

            # Update test file list if it exists
            if hasattr(self, "test_files_list"):
                self.test_files_list.clear()
                for test_file in discovered_tests:
                    try:
                        # Show relative path from project root
                        from pathlib import Path
                        project_root = self.test_manager._get_project_root()
                        relative_path = test_file.relative_to(project_root)
                        self.test_files_list.addItem(str(relative_path))
                    except ValueError:
                        # If we can't make it relative, show absolute path
                        self.test_files_list.addItem(str(test_file))

        except Exception as e:
            print(f"Error refreshing discovered tests: {e}")

    # UI update methods
    def update_test_progress(self, message: str) -> None:
        """
        Update test progress display.

        Args:
            message: Progress message to display
        """
        if hasattr(self, "progress_label"):
            self.progress_label.setText(message)

    def update_test_output(self, line: str) -> None:
        """
        Update test output display.

        Args:
            line: Output line to add
        """
        if hasattr(self, "output_text"):
            self.output_text.append(line)

    # Placeholder methods for CI/CD and scheduling functionality
    def analyze_performance_trends(self) -> None:
        """Analyze performance trends from test history."""
        analysis = self.results_handler.analyze_performance_trends()
        recommendations = self.results_handler.generate_test_recommendations()

        # Update UI with analysis results
        if hasattr(self, "avg_duration_label"):
            avg_duration = analysis.get("average_duration", 0)
            self.avg_duration_label.setText(f"{avg_duration:.2f}s")

        if hasattr(self, "success_rate_label"):
            success_rate = analysis.get("success_rate", 0)
            self.success_rate_label.setText(f"{success_rate:.1%}")

        if hasattr(self, "recommendations_text"):
            self.recommendations_text.setPlainText("\n".join(recommendations))

    def generate_test_recommendations(self) -> None:
        """Generate test improvement recommendations."""
        # This is handled by analyze_performance_trends
        self.analyze_performance_trends()

    def generate_github_workflow(self) -> None:
        """Generate GitHub workflow configuration."""
        # Placeholder for CI/CD functionality
        pass

    def validate_cicd_config(self) -> None:
        """Validate CI/CD configuration."""
        # Placeholder for CI/CD functionality
        pass

    def test_webhook(self) -> None:
        """Test webhook functionality."""
        # Placeholder for CI/CD functionality
        pass

    def update_pipeline_status(self) -> None:
        """Update pipeline status display."""
        # Placeholder for CI/CD functionality
        pass

    def schedule_one_time_test(self) -> None:
        """Schedule a one-time test execution."""
        # Placeholder for scheduling functionality
        pass

    def run_scheduled_test_now(self) -> None:
        """Run a scheduled test immediately."""
        # Placeholder for scheduling functionality
        pass

    def refresh_scheduled_jobs(self) -> None:
        """Refresh the list of scheduled jobs."""
        # Placeholder for scheduling functionality
        pass

    def cancel_scheduled_job(self) -> None:
        """Cancel a scheduled job."""
        # Placeholder for scheduling functionality
        pass

    def closeEvent(self, event) -> None:
        """
        Handle dialog close event.

        Args:
            event: Close event
        """
        # Clean up any running workers
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait()

        super().closeEvent(event)
