
import os
import sqlite3
import sys
from datetime import datetime

# Qt Graphics/Platform Configuration for crash prevention
os.environ["QT_QPA_PLATFORM"] = "windows"
os.environ["QT_OPENGL"] = (
    "software"  # Force software rendering to avoid graphics driver issues
)
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"  # Disable auto scaling
os.environ["QT_SCALE_FACTOR"] = "1"  # Fixed scale factor
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"  # Disable high DPI scaling
os.environ["QT_LOGGING_RULES"] = "qt.qpa.plugin=false"  # Reduce plugin logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import PyQt5 modules
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAction, QApplication, QHBoxLayout, QLabel,
                             QListWidgetItem, QMainWindow, QMessageBox,
                             QVBoxLayout, QWidget)

# Set Qt attributes BEFORE creating QApplication
QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)  # Force software OpenGL
QApplication.setAttribute(
    Qt.AA_DontCreateNativeWidgetSiblings, True
)  # Prevent native widget issues
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, False)  # Disable high DPI pixmaps
from scripts.case_management import (AddNewCaseDialog, EditCasesDialog,
                                     ToDoListDialog, ViewCasesDialog,
                                     ViewDeletedCasesDialog)
from scripts.case_management_modules.write_off_management_dialog import \
    WriteOffManagementDialog
from scripts.case_management_modules.write_off_submission_dialog import \
    WriteOffSubmissionDialog
from scripts.category_management import ManageCategoriesDialog
from scripts.email_template_management import ManageEmailTemplatesDialog
from scripts.financial_year_management import FinancialYearManagementDialog
from scripts.list_management import ManageListsDialog
from scripts.report_management import ReportManagementDialog
from scripts.responsibility_management_ui import ResponsibilityManagementDialog
from scripts.ui.dialogs.checklist_dialog import ChecklistDialog
from scripts.ui.dialogs.import_cases_dialog import import_undisclosed_cases
from scripts.ui.dialogs.import_cases_dialog_core import \
    ImportUndisclosedCasesDialog
from scripts.ui.dialogs.admin.delegation_manager import DelegationManagerDialog
from scripts.ui.dialogs.annexure_preparation_dialog import AnnexurePreparationDialog
from scripts.Utilities.config import DB_PATH, initialize_shared_documents_table
from scripts.Utilities.financial_utils import get_active_period_display
from scripts.Utilities.qt_diagnostics import (apply_qt_fixes,
                                              check_qt_compatibility,
                                              print_qt_diagnostics)
from scripts.Utilities.ui_theme import apply_theme, create_status_label
from scripts.Utilities.logging_utils import configure_logging
from scripts.wipe_cases_dialog import WipeCasesDialog
from scripts.optimization_management import open_optimization_management


class FWManagementApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "FWMIS - Fruitless and Wasteful Expenditure Management Information System"
        )

        # Set minimum size and allow resizing/maximizing
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)  # Default size
        self.center_window()

        # Enable maximize button and window resizing
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowMinimizeButtonHint
        )

        # Apply professional theme
        apply_theme(self)

        # Initialize database tables
        try:
            initialize_shared_documents_table()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Database Warning",
                f"Failed to initialize database tables: {str(e)}",
            )

        self.setup_ui()
        self.setup_menu()

    def center_window(self):
        """Center the window on the screen"""
        from PyQt5.QtWidgets import QDesktopWidget

        screen = QDesktopWidget().screenGeometry()
        # Use the default size for centering calculations
        window_width = 1200
        window_height = 800
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
        self.move(x, y)

    def setup_ui(self):
        # Create professional central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Welcome header
        active_period_text = get_active_period_display()
        if active_period_text:
            welcome_text = f"Welcome to the FWMIS\n{active_period_text}"
        else:
            welcome_text = "Welcome to the FWMIS"

        welcome_label = QLabel(welcome_text)
        welcome_label.setWordWrap(True)
        welcome_label.setAlignment(Qt.AlignCenter)  # Center align the text within the label
        welcome_label.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: 600;
                font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
                color: #1a365d;
                margin-bottom: 10px;
            }
        """
        )
        layout.addWidget(welcome_label, alignment=Qt.AlignCenter)

        # Subtitle
        subtitle_label = QLabel(
            "Fruitless and Wasteful Expenditure Management Information System"
        )
        subtitle_label.setAlignment(Qt.AlignCenter)  # Center align the text within the label
        subtitle_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
                color: #4a5568;
                margin-bottom: 30px;
            }
        """
        )
        layout.addWidget(subtitle_label, alignment=Qt.AlignCenter)

        # Quick actions section
        actions_group = QWidget()
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(15)

        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: 600;
                font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
                color: #2d3748;
                margin-bottom: 15px;
            }
        """
        )
        actions_layout.addWidget(actions_title, alignment=Qt.AlignCenter)

        # Action buttons in a grid
        from PyQt5.QtWidgets import QGridLayout, QPushButton
        from scripts.Utilities.ui_theme import create_professional_button

        buttons_layout = QGridLayout()
        buttons_layout.setSpacing(15)

        # Create professional corporate action buttons
        add_case_btn = create_professional_button("Add New Case", "success", "large")
        add_case_btn.clicked.connect(self.add_new_case)
        buttons_layout.addWidget(add_case_btn, 0, 0)

        view_cases_btn = create_professional_button("View Cases", "primary", "large")
        view_cases_btn.clicked.connect(self.view_cases)
        buttons_layout.addWidget(view_cases_btn, 0, 1)

        import_cases_btn = create_professional_button(
            "Import Cases", "info", "large"
        )
        import_cases_btn.clicked.connect(self.import_undisclosed_cases)
        buttons_layout.addWidget(import_cases_btn, 1, 0)

        reports_btn = create_professional_button(
            "Generate Reports", "warning", "large"
        )
        reports_btn.clicked.connect(self.generate_reports)
        buttons_layout.addWidget(reports_btn, 1, 1)

        actions_layout.addLayout(buttons_layout)
        layout.addWidget(actions_group)


        # Add stretch to push everything to the top
        layout.addStretch()

    def refresh_cases(self):
        """Refresh cases display - placeholder for future implementation"""
        # This method can be implemented later if needed for refreshing the main window
        pass

    def setup_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        # Management actions
        responsibilities_action = QAction("Manage Responsibilities", self)
        responsibilities_action.triggered.connect(self.manage_responsibilities)
        file_menu.addAction(responsibilities_action)

        email_templates_action = QAction("Manage Email Templates", self)
        email_templates_action.triggered.connect(self.manage_email_templates)
        file_menu.addAction(email_templates_action)

        file_menu.addSeparator()  # Separator before Exit

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Cases menu
        cases_menu = menubar.addMenu("Cases")
        add_case_action = QAction("Add New Case", self)
        add_case_action.triggered.connect(self.add_new_case)
        cases_menu.addAction(add_case_action)

        import_cases_action = QAction("Import Undisclosed Cases", self)
        import_cases_action.triggered.connect(self.import_undisclosed_cases)
        cases_menu.addAction(import_cases_action)

        cases_menu.addSeparator()  # Add separator

        view_cases_action = QAction("View Cases", self)
        view_cases_action.triggered.connect(self.view_cases)
        cases_menu.addAction(view_cases_action)
        edit_cases_action = QAction("Edit Cases", self)
        edit_cases_action.triggered.connect(
            self.manage_cases
        )  # Reusing existing method
        cases_menu.addAction(edit_cases_action)

        cases_menu.addSeparator()  # Add separator

        # Write-off management
        prepare_annexures_action = QAction("Prepare Write-Off Annexures", self)
        prepare_annexures_action.triggered.connect(self.prepare_write_off_annexures)
        cases_menu.addAction(prepare_annexures_action)

        create_write_off_action = QAction("Create Write-Off Submission", self)
        create_write_off_action.triggered.connect(self.create_write_off_submission)
        cases_menu.addAction(create_write_off_action)

        manage_write_off_action = QAction("Manage Write-Off Submissions", self)
        manage_write_off_action.triggered.connect(self.manage_write_off_submissions)
        cases_menu.addAction(manage_write_off_action)

        # To-Do List as standalone main menu
        todo_menu = menubar.addMenu("To-Do List")
        todo_action = QAction("View To-Do List", self)
        todo_action.triggered.connect(self.todo_list)
        todo_menu.addAction(todo_action)

        # View menu with sub-menu items
        view_menu = menubar.addMenu("View")
        checklist_action = QAction("Checklist", self)
        checklist_action.triggered.connect(self.view_checklist)
        view_menu.addAction(checklist_action)

        lead_schedule_action = QAction("Lead Schedule", self)
        lead_schedule_action.triggered.connect(self.view_lead_schedule)
        view_menu.addAction(lead_schedule_action)

        deleted_items_action = QAction("Deleted Items", self)
        deleted_items_action.triggered.connect(self.view_deleted_items)
        view_menu.addAction(deleted_items_action)

        deleted_cases_action = QAction("Deleted Cases", self)
        deleted_cases_action.triggered.connect(self.view_deleted_cases)
        view_menu.addAction(deleted_cases_action)

        # Administrator menu with Manage submenu
        admin_menu = menubar.addMenu("Administrator")
        manage_submenu = admin_menu.addMenu("Manage")

        # Add management items to Administrator > Manage
        categories_action = QAction("Categories", self)
        categories_action.triggered.connect(self.manage_categories)
        manage_submenu.addAction(categories_action)

        lists_action = QAction("Lists", self)
        lists_action.triggered.connect(self.manage_lists)
        manage_submenu.addAction(lists_action)

        # Add Financial Years to Administrator > Manage
        fy_action = QAction("Financial Years", self)
        fy_action.triggered.connect(self.manage_financial_years)
        manage_submenu.addAction(fy_action)

        # Add Write-Off Delegations to Administrator > Manage
        delegations_action = QAction("Write-Off Delegations", self)
        delegations_action.triggered.connect(self.manage_write_off_delegations)
        manage_submenu.addAction(delegations_action)

        # Add Performance Optimization Management
        optimization_action = QAction("Performance Optimization", self)
        optimization_action.triggered.connect(self.open_optimization_management)
        optimization_action.setToolTip("Configure performance optimizations for large datasets")
        admin_menu.addAction(optimization_action)

        # Add separator before system management
        admin_menu.addSeparator()

        # Database Archiving Management
        archiving_action = QAction("🗄️ Database Archiving", self)
        archiving_action.triggered.connect(self.open_database_archiving)
        archiving_action.setToolTip("Manage database archiving for performance optimization")
        admin_menu.addAction(archiving_action)

        # Automated Testing Management
        testing_action = QAction("🧪 Automated Testing", self)
        testing_action.triggered.connect(self.open_automated_testing)
        testing_action.setToolTip("Run automated tests and manage CI/CD integration")
        admin_menu.addAction(testing_action)

        # Test Verification Management
        verification_action = QAction("🔍 Test Verification", self)
        verification_action.triggered.connect(self.run_daily_test_verification)
        verification_action.setToolTip("Run daily test verification to check coverage and integration")
        admin_menu.addAction(verification_action)

        # Add separator before dangerous operations
        admin_menu.addSeparator()

        # Wipe Cases action (dangerous operation)
        wipe_cases_action = QAction("Wipe Cases (Dangerous)", self)
        wipe_cases_action.triggered.connect(self.wipe_cases)
        wipe_cases_action.setToolTip(
            "Permanently delete all cases for a selected financial year"
        )
        admin_menu.addAction(wipe_cases_action)

        # Reports menu
        reports_menu = menubar.addMenu("Reports")
        generate_report_action = QAction("Generate Reports", self)
        generate_report_action.triggered.connect(self.generate_reports)
        reports_menu.addAction(generate_report_action)

    def add_new_case(self):
        try:
            dialog = AddNewCaseDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Add New Case dialog: {str(e)}"
            )

    def import_undisclosed_cases(self):
        try:
            import_undisclosed_cases(self)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open Import Undisclosed Cases dialog: {str(e)}",
            )

    def view_cases(self):
        try:
            dialog = ViewCasesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open View Cases dialog: {str(e)}"
            )

    def manage_cases(self):
        try:
            dialog = EditCasesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Edit Cases dialog: {str(e)}"
            )

    def todo_list(self):
        try:
            dialog = ToDoListDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open To-Do List dialog: {str(e)}"
            )

    def manage_categories(self):
        try:
            dialog = ManageCategoriesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Manage Categories dialog: {str(e)}"
            )

    def manage_lists(self):
        try:
            dialog = ManageListsDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Manage Lists dialog: {str(e)}"
            )

    def manage_responsibilities(self):
        try:
            dialog = ResponsibilityManagementDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open Manage Responsibilities dialog: {str(e)}",
            )

    def manage_email_templates(self):
        try:
            dialog = ManageEmailTemplatesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Manage Email Templates dialog: {str(e)}"
            )

    def generate_reports(self):
        try:
            dialog = ReportManagementDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Generate Reports dialog: {str(e)}"
            )

    def manage_financial_years(self):
        try:
            dialog = FinancialYearManagementDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open Financial Year Management dialog: {str(e)}",
            )

    def wipe_cases(self):
        try:
            dialog = WipeCasesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Wipe Cases dialog: {str(e)}"
            )

    def view_checklist(self):
        try:
            dialog = ChecklistDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Checklist dialog: {str(e)}"
            )

    def view_lead_schedule(self):
        pass

    def view_deleted_items(self):
        """Placeholder for Deleted Items view - to be implemented"""
        QMessageBox.information(
            self,
            "Deleted Items",
            "Deleted Items view functionality will be implemented here.",
        )

    def view_deleted_cases(self):
        """View cases in the Deleted Cases list"""
        try:
            dialog = ViewDeletedCasesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Deleted Cases view: {str(e)}"
            )

    def create_write_off_submission(self):
        """Create a new write-off submission"""
        try:
            dialog = WriteOffSubmissionDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Write-Off Submission dialog: {str(e)}"
            )

    def manage_write_off_submissions(self):
        """Manage existing write-off submissions"""
        try:
            dialog = WriteOffManagementDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Write-Off Management dialog: {str(e)}"
            )

    def open_optimization_management(self):
        """Open the performance optimization management dialog"""
        try:
            open_optimization_management(self)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Performance Optimization dialog: {str(e)}"
            )

    def open_database_archiving(self):
        """Open the database archiving management dialog"""
        try:
            from scripts.ui.dialogs.database_archiving_dialog import show_database_archiving_dialog
            show_database_archiving_dialog(self)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Database Archiving dialog: {str(e)}"
            )

    def open_automated_testing(self):
        """Open the automated testing and CI/CD integration dialog"""
        try:
            from scripts.ui.dialogs.automated_testing_dialog import show_automated_testing_dialog
            show_automated_testing_dialog(self)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Automated Testing dialog: {str(e)}"
            )

    def run_daily_test_verification(self):
        """Run the daily test verification script"""
        try:
            import subprocess
            import sys
            from pathlib import Path

            # Build verification command
            project_root = Path(__file__).parent.parent  # FWMIS directory
            script_path = project_root / "daily_test_verification.py"

            if not script_path.exists():
                QMessageBox.warning(
                    self, "Script Not Found",
                    f"Daily verification script not found at:\n{script_path}\n\n"
                    "Please ensure daily_test_verification.py exists in the project root."
                )
                return

            # Run the verification script
            command = [sys.executable, str(script_path)]
            working_dir = str(project_root)

            # Show progress dialog
            from PyQt5.QtWidgets import QProgressDialog
            progress = QProgressDialog("Running Test Verification...", "Cancel", 0, 0, self)
            progress.setWindowModality(2)  # Qt.WindowModal
            progress.setAutoClose(False)
            progress.setAutoReset(False)
            progress.show()

            try:
                # Run the verification
                result = subprocess.run(
                    command,
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 minute timeout
                )

                progress.close()

                # Show results
                from PyQt5.QtWidgets import QTextEdit, QVBoxLayout, QDialog, QDialogButtonBox

                result_dialog = QDialog(self)
                result_dialog.setWindowTitle("Test Verification Results")
                result_dialog.setModal(True)
                result_dialog.resize(900, 700)
                result_dialog.setMinimumSize(800, 600)

                layout = QVBoxLayout(result_dialog)

                # Title
                title_label = QLabel("🔍 Daily Test Verification Results")
                title_font = title_label.font()
                title_font.setPointSize(12)
                title_font.setBold(True)
                title_label.setFont(title_font)
                layout.addWidget(title_label)

                # Results text area
                results_text = QTextEdit()
                results_text.setPlainText(result.stdout)
                if result.stderr:
                    results_text.append("\n" + "="*50 + "\nSTDERR OUTPUT:\n" + "="*50)
                    results_text.append(result.stderr)
                results_text.setReadOnly(True)
                results_text.setFontFamily("Courier New")
                layout.addWidget(results_text)

                # Status summary
                summary_text = f"\nExit Code: {result.returncode}\n"
                if result.returncode == 0:
                    summary_text += "✅ VERIFICATION PASSED - All tests properly integrated!"
                else:
                    summary_text += "❌ VERIFICATION FAILED - Issues need attention!"

                status_label = QLabel(summary_text)
                if result.returncode == 0:
                    status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                else:
                    status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                layout.addWidget(status_label)

                # Buttons
                button_box = QDialogButtonBox(QDialogButtonBox.Ok)
                if result.returncode != 0:
                    # Add auto-fix button if there are issues
                    auto_fix_btn = button_box.addButton("🔧 Auto-Fix Issues", QDialogButtonBox.ActionRole)
                    auto_fix_btn.clicked.connect(lambda: self.run_verification_auto_fix(result_dialog))

                button_box.accepted.connect(result_dialog.accept)
                layout.addWidget(button_box)

                result_dialog.exec_()

            except subprocess.TimeoutExpired:
                progress.close()
                QMessageBox.warning(
                    self, "Timeout",
                    "Test verification timed out after 2 minutes.\n\n"
                    "The verification process may be taking too long or may be stuck."
                )
            except Exception as run_error:
                progress.close()
                QMessageBox.critical(
                    self, "Execution Error",
                    f"Failed to run test verification:\n{str(run_error)}"
                )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to run daily test verification: {str(e)}"
            )

    def run_verification_auto_fix(self, parent_dialog):
        """Run the verification auto-fix"""
        try:
            import subprocess
            import sys
            from pathlib import Path

            project_root = Path(__file__).parent.parent  # FWMIS directory
            script_path = project_root / "daily_test_verification.py"

            command = [sys.executable, str(script_path), "--auto-fix"]
            working_dir = str(project_root)

            # Run auto-fix
            result = subprocess.run(
                command,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Show auto-fix results
            from PyQt5.QtWidgets import QMessageBox

            if result.returncode == 0:
                QMessageBox.information(
                    parent_dialog, "Auto-Fix Completed",
                    "✅ Auto-fix completed successfully!\n\n"
                    "Common issues have been resolved.\n"
                    "Please re-run the verification to confirm."
                )
            else:
                QMessageBox.warning(
                    parent_dialog, "Auto-Fix Issues",
                    "❌ Auto-fix encountered issues:\n\n" +
                    result.stdout + "\n" + result.stderr + "\n\n" +
                    "Please check the output for details."
                )

        except Exception as e:
            QMessageBox.critical(
                parent_dialog, "Auto-Fix Error",
                f"Failed to run auto-fix: {str(e)}"
            )

    def manage_write_off_delegations(self):
        """Open the write-off delegation management dialog"""
        try:
            dialog = DelegationManagerDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Write-Off Delegations dialog: {str(e)}"
            )

    def prepare_write_off_annexures(self):
        """Open the annexure preparation dialog"""
        try:
            dialog = AnnexurePreparationDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open Annexure Preparation dialog: {str(e)}"
            )


def exception_handler(exctype, value, traceback):
    """Global exception handler to catch unhandled exceptions"""
    import traceback as tb

    error_msg = "".join(tb.format_exception(exctype, value, traceback))
    print(f"CRITICAL: Unhandled exception: {error_msg}")

    # Try to save emergency recovery information
    try:
        with open("emergency_recovery.log", "w") as f:
            f.write(f"Emergency Recovery Log\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Exception: {exctype.__name__}: {value}\n")
            f.write(f"Traceback:\n{error_msg}\n")
        print(
            "CRITICAL: Emergency recovery information saved to emergency_recovery.log"
        )
    except:
        print("CRITICAL: Could not save emergency recovery information")

    # Show error dialog if QApplication exists
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance()
        if app:
            reply = QMessageBox.critical(
                None,
                "Critical Application Error",
                f"A critical error occurred:\n\n{str(value)}\n\n"
                "Emergency recovery information has been saved.\n\n"
                "Would you like to restart the application?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                print("CRITICAL: User requested application restart")
                # Try to restart the application
                try:
                    import subprocess

                    subprocess.Popen([sys.executable] + sys.argv)
                    print("CRITICAL: Application restart initiated")
                except Exception as restart_error:
                    print(f"CRITICAL: Could not restart application: {restart_error}")
        else:
            QMessageBox.critical(
                None,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{str(value)}\n\nThe application will now close.",
            )
    except Exception as dialog_error:
        print(f"CRITICAL: Could not show error dialog: {dialog_error}")

    # Exit gracefully
    print("CRITICAL: Application shutting down due to critical error")
    sys.exit(1)


if __name__ == "__main__":
    # Install global exception handler
    sys.excepthook = exception_handler

    # Run Qt diagnostics and apply fixes
    # Initialize structured logging
    try:
        from scripts.Utilities.logging_utils import configure_logging

        configure_logging()
    except Exception:
        pass

    # Initialize performance monitoring and optimizations
    try:
        from scripts.Utilities.performance_profiler import (
            performance_profiler, memory_profiler, log_performance_report
        )
        from scripts.Utilities.optimization_manager import enable_all_optimizations
        
        # Enable all optimizations
        enable_all_optimizations()
        
        # Start performance monitoring
        memory_profiler.take_snapshot("app_start")
        performance_profiler.start_timer("app_initialization")
        log_performance_report()
    except Exception:
        pass

    # Run Qt diagnostics and apply fixes
    apply_qt_fixes()
    issues = check_qt_compatibility()
    if issues:
        for issue in issues:
            pass  # Issues detected, but no print
    else:
        pass

    try:
        app = QApplication(sys.argv)

        # Note: Qt message handler not available in this PyQt5 version
        # Qt internal errors will be caught by the global exception handler

        window = FWManagementApp()
        window.show()

        # Force process events before starting main loop
        app.processEvents()

        # Run the application with error handling
        try:
            exit_code = app.exec_()
        except Exception as event_error:
            import traceback

            traceback.print_exc()
            exit_code = 1

        sys.exit(exit_code)

    except Exception as e:
        import traceback

        traceback.print_exc()
        sys.exit(1)
