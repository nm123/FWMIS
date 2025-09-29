"""
UI Setup Module

Contains UI initialization and setup functionality for the automated testing dialog.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dialog import AutomatedTestingDialog


class UISetupManager:
    """
    Manages UI setup and initialization for the automated testing dialog.
    """

    def __init__(self, dialog: "AutomatedTestingDialog"):
        """
        Initialize the UI setup manager.

        Args:
            dialog: The parent AutomatedTestingDialog instance
        """
        self.dialog = dialog

    def setup_ui(self) -> None:
        """Set up the main dialog UI."""
        self.dialog.setWindowTitle("🧪 Automated Testing & CI/CD Integration")
        self.dialog.setModal(True)
        self.dialog.resize(1200, 800)
        self.dialog.setMinimumSize(1000, 600)

        # Create main layout
        from PyQt5.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(self.dialog)

        # Create tab widget
        from PyQt5.QtWidgets import QTabWidget

        self.dialog.tab_widget = QTabWidget()

        # Create tabs
        self._setup_execution_tab()
        self._setup_results_tab()
        self._setup_cicd_tab()
        self._setup_scheduling_tab()

        layout.addWidget(self.dialog.tab_widget)

        # Initialize other attributes
        self.dialog.current_worker = None
        self.dialog.test_history = []

    def _setup_execution_tab(self) -> None:
        """Set up the test execution tab."""
        from PyQt5.QtWidgets import (
            QCheckBox,
            QComboBox,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )

        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Test Options Group
        options_group = QGroupBox("Test Configuration")
        options_layout = QVBoxLayout(options_group)

        # Test type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Test Suite:"))
        self.dialog.test_type_combo = QComboBox()
        self.dialog.test_type_combo.addItems(
            [
                "Complete Test Suite",
                "Unit Tests Only",
                "Integration Tests Only",
                "Performance Tests Only",
            ]
        )
        self.dialog.test_type_combo.currentTextChanged.connect(
            self.dialog.update_test_options
        )
        type_layout.addWidget(self.dialog.test_type_combo)
        type_layout.addStretch()
        options_layout.addLayout(type_layout)

        # Test options checkboxes
        self.dialog.verbose_checkbox = QCheckBox("Verbose output")
        self.dialog.verbose_checkbox.setChecked(True)
        options_layout.addWidget(self.dialog.verbose_checkbox)

        self.dialog.coverage_checkbox = QCheckBox("Generate coverage report")
        options_layout.addWidget(self.dialog.coverage_checkbox)

        self.dialog.parallel_checkbox = QCheckBox("Run tests in parallel")
        options_layout.addWidget(self.dialog.parallel_checkbox)

        layout.addWidget(options_group)

        # Test Discovery Status
        discovery_group = QGroupBox("Test Discovery")
        discovery_layout = QVBoxLayout(discovery_group)

        # Discovery status and refresh button
        discovery_header_layout = QHBoxLayout()
        self.dialog.discovered_tests_label = QLabel("Scanning for tests...")
        discovery_header_layout.addWidget(self.dialog.discovered_tests_label)

        refresh_discovery_btn = QPushButton("🔄 Refresh")
        refresh_discovery_btn.clicked.connect(self.dialog.refresh_discovered_tests)
        discovery_header_layout.addWidget(refresh_discovery_btn)
        discovery_layout.addLayout(discovery_header_layout)

        # Test files list
        from PyQt5.QtWidgets import QListWidget
        self.dialog.test_files_list = QListWidget()
        self.dialog.test_files_list.setMaximumHeight(150)
        discovery_layout.addWidget(self.dialog.test_files_list)

        layout.addWidget(discovery_group)

        # Quick Action Buttons
        buttons_layout = QHBoxLayout()

        self.dialog.run_complete_btn = QPushButton("🚀 Run Complete Test Suite")
        self.dialog.run_complete_btn.setToolTip("Run all discovered test files automatically")
        self.dialog.run_complete_btn.clicked.connect(
            self.dialog.run_complete_test_suite
        )
        buttons_layout.addWidget(self.dialog.run_complete_btn)

        self.dialog.run_verification_btn = QPushButton("🔍 Run Daily Verification")
        self.dialog.run_verification_btn.clicked.connect(
            self.dialog.run_daily_verification
        )
        buttons_layout.addWidget(self.dialog.run_verification_btn)

        layout.addLayout(buttons_layout)

        # Progress and Output
        progress_group = QGroupBox("Execution Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.dialog.progress_label = QLabel("Ready to run tests")
        progress_layout.addWidget(self.dialog.progress_label)

        from PyQt5.QtWidgets import QProgressBar

        self.dialog.progress_bar = QProgressBar()
        self.dialog.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.dialog.progress_bar.setVisible(False)
        progress_layout.addWidget(self.dialog.progress_bar)

        self.dialog.output_text = QTextEdit()
        self.dialog.output_text.setReadOnly(True)
        self.dialog.output_text.setMaximumHeight(300)
        progress_layout.addWidget(self.dialog.output_text)

        layout.addWidget(progress_group)

        self.dialog.tab_widget.addTab(tab, "⚡ Execution")

    def _setup_results_tab(self) -> None:
        """Set up the test results tab."""
        from PyQt5.QtWidgets import (
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QTableWidget,
            QTableWidgetItem,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )

        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Summary Section
        summary_group = QGroupBox("Test Summary")
        summary_layout = QVBoxLayout(summary_group)

        # Verification status
        verification_layout = QHBoxLayout()
        verification_layout.addWidget(QLabel("Daily Verification:"))
        self.dialog.verification_status_label = QLabel("Not run")
        verification_layout.addWidget(self.dialog.verification_status_label)
        verification_layout.addStretch()
        verification_layout.addWidget(QLabel("Last run:"))
        self.dialog.last_verification_label = QLabel("Never")
        verification_layout.addWidget(self.dialog.last_verification_label)
        summary_layout.addLayout(verification_layout)

        # Performance metrics
        perf_layout = QHBoxLayout()
        perf_layout.addWidget(QLabel("Average Duration:"))
        self.dialog.avg_duration_label = QLabel("N/A")
        perf_layout.addWidget(self.dialog.avg_duration_label)
        perf_layout.addStretch()
        perf_layout.addWidget(QLabel("Success Rate:"))
        self.dialog.success_rate_label = QLabel("N/A")
        perf_layout.addWidget(self.dialog.success_rate_label)
        summary_layout.addLayout(perf_layout)

        layout.addWidget(summary_group)

        # Results Table
        table_group = QGroupBox("Test History")
        table_layout = QVBoxLayout(table_group)

        self.dialog.results_table = QTableWidget()
        self.dialog.results_table.setColumnCount(4)
        self.dialog.results_table.setHorizontalHeaderLabels(
            ["Timestamp", "Type", "Result", "Duration"]
        )
        self.dialog.results_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.dialog.results_table)

        # Table buttons
        buttons_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.dialog.load_test_history)
        buttons_layout.addWidget(refresh_btn)

        analyze_btn = QPushButton("📊 Analyze Trends")
        analyze_btn.clicked.connect(self.dialog.analyze_performance_trends)
        buttons_layout.addWidget(analyze_btn)

        buttons_layout.addStretch()
        table_layout.addLayout(buttons_layout)

        layout.addWidget(table_group)

        # Recommendations section
        rec_group = QGroupBox("Recommendations")
        rec_layout = QVBoxLayout(rec_group)

        self.dialog.recommendations_text = QTextEdit()
        self.dialog.recommendations_text.setReadOnly(True)
        self.dialog.recommendations_text.setMaximumHeight(150)
        rec_layout.addWidget(self.dialog.recommendations_text)

        layout.addWidget(rec_group)

        self.dialog.tab_widget.addTab(tab, "📊 Results")

    def _setup_cicd_tab(self) -> None:
        """Set up the CI/CD integration tab."""
        from PyQt5.QtWidgets import (
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QPushButton,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )

        tab = QWidget()
        layout = QVBoxLayout(tab)

        # GitHub Integration
        github_group = QGroupBox("GitHub Integration")
        github_layout = QVBoxLayout(github_group)

        # Repository settings
        repo_layout = QHBoxLayout()
        repo_layout.addWidget(QLabel("Repository:"))
        self.dialog.repo_input = QLineEdit("owner/repository")
        repo_layout.addWidget(self.dialog.repo_input)
        github_layout.addLayout(repo_layout)

        # Workflow generation
        workflow_layout = QHBoxLayout()
        generate_workflow_btn = QPushButton("🚀 Generate GitHub Workflow")
        generate_workflow_btn.clicked.connect(self.dialog.generate_github_workflow)
        workflow_layout.addWidget(generate_workflow_btn)

        validate_btn = QPushButton("✅ Validate Configuration")
        validate_btn.clicked.connect(self.dialog.validate_cicd_config)
        workflow_layout.addWidget(validate_btn)

        workflow_layout.addStretch()
        github_layout.addLayout(workflow_layout)

        layout.addWidget(github_group)

        # Webhook Testing
        webhook_group = QGroupBox("Webhook Testing")
        webhook_layout = QVBoxLayout(webhook_group)

        webhook_layout.addWidget(QLabel("Test webhook endpoints and payload handling:"))

        test_webhook_btn = QPushButton("🔗 Test Webhook")
        test_webhook_btn.clicked.connect(self.dialog.test_webhook)
        webhook_layout.addWidget(test_webhook_btn)

        layout.addWidget(webhook_group)

        # Pipeline Status
        status_group = QGroupBox("Pipeline Status")
        status_layout = QVBoxLayout(status_group)

        self.dialog.pipeline_status_text = QTextEdit()
        self.dialog.pipeline_status_text.setReadOnly(True)
        self.dialog.pipeline_status_text.setMaximumHeight(200)
        status_layout.addWidget(self.dialog.pipeline_status_text)

        refresh_status_btn = QPushButton("🔄 Refresh Status")
        refresh_status_btn.clicked.connect(self.dialog.update_pipeline_status)
        status_layout.addWidget(refresh_status_btn)

        layout.addWidget(status_group)

        self.dialog.tab_widget.addTab(tab, "🔄 CI/CD")

    def _setup_scheduling_tab(self) -> None:
        """Set up the test scheduling tab."""
        from PyQt5.QtWidgets import (
            QDateTimeEdit,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )

        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Scheduled Tests
        schedule_group = QGroupBox("Scheduled Tests")
        schedule_layout = QVBoxLayout(schedule_group)

        # Schedule new test
        new_test_layout = QHBoxLayout()
        self.dialog.schedule_datetime = QDateTimeEdit()
        self.dialog.schedule_datetime.setDateTime(
            self.dialog.schedule_datetime.dateTime().addDays(1)
        )
        new_test_layout.addWidget(QLabel("Schedule for:"))
        new_test_layout.addWidget(self.dialog.schedule_datetime)

        schedule_btn = QPushButton("📅 Schedule Test")
        schedule_btn.clicked.connect(self.dialog.schedule_one_time_test)
        new_test_layout.addWidget(schedule_btn)

        schedule_layout.addLayout(new_test_layout)

        # Scheduled jobs list
        schedule_layout.addWidget(QLabel("Scheduled Jobs:"))
        self.dialog.scheduled_jobs_list = QListWidget()
        schedule_layout.addWidget(self.dialog.scheduled_jobs_list)

        # Job management buttons
        job_buttons_layout = QHBoxLayout()
        run_now_btn = QPushButton("▶️ Run Now")
        run_now_btn.clicked.connect(self.dialog.run_scheduled_test_now)
        job_buttons_layout.addWidget(run_now_btn)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.dialog.cancel_scheduled_job)
        job_buttons_layout.addWidget(cancel_btn)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.dialog.refresh_scheduled_jobs)
        job_buttons_layout.addWidget(refresh_btn)

        job_buttons_layout.addStretch()
        schedule_layout.addLayout(job_buttons_layout)

        layout.addWidget(schedule_group)

        self.dialog.tab_widget.addTab(tab, "⏰ Scheduling")
