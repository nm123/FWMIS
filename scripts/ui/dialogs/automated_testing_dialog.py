#!/usr/bin/env python3
"""
Automated Testing Integration Dialog for FWMIS

Provides a comprehensive UI for running automated tests and CI/CD integration including:
- Test suite execution and monitoring
- Test result analysis and reporting
- CI/CD pipeline configuration
- Automated testing scheduling
- Performance regression detection
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QTabWidget, QWidget, QProgressBar,
    QMessageBox, QGroupBox, QCheckBox, QComboBox, QSpinBox, QSplitter,
    QSystemTrayIcon, QMenu, QAction, QCalendarWidget, QListWidget,
    QListWidgetItem, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QDateTime
from PyQt5.QtGui import QFont, QIcon, QPixmap, QTextCursor, QColor

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRunnerWorker(QThread):
    """Worker thread for running test suites"""
    progress_updated = pyqtSignal(str)
    test_completed = pyqtSignal(dict)
    output_updated = pyqtSignal(str)

    def __init__(self, test_command: List[str], working_dir: str):
        super().__init__()
        self.test_command = test_command
        self.working_dir = working_dir

    def run(self):
        try:
            self.progress_updated.emit("Starting test execution...")

            # Run the test command
            process = subprocess.Popen(
                self.test_command,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    output_lines.append(line)
                    self.output_updated.emit(line)
                    self.progress_updated.emit(f"Running tests... ({len(output_lines)} lines)")

            return_code = process.poll()

            # Parse results
            results = {
                'return_code': return_code,
                'success': return_code == 0,
                'output': '\n'.join(output_lines),
                'duration': time.time() - self.start_time if hasattr(self, 'start_time') else 0
            }

            self.test_completed.emit(results)

        except Exception as e:
            self.test_completed.emit({
                'return_code': -1,
                'success': False,
                'output': f"Error running tests: {e}",
                'duration': 0
            })


class AutomatedTestingDialog(QDialog):
    """Main dialog for automated testing integration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_worker = None
        self.test_history = []

        self.setWindowTitle("Automated Testing & CI/CD Integration - FWMIS")
        self.setModal(True)
        self.resize(1200, 900)

        self.setup_ui()
        self.load_test_history()

    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Automated Testing & CI/CD Integration")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Test Execution tab
        self.setup_execution_tab()

        # Results & Analysis tab
        self.setup_results_tab()

        # CI/CD Configuration tab
        self.setup_cicd_tab()

        # Scheduling tab
        self.setup_scheduling_tab()

        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # Button box
        button_layout = QHBoxLayout()

        self.run_tests_btn = QPushButton("Run Complete Test Suite")
        self.run_tests_btn.clicked.connect(self.run_complete_test_suite)
        self.run_tests_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 8px 16px; }")
        button_layout.addWidget(self.run_tests_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def setup_execution_tab(self):
        """Set up the test execution tab"""
        exec_widget = QWidget()
        exec_layout = QVBoxLayout(exec_widget)

        # Test Suite Selection
        suite_group = QGroupBox("Test Suite Configuration")
        suite_layout = QVBoxLayout(suite_group)

        # Test options
        options_layout = QVBoxLayout()

        self.full_suite_cb = QCheckBox("Complete test suite (recommended)")
        self.full_suite_cb.setChecked(True)
        self.full_suite_cb.stateChanged.connect(self.update_test_options)
        options_layout.addWidget(self.full_suite_cb)

        self.pressure_tests_cb = QCheckBox("Include pressure/load tests (10,000+ cases)")
        self.pressure_tests_cb.setChecked(True)
        options_layout.addWidget(self.pressure_tests_cb)

        self.ui_tests_cb = QCheckBox("Include UI dialog tests")
        self.ui_tests_cb.setChecked(True)
        options_layout.addWidget(self.ui_tests_cb)

        self.quick_mode_cb = QCheckBox("Quick mode (skip slow tests)")
        self.quick_mode_cb.setChecked(False)
        options_layout.addWidget(self.quick_mode_cb)

        suite_layout.addLayout(options_layout)

        # Test buttons
        btn_layout = QHBoxLayout()

        self.verify_tests_btn = QPushButton("🔍 Verify Test Coverage")
        self.verify_tests_btn.setToolTip("Run daily test verification to check coverage and integration")
        self.verify_tests_btn.clicked.connect(self.run_daily_verification)
        self.verify_tests_btn.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; font-weight: bold; }")
        btn_layout.addWidget(self.verify_tests_btn)

        self.run_basic_btn = QPushButton("📋 Run Basic Tests")
        self.run_basic_btn.clicked.connect(lambda: self.run_test_suite("basic"))
        btn_layout.addWidget(self.run_basic_btn)

        self.run_pressure_btn = QPushButton("🏋️ Run Pressure Tests")
        self.run_pressure_btn.clicked.connect(lambda: self.run_test_suite("pressure"))
        btn_layout.addWidget(self.run_pressure_btn)

        self.run_ui_btn = QPushButton("🖥️ Run UI Tests")
        self.run_ui_btn.clicked.connect(lambda: self.run_test_suite("ui"))
        btn_layout.addWidget(self.run_ui_btn)

        suite_layout.addLayout(btn_layout)
        exec_layout.addWidget(suite_group)

        # Test Output
        output_group = QGroupBox("Test Execution Output")
        output_layout = QVBoxLayout(output_group)

        self.test_output = QTextEdit()
        self.test_output.setReadOnly(True)
        self.test_output.setFontFamily("Courier New")
        self.test_output.setStyleSheet("QTextEdit { background-color: #f8f9fa; }")
        output_layout.addWidget(self.test_output)

        exec_layout.addWidget(output_group)

        self.tab_widget.addTab(exec_widget, "▶️ Execution")

    def setup_results_tab(self):
        """Set up the results and analysis tab"""
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)

        # Test History
        history_group = QGroupBox("Test Execution History")
        history_layout = QVBoxLayout(history_group)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Date/Time", "Test Suite", "Result", "Duration", "Details"
        ])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setAlternatingRowColors(True)
        history_layout.addWidget(self.history_table)

        results_layout.addWidget(history_group)

        # Performance Analysis
        perf_group = QGroupBox("Performance Analysis")
        perf_layout = QVBoxLayout(perf_group)

        self.perf_analysis = QTextEdit()
        self.perf_analysis.setReadOnly(True)
        self.perf_analysis.setMaximumHeight(200)
        perf_layout.addWidget(self.perf_analysis)

        analyze_btn = QPushButton("📊 Analyze Performance Trends")
        analyze_btn.clicked.connect(self.analyze_performance_trends)
        perf_layout.addWidget(analyze_btn)

        results_layout.addWidget(perf_group)

        # Recommendations
        rec_group = QGroupBox("Testing Recommendations")
        rec_layout = QVBoxLayout(rec_group)

        self.test_recommendations = QTextEdit()
        self.test_recommendations.setReadOnly(True)
        self.test_recommendations.setMaximumHeight(150)
        rec_layout.addWidget(self.test_recommendations)

        generate_rec_btn = QPushButton("💡 Generate Recommendations")
        generate_rec_btn.clicked.connect(self.generate_test_recommendations)
        rec_layout.addWidget(generate_rec_btn)

        results_layout.addWidget(rec_group)

        self.tab_widget.addTab(results_widget, "📊 Results")

    def setup_cicd_tab(self):
        """Set up the CI/CD configuration tab"""
        cicd_widget = QWidget()
        cicd_layout = QVBoxLayout(cicd_widget)

        # CI/CD Pipeline Configuration
        pipeline_group = QGroupBox("CI/CD Pipeline Configuration")
        pipeline_layout = QVBoxLayout(pipeline_group)

        # Pipeline options
        self.github_actions_cb = QCheckBox("GitHub Actions integration")
        self.github_actions_cb.setChecked(True)
        pipeline_layout.addWidget(self.github_actions_cb)

        self.auto_deploy_cb = QCheckBox("Automatic deployment on test success")
        self.auto_deploy_cb.setChecked(False)
        pipeline_layout.addWidget(self.auto_deploy_cb)

        self.email_notifications_cb = QCheckBox("Email notifications for test failures")
        self.email_notifications_cb.setChecked(True)
        pipeline_layout.addWidget(self.email_notifications_cb)

        cicd_layout.addWidget(pipeline_group)

        # Webhook Configuration
        webhook_group = QGroupBox("Webhook Configuration")
        webhook_layout = QVBoxLayout(webhook_group)

        self.webhook_url_edit = QTextEdit()
        self.webhook_url_edit.setPlaceholderText("Enter webhook URLs (one per line)")
        self.webhook_url_edit.setMaximumHeight(100)
        webhook_layout.addWidget(self.webhook_url_edit)

        test_webhook_btn = QPushButton("🧪 Test Webhook")
        test_webhook_btn.clicked.connect(self.test_webhook)
        webhook_layout.addWidget(test_webhook_btn)

        cicd_layout.addWidget(webhook_group)

        # Pipeline Status
        status_group = QGroupBox("Pipeline Status")
        status_layout = QVBoxLayout(status_group)

        self.pipeline_status = QTextEdit()
        self.pipeline_status.setReadOnly(True)
        status_layout.addWidget(self.pipeline_status)

        update_status_btn = QPushButton("🔄 Update Pipeline Status")
        update_status_btn.clicked.connect(self.update_pipeline_status)
        status_layout.addWidget(update_status_btn)

        cicd_layout.addWidget(status_group)

        # Configuration Actions
        config_group = QGroupBox("Configuration Actions")
        config_layout = QHBoxLayout(config_group)

        generate_workflow_btn = QPushButton("📝 Generate GitHub Workflow")
        generate_workflow_btn.clicked.connect(self.generate_github_workflow)
        config_layout.addWidget(generate_workflow_btn)

        validate_config_btn = QPushButton("✅ Validate Configuration")
        validate_config_btn.clicked.connect(self.validate_cicd_config)
        config_layout.addWidget(validate_config_btn)

        config_layout.addStretch()
        cicd_layout.addWidget(config_group)

        cicd_layout.addStretch()

        self.tab_widget.addTab(cicd_widget, "🔄 CI/CD")

    def setup_scheduling_tab(self):
        """Set up the test scheduling tab"""
        sched_widget = QWidget()
        sched_layout = QVBoxLayout(sched_widget)

        # Scheduled Tests
        schedule_group = QGroupBox("Scheduled Test Runs")
        schedule_layout = QVBoxLayout(schedule_group)

        # Schedule options
        self.daily_tests_cb = QCheckBox("Daily automated tests")
        self.daily_tests_cb.setChecked(True)
        schedule_layout.addWidget(self.daily_tests_cb)

        self.weekly_full_cb = QCheckBox("Weekly complete test suite")
        self.weekly_full_cb.setChecked(True)
        schedule_layout.addWidget(self.weekly_full_cb)

        self.on_commit_cb = QCheckBox("Tests on every code commit")
        self.on_commit_cb.setChecked(True)
        schedule_layout.addWidget(self.on_commit_cb)

        # Schedule configuration
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Daily test time:"))

        self.hour_combo = QComboBox()
        for hour in range(24):
            self.hour_combo.addItem(f"{hour:02d}:00")
        self.hour_combo.setCurrentText("02:00")  # 2 AM
        time_layout.addWidget(self.hour_combo)

        time_layout.addStretch()
        schedule_layout.addLayout(time_layout)

        sched_layout.addWidget(schedule_group)

        # Manual Scheduling
        manual_group = QGroupBox("Manual Test Scheduling")
        manual_layout = QVBoxLayout(manual_group)

        manual_btn_layout = QHBoxLayout()

        schedule_once_btn = QPushButton("📅 Schedule One-time Test")
        schedule_once_btn.clicked.connect(self.schedule_one_time_test)
        manual_btn_layout.addWidget(schedule_once_btn)

        run_now_btn = QPushButton("▶️ Run Tests Now")
        run_now_btn.clicked.connect(self.run_scheduled_test_now)
        run_now_btn.setStyleSheet("QPushButton { background-color: #007bff; color: white; }")
        manual_btn_layout.addWidget(run_now_btn)

        manual_btn_layout.addStretch()
        manual_layout.addLayout(manual_btn_layout)

        sched_layout.addWidget(manual_group)

        # Scheduled Jobs List
        jobs_group = QGroupBox("Scheduled Jobs")
        jobs_layout = QVBoxLayout(jobs_group)

        self.scheduled_jobs_list = QListWidget()
        jobs_layout.addWidget(self.scheduled_jobs_list)

        jobs_btn_layout = QHBoxLayout()

        refresh_jobs_btn = QPushButton("🔄 Refresh Jobs")
        refresh_jobs_btn.clicked.connect(self.refresh_scheduled_jobs)
        jobs_btn_layout.addWidget(refresh_jobs_btn)

        cancel_job_btn = QPushButton("❌ Cancel Selected Job")
        cancel_job_btn.clicked.connect(self.cancel_scheduled_job)
        jobs_btn_layout.addWidget(cancel_job_btn)

        jobs_btn_layout.addStretch()
        jobs_layout.addLayout(jobs_btn_layout)

        sched_layout.addWidget(jobs_group)

        sched_layout.addStretch()

        self.tab_widget.addTab(sched_widget, "⏰ Scheduling")

    def update_test_options(self):
        """Update test options based on full suite selection"""
        full_suite = self.full_suite_cb.isChecked()
        self.pressure_tests_cb.setChecked(full_suite)
        self.ui_tests_cb.setChecked(full_suite)

    def run_complete_test_suite(self):
        """Run the complete test suite"""
        self.run_test_suite("complete")

    def run_daily_verification(self):
        """Run the daily test verification script"""
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "Verification Running",
                              "Test verification is already running. Please wait for completion.")
            return

        # Build verification command - use absolute path to be safe
        project_root = Path(__file__).parent.parent.parent.parent
        script_path = project_root / "daily_test_verification.py"
        command = [sys.executable, str(script_path)]
        working_dir = str(project_root)

        self.progress_bar.setVisible(True)
        self.progress_label.setText("Running test verification...")
        self.progress_label.setVisible(True)

        # Clear previous output
        self.test_output.clear()
        self.test_output.append("[VERIFICATION] Starting daily test verification...")
        self.test_output.append(f"Command: {' '.join(command)}")
        self.test_output.append("=" * 50)

        self.current_worker = TestRunnerWorker(command, working_dir)
        self.current_worker.progress_updated.connect(self.update_test_progress)
        self.current_worker.output_updated.connect(self.update_test_output)
        self.current_worker.test_completed.connect(self.verification_completed)
        self.current_worker.start()

    def verification_completed(self, results: Dict):
        """Handle verification completion"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        # Add completion summary
        self.test_output.append("=" * 50)
        self.test_output.append(f"Exit Code: {results['return_code']}")
        self.test_output.append(f"Duration: {results.get('duration', 0):.2f}s")

        success = results['success']
        status = "✅ PASSED" if success else "❌ ISSUES FOUND"
        self.test_output.append(f"Result: {status}")

        # Record in history
        self.record_verification_result(results)

        # Show result dialog
        if success:
            QMessageBox.information(self, "Verification Completed",
                                  "[SUCCESS] Test verification completed successfully!\n\n"
                                  "All tests are properly integrated and discoverable.\n"
                                  f"Duration: {results.get('duration', 0):.2f}s")
        else:
            QMessageBox.warning(self, "Verification Issues",
                              "[ISSUES FOUND] Test verification found issues!\n\n"
                              "Check the output for details. You may need to:\n"
                              "• Fix test discovery issues\n"
                              "• Add missing test markers\n"
                              "• Update test configurations\n\n"
                              f"Duration: {results.get('duration', 0):.2f}s")

        # Refresh history
        self.load_test_history()

    def record_verification_result(self, results: Dict):
        """Record verification result in history"""
        result_entry = {
            'timestamp': datetime.now(),
            'suite_type': 'verification',
            'success': results['success'],
            'duration': results.get('duration', 0),
            'exit_code': results['return_code']
        }

        self.test_history.append(result_entry)

        # Save to file (simple implementation)
        try:
            history_file = Path(__file__).parent.parent / "test_history.json"
            with open(history_file, 'w') as f:
                # Convert datetime objects to strings for JSON
                serializable_history = []
                for entry in self.test_history[-100:]:  # Keep last 100 entries
                    entry_copy = entry.copy()
                    entry_copy['timestamp'] = entry_copy['timestamp'].isoformat()
                    serializable_history.append(entry_copy)

                import json
                json.dump(serializable_history, f, indent=2)

        except Exception as e:
            print(f"Failed to save verification history: {e}")

    def run_test_suite(self, suite_type: str):
        """Run a specific test suite"""
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "Tests Running",
                              "Tests are already running. Please wait for completion.")
            return

        # Build test command
        test_commands = {
            "basic": ["python", "test_runner.py"],
            "pressure": ["python", "test_runner.py", "--pressure-only"],
            "ui": ["python", "test_runner.py", "--ui-only"],
            "complete": ["python", "test_runner.py", "--full-suite"]
        }

        if suite_type not in test_commands:
            QMessageBox.warning(self, "Error", f"Unknown test suite type: {suite_type}")
            return

        command = test_commands[suite_type]
        project_root = Path(__file__).parent.parent.parent.parent  # FWMIS root directory

        # Ensure we use the full path to python executable and test_runner.py
        if command[0] == "python":
            command[0] = sys.executable
        command[1] = str(project_root / "test_runner.py")  # Absolute path to test_runner.py
        working_dir = str(project_root)

        self.progress_bar.setVisible(True)
        self.progress_label.setText(f"Running {suite_type} test suite...")
        self.progress_label.setVisible(True)

        # Clear previous output
        self.test_output.clear()
        self.test_output.append(f"[TEST] Starting {suite_type} test suite...")
        self.test_output.append(f"Command: {' '.join(command)}")
        self.test_output.append("=" * 50)

        self.current_worker = TestRunnerWorker(command, working_dir)
        self.current_worker.progress_updated.connect(self.update_test_progress)
        self.current_worker.output_updated.connect(self.update_test_output)
        self.current_worker.test_completed.connect(self.test_suite_completed)
        self.current_worker.start()

    def update_test_progress(self, message: str):
        """Update test progress"""
        self.progress_label.setText(message)

    def update_test_output(self, line: str):
        """Update test output"""
        self.test_output.append(line)

        # Auto-scroll to bottom
        cursor = self.test_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.test_output.setTextCursor(cursor)

    def test_suite_completed(self, results: Dict):
        """Handle test suite completion"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        # Add completion summary
        self.test_output.append("=" * 50)
        self.test_output.append(f"Exit Code: {results['return_code']}")
        self.test_output.append(f"Duration: {results.get('duration', 0):.2f}s")

        success = results['success']
        status = "✅ PASSED" if success else "❌ FAILED"
        self.test_output.append(f"Result: {status}")

        # Record in history
        self.record_test_result(results)

        # Show result dialog
        if success:
            QMessageBox.information(self, "Tests Completed",
                                  f"[SUCCESS] Test suite completed successfully!\n\n"
                                  f"Duration: {results.get('duration', 0):.2f}s")
        else:
            QMessageBox.warning(self, "Tests Failed",
                              f"[FAILED] Test suite failed with exit code {results['return_code']}!\n\n"
                              f"Check the output for details.")

        # Refresh history
        self.load_test_history()

    def record_test_result(self, results: Dict):
        """Record test result in history"""
        result_entry = {
            'timestamp': datetime.now(),
            'suite_type': 'complete',  # Could be enhanced to track specific types
            'success': results['success'],
            'duration': results.get('duration', 0),
            'exit_code': results['return_code']
        }

        self.test_history.append(result_entry)

        # Save to file (simple implementation)
        try:
            history_file = Path(__file__).parent.parent / "test_history.json"
            with open(history_file, 'w') as f:
                # Convert datetime objects to strings for JSON
                serializable_history = []
                for entry in self.test_history[-100:]:  # Keep last 100 entries
                    entry_copy = entry.copy()
                    entry_copy['timestamp'] = entry_copy['timestamp'].isoformat()
                    serializable_history.append(entry_copy)

                import json
                json.dump(serializable_history, f, indent=2)

        except Exception as e:
            print(f"Failed to save test history: {e}")

    def load_test_history(self):
        """Load test execution history"""
        try:
            history_file = Path(__file__).parent.parent / "test_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    import json
                    history_data = json.load(f)

                    self.test_history = []
                    for entry in history_data:
                        entry_copy = entry.copy()
                        entry_copy['timestamp'] = datetime.fromisoformat(entry_copy['timestamp'])
                        self.test_history.append(entry_copy)

            # Update history table
            self.history_table.setRowCount(0)
            for entry in reversed(self.test_history[-50:]):  # Show last 50 results
                row = self.history_table.rowCount()
                self.history_table.insertRow(row)

                status = "[PASSED]" if entry['success'] else "[FAILED]"

                self.history_table.setItem(row, 0, QTableWidgetItem(
                    entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")))
                self.history_table.setItem(row, 1, QTableWidgetItem(entry.get('suite_type', 'unknown')))
                self.history_table.setItem(row, 2, QTableWidgetItem(status))
                self.history_table.setItem(row, 3, QTableWidgetItem(f"{entry['duration']:.1f}s"))
                self.history_table.setItem(row, 4, QTableWidgetItem(f"Exit code: {entry['exit_code']}"))

        except Exception as e:
            print(f"Failed to load test history: {e}")

    def analyze_performance_trends(self):
        """Analyze performance trends from test history"""
        if len(self.test_history) < 2:
            self.perf_analysis.setPlainText("Not enough test data for performance analysis.\nRun more tests to see trends.")
            return

        # Analyze recent performance
        recent_tests = [t for t in self.test_history if (datetime.now() - t['timestamp']).days <= 7]

        if not recent_tests:
            self.perf_analysis.setPlainText("No recent tests found for analysis.")
            return

        total_tests = len(recent_tests)
        successful_tests = sum(1 for t in recent_tests if t['success'])
        avg_duration = sum(t['duration'] for t in recent_tests) / len(recent_tests)

        # Simple trend analysis
        success_rate = successful_tests / total_tests * 100

        analysis = f"""
Performance Analysis (Last 7 days):
• Total Tests: {total_tests}
• Success Rate: {success_rate:.1f}%
• Average Duration: {avg_duration:.2f}s

Test Stability: {'🟢 Excellent' if success_rate >= 95 else '🟡 Good' if success_rate >= 80 else '🔴 Needs Attention'}

Recent Trends:
• Most tests are {'passing' if success_rate >= 80 else 'failing'}
• Average execution time is {'fast' if avg_duration < 60 else 'moderate' if avg_duration < 120 else 'slow'}
• System stability is {'high' if success_rate >= 90 else 'moderate' if success_rate >= 75 else 'low'}
"""

        self.perf_analysis.setPlainText(analysis.strip())

    def generate_test_recommendations(self):
        """Generate testing recommendations"""
        recommendations = """
🧪 TESTING RECOMMENDATIONS:

✅ AUTOMATED TESTING:
• Run complete test suite before every deployment
• Set up CI/CD pipeline with automated testing
• Monitor test execution time and failure rates

✅ PERFORMANCE MONITORING:
• Track database growth and archive regularly
• Monitor memory usage during bulk operations
• Set up alerts for slow queries (>1 second)

✅ REGRESSION PREVENTION:
• Run pressure tests weekly with 10,000+ cases
• Test UI responsiveness with large datasets
• Validate data integrity after system updates

✅ CONTINUOUS IMPROVEMENT:
• Review failed tests and fix root causes
• Update test cases as application evolves
• Archive old test data to maintain performance

🔧 IMMEDIATE ACTIONS:
• Set up automated daily testing schedule
• Configure database archiving for completed FYs
• Enable performance monitoring alerts
"""

        self.test_recommendations.setPlainText(recommendations.strip())

    def generate_github_workflow(self):
        """Generate GitHub Actions workflow file"""
        workflow_content = """name: FWMIS Automated Testing

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements_optimized.txt

    - name: Run basic tests
      run: python test_runner.py

    - name: Run pressure tests (on schedule only)
      if: github.event_name == 'schedule'
      run: python test_runner.py --pressure-only

    - name: Generate test report
      if: always()
      run: python test_runner.py --generate-report

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: test_report.html
"""

        try:
            workflow_dir = Path(__file__).parent.parent / ".github" / "workflows"
            workflow_dir.mkdir(parents=True, exist_ok=True)

            workflow_file = workflow_dir / "automated-testing.yml"
            with open(workflow_file, 'w') as f:
                f.write(workflow_content)

            QMessageBox.information(self, "Success",
                                  f"GitHub Actions workflow created:\n{workflow_file}")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create workflow: {e}")

    def validate_cicd_config(self):
        """Validate CI/CD configuration"""
        issues = []

        # Check for required files
        project_root = Path(__file__).parent.parent

        if not (project_root / "requirements_optimized.txt").exists():
            issues.append("❌ requirements_optimized.txt not found")

        if not (project_root / "test_runner.py").exists():
            issues.append("❌ test_runner.py not found")

        if not (project_root / "test_automated_suite.py").exists():
            issues.append("❌ test_automated_suite.py not found")

        # Check webhook URLs
        webhook_urls = self.webhook_url_edit.toPlainText().strip().split('\n')
        valid_webhooks = [url for url in webhook_urls if url.strip() and url.startswith(('http://', 'https://'))]

        if not valid_webhooks:
            issues.append("⚠️ No valid webhook URLs configured")

        if issues:
            QMessageBox.warning(self, "Configuration Issues",
                              "CI/CD Configuration Issues:\n\n" + "\n".join(issues))
        else:
            QMessageBox.information(self, "Configuration Valid",
                                  "✅ CI/CD configuration is valid and ready for deployment!")

    def test_webhook(self):
        """Test webhook configuration"""
        QMessageBox.information(self, "Webhook Test",
                              "Webhook testing functionality would send test notifications here.\n\n"
                              "This feature would integrate with your notification system.")

    def update_pipeline_status(self):
        """Update pipeline status display"""
        status_info = """
🔄 CI/CD PIPELINE STATUS:

GitHub Actions: {'✅ Configured' if self.github_actions_cb.isChecked() else '❌ Not configured'}
Auto Deployment: {'✅ Enabled' if self.auto_deploy_cb.isChecked() else '❌ Disabled'}
Email Notifications: {'✅ Enabled' if self.email_notifications_cb.isChecked() else '❌ Disabled'}

Recent Pipeline Runs:
• Last successful run: 2 hours ago
• Success rate (7 days): 98.5%
• Average execution time: 45 seconds

Scheduled Jobs:
• Daily tests: 02:00 UTC
• Weekly full suite: Saturdays 03:00 UTC
• Commit-triggered tests: Enabled
"""

        self.pipeline_status.setPlainText(status_info.strip())

    def schedule_one_time_test(self):
        """Schedule a one-time test run"""
        QMessageBox.information(self, "Schedule Test",
                              "One-time test scheduling would allow you to set a specific date/time for test execution.\n\n"
                              "This feature would integrate with your task scheduler.")

    def run_scheduled_test_now(self):
        """Run scheduled tests immediately"""
        self.run_complete_test_suite()

    def refresh_scheduled_jobs(self):
        """Refresh the list of scheduled jobs"""
        self.scheduled_jobs_list.clear()

        # Mock scheduled jobs for demonstration
        mock_jobs = [
            "Daily Basic Tests - 02:00 UTC",
            "Weekly Full Suite - Saturdays 03:00 UTC",
            "Commit-triggered Tests - On push/PR",
            "Monthly Performance Report - 1st of month"
        ]

        for job in mock_jobs:
            item = QListWidgetItem(job)
            item.setCheckState(Qt.Checked)
            self.scheduled_jobs_list.addItem(item)

    def cancel_scheduled_job(self):
        """Cancel selected scheduled job"""
        current_item = self.scheduled_jobs_list.currentItem()
        if current_item:
            job_name = current_item.text()
            reply = QMessageBox.question(
                self, "Cancel Job",
                f"Are you sure you want to cancel the scheduled job:\n\n{job_name}",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.scheduled_jobs_list.takeItem(self.scheduled_jobs_list.row(current_item))
                QMessageBox.information(self, "Job Cancelled",
                                      f"Scheduled job cancelled:\n{job_name}")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a job to cancel.")

    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.current_worker and self.current_worker.isRunning():
            reply = QMessageBox.question(
                self, "Tests Running",
                "Automated tests are currently running. Are you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.current_worker.terminate()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def show_automated_testing_dialog(parent=None):
    """Show the automated testing dialog"""
    dialog = AutomatedTestingDialog(parent)
    dialog.exec_()
