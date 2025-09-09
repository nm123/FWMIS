import sys
import os
import sqlite3
from datetime import datetime

# Qt Graphics/Platform Configuration for crash prevention
os.environ['QT_QPA_PLATFORM'] = 'windows'
os.environ['QT_OPENGL'] = 'software'  # Force software rendering to avoid graphics driver issues
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'  # Disable auto scaling
os.environ['QT_SCALE_FACTOR'] = '1'  # Fixed scale factor
os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0'  # Disable high DPI scaling
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.plugin=false'  # Reduce plugin logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import PyQt5 modules
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QAction,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QLabel,
    QListWidgetItem,
)

# Set Qt attributes BEFORE creating QApplication
print("DEBUG: Setting Qt attributes before QApplication creation")
QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)  # Force software OpenGL
QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)  # Prevent native widget issues
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, False)  # Disable high DPI pixmaps
print("DEBUG: Qt application attributes set before QApplication creation")
from scripts.Utilities.ui_theme import apply_theme, create_status_label
from scripts.case_management import AddNewCaseDialog, ViewCasesDialog, EditCasesDialog, ToDoListDialog, ViewDeletedCasesDialog
from scripts.ui.dialogs.import_cases_dialog import import_undisclosed_cases
from scripts.case_management_modules.bulk_case_entry import BulkCaseEntryWizard
from scripts.case_management_modules.write_off_submission_dialog import WriteOffSubmissionDialog
from scripts.case_management_modules.write_off_management_dialog import WriteOffManagementDialog
from scripts.category_management import ManageCategoriesDialog
from scripts.list_management import ManageListsDialog
from scripts.email_template_management import ManageEmailTemplatesDialog
from scripts.responsibility_management_ui import ResponsibilityManagementDialog
from scripts.report_management import ReportManagementDialog
from scripts.financial_year_management import FinancialYearManagementDialog
from scripts.Utilities.config import initialize_shared_documents_table, DB_PATH
from scripts.Utilities.financial_utils import get_active_period_display
from scripts.Utilities.qt_diagnostics import apply_qt_fixes, print_qt_diagnostics, check_qt_compatibility

class FWManagementApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 FWMIS - Fruitless and Wasteful Expenditure Management System")

        # Set minimum size and allow resizing/maximizing
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)  # Default size
        self.center_window()

        # Enable maximize button and window resizing
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)

        # Apply professional theme
        apply_theme(self)

        # Initialize database tables
        try:
            print("DEBUG: Initializing database tables")
            initialize_shared_documents_table()
            print("DEBUG: Database tables initialized successfully")
        except Exception as e:
            print(f"DEBUG: Error initializing database: {e}")
            QMessageBox.warning(self, "Database Warning", f"Failed to initialize database tables: {str(e)}")

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
            welcome_text = f"🏢 Welcome to FWMIS\n{active_period_text}"
        else:
            welcome_text = "🏢 Welcome to FWMIS"

        welcome_label = QLabel(welcome_text)
        welcome_label.setWordWrap(True)
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #343a40;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(welcome_label, alignment=Qt.AlignCenter)

        # Subtitle
        subtitle_label = QLabel("Fruitless and Wasteful Expenditure Management Information System")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #6c757d;
                margin-bottom: 30px;
            }
        """)
        layout.addWidget(subtitle_label, alignment=Qt.AlignCenter)

        # Quick actions section
        actions_group = QWidget()
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(15)

        actions_title = QLabel("🚀 Quick Actions")
        actions_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #495057;
                margin-bottom: 15px;
            }
        """)
        actions_layout.addWidget(actions_title, alignment=Qt.AlignCenter)

        # Action buttons in a grid
        from PyQt5.QtWidgets import QGridLayout, QPushButton
        from scripts.Utilities.ui_theme import create_professional_button

        buttons_layout = QGridLayout()
        buttons_layout.setSpacing(15)

        # Create professional action buttons
        add_case_btn = create_professional_button("➕ Add New Case", "success", "large")
        add_case_btn.clicked.connect(self.add_new_case)
        buttons_layout.addWidget(add_case_btn, 0, 0)

        view_cases_btn = create_professional_button("👁️ View Cases", "primary", "large")
        view_cases_btn.clicked.connect(self.view_cases)
        buttons_layout.addWidget(view_cases_btn, 0, 1)

        import_cases_btn = create_professional_button("📊 Import Cases", "info", "large")
        import_cases_btn.clicked.connect(self.import_undisclosed_cases)
        buttons_layout.addWidget(import_cases_btn, 1, 0)

        reports_btn = create_professional_button("📈 Generate Reports", "warning", "large")
        reports_btn.clicked.connect(self.generate_reports)
        buttons_layout.addWidget(reports_btn, 1, 1)

        actions_layout.addLayout(buttons_layout)
        layout.addWidget(actions_group)

        # Status information
        status_label = create_status_label("ℹ️ System ready. Use the menu above or quick actions below to get started.", "info")
        layout.addWidget(status_label)

        # Add stretch to push everything to the top
        layout.addStretch()

    def refresh_cases(self):
        """Refresh cases display - placeholder for future implementation"""
        print("DEBUG: refresh_cases called on main window")
        # This method can be implemented later if needed for refreshing the main window
        pass

    def setup_menu(self):
        menubar = self.menuBar()

        # File menu with Exit option only
        file_menu = menubar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Cases menu
        cases_menu = menubar.addMenu("Cases")
        add_case_action = QAction("Add New Case", self)
        add_case_action.triggered.connect(self.add_new_case)
        cases_menu.addAction(add_case_action)

        bulk_case_action = QAction("Bulk Case Entry", self)
        bulk_case_action.triggered.connect(self.bulk_case_entry)
        cases_menu.addAction(bulk_case_action)

        import_cases_action = QAction("Import Undisclosed Cases", self)
        import_cases_action.triggered.connect(self.import_undisclosed_cases)
        cases_menu.addAction(import_cases_action)

        cases_menu.addSeparator()  # Add separator

        view_cases_action = QAction("View Cases", self)
        view_cases_action.triggered.connect(self.view_cases)
        cases_menu.addAction(view_cases_action)
        edit_cases_action = QAction("Edit Cases", self)
        edit_cases_action.triggered.connect(self.manage_cases)  # Reusing existing method
        cases_menu.addAction(edit_cases_action)

        cases_menu.addSeparator()  # Add separator

        # Write-off management
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

        responsibilities_action = QAction("Responsibilities", self)
        responsibilities_action.triggered.connect(self.manage_responsibilities)
        manage_submenu.addAction(responsibilities_action)

        email_templates_action = QAction("Email Templates", self)
        email_templates_action.triggered.connect(self.manage_email_templates)
        manage_submenu.addAction(email_templates_action)

        # Add Financial Years to Administrator > Manage
        fy_action = QAction("Financial Years", self)
        fy_action.triggered.connect(self.manage_financial_years)
        manage_submenu.addAction(fy_action)

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
            QMessageBox.critical(self, "Error", f"Failed to open Add New Case dialog: {str(e)}")

    def bulk_case_entry(self):
        try:
            wizard = BulkCaseEntryWizard(self)
            wizard.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Bulk Case Entry wizard: {str(e)}")

    def import_undisclosed_cases(self):
        try:
            import_undisclosed_cases(self)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Import Undisclosed Cases dialog: {str(e)}")

    def view_cases(self):
        try:
            dialog = ViewCasesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open View Cases dialog: {str(e)}")

    def manage_cases(self):
        try:
            print("DEBUG: Opening Edit Cases dialog")
            dialog = EditCasesDialog(self)
            print("DEBUG: EditCasesDialog created successfully")

            # Test dialog display before showing
            try:
                dialog.show()
                dialog.hide()  # Hide immediately to test
                print("DEBUG: Dialog display test successful")
            except Exception as display_test_error:
                print(f"DEBUG: Dialog display test failed: {display_test_error}")
                # Try to create a simplified fallback dialog
                self.show_fallback_edit_dialog()
                return

            # Connect to dialog's signals to monitor for issues
            def on_dialog_finished(result):
                print(f"DEBUG: EditCasesDialog finished with result: {result}")

            def on_dialog_destroyed():
                print("DEBUG: EditCasesDialog destroyed")

            dialog.finished.connect(on_dialog_finished)
            dialog.destroyed.connect(on_dialog_destroyed)
            print("DEBUG: Connected to dialog finished and destroyed signals")

            # Add additional Qt error monitoring
            print("DEBUG: About to call dialog.show()")
            dialog.show()
            print("DEBUG: dialog.show() completed")

            print("DEBUG: About to call dialog.raise_()")
            dialog.raise_()
            print("DEBUG: dialog.raise_() completed")

            print("DEBUG: About to call dialog.activateWindow()")
            dialog.activateWindow()
            print("DEBUG: dialog.activateWindow() completed")

            print("DEBUG: About to call app.processEvents()")
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.processEvents()
                print("DEBUG: app.processEvents() completed")

            print("DEBUG: About to call dialog.exec_()")

            # Add emergency crash protection
            import signal
            import os

            def emergency_handler(signum, frame):
                print("EMERGENCY: Application received termination signal")
                print(f"EMERGENCY: Signal: {signum}")
                try:
                    # Try to show emergency dialog
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.critical(None, "Emergency Shutdown",
                                       "Application experienced a critical error and must shut down.\n\n"
                                       "Please restart the application and try again.")
                except:
                    print("EMERGENCY: Could not show emergency dialog")

                # Force exit
                os._exit(1)

            # Set up emergency signal handlers
            old_sigterm = signal.signal(signal.SIGTERM, emergency_handler)
            old_sigint = signal.signal(signal.SIGINT, emergency_handler)

            print("DEBUG: Using non-modal dialog approach to avoid Qt crash")

            # Use non-modal approach to avoid Qt modal dialog crash
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()

            # Set up result tracking for non-modal dialog
            dialog_result = [None]  # Use list to allow modification in nested function

            def on_dialog_finished(result):
                print(f"DEBUG: Non-modal dialog finished with result: {result}")
                dialog_result[0] = result
                # Refresh cases if dialog was accepted
                if result == 1:  # QDialog.Accepted
                    print("DEBUG: Dialog accepted, refreshing cases")
                    try:
                        self.refresh_cases()
                        print("DEBUG: Cases refreshed successfully")
                    except Exception as refresh_error:
                        print(f"DEBUG: Error refreshing cases: {refresh_error}")

            # Connect to finished signal
            dialog.finished.connect(on_dialog_finished)

            # Process events to allow dialog to be displayed
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.processEvents()

            print("DEBUG: Non-modal dialog displayed successfully")
            print("DEBUG: Dialog will remain open until user closes it")

            # Return success since dialog is displayed
            result = True

            # Clean up signal handlers
            try:
                signal.signal(signal.SIGTERM, old_sigterm)
                signal.signal(signal.SIGINT, old_sigint)
                print("DEBUG: Signal handlers restored")
            except:
                print("DEBUG: Could not restore signal handlers")

            # Clean up
            try:
                dialog.finished.disconnect(on_dialog_finished)
                print("DEBUG: Disconnected dialog signals")
            except:
                print("DEBUG: Could not disconnect dialog signals")

        except Exception as e:
            print(f"DEBUG: Error in manage_cases: {e}")
            import traceback
            traceback.print_exc()
            try:
                QMessageBox.critical(self, "Error", f"Failed to open Edit Cases dialog: {str(e)}")
            except Exception as msg_error:
                print(f"DEBUG: Could not show error dialog: {msg_error}")

    def todo_list(self):
        try:
            dialog = ToDoListDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open To-Do List dialog: {str(e)}")

    def manage_categories(self):
        try:
            dialog = ManageCategoriesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Manage Categories dialog: {str(e)}")

    def manage_lists(self):
        try:
            dialog = ManageListsDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Manage Lists dialog: {str(e)}")

    def manage_responsibilities(self):
        try:
            dialog = ResponsibilityManagementDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Manage Responsibilities dialog: {str(e)}")

    def manage_email_templates(self):
        try:
            dialog = ManageEmailTemplatesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Manage Email Templates dialog: {str(e)}")

    def generate_reports(self):
        try:
            dialog = ReportManagementDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Generate Reports dialog: {str(e)}")

    def manage_financial_years(self):
        try:
            dialog = FinancialYearManagementDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Financial Year Management dialog: {str(e)}")

    def view_checklist(self):
        """Placeholder for Checklist view - to be implemented"""
        QMessageBox.information(self, "Checklist", "Checklist view functionality will be implemented here.")

    def view_lead_schedule(self):
        """Placeholder for Lead Schedule view - to be implemented"""
        QMessageBox.information(self, "Lead Schedule", "Lead Schedule view functionality will be implemented here.")

    def view_deleted_items(self):
        """Placeholder for Deleted Items view - to be implemented"""
        QMessageBox.information(self, "Deleted Items", "Deleted Items view functionality will be implemented here.")

    def view_deleted_cases(self):
        """View cases in the Deleted Cases list"""
        try:
            dialog = ViewDeletedCasesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Deleted Cases view: {str(e)}")

    def create_write_off_submission(self):
        """Create a new write-off submission"""
        try:
            dialog = WriteOffSubmissionDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Write-Off Submission dialog: {str(e)}")

    def manage_write_off_submissions(self):
        """Manage existing write-off submissions"""
        try:
            dialog = WriteOffManagementDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Write-Off Management dialog: {str(e)}")

    def show_fallback_edit_dialog(self):
        """Show a simplified fallback dialog when the main Edit Cases dialog fails"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem

            dialog = QDialog(self)
            dialog.setWindowTitle("Edit Cases (Fallback Mode)")
            dialog.setFixedSize(600, 400)
            dialog.setAttribute(Qt.WA_DeleteOnClose, False)

            layout = QVBoxLayout(dialog)

            # Warning message
            warning_label = QLabel("⚠️ Advanced Edit Cases dialog failed to load.\nUsing simplified fallback mode.")
            warning_label.setStyleSheet("color: orange; font-weight: bold;")
            layout.addWidget(warning_label)

            # Simple case list
            list_label = QLabel("Available Cases:")
            layout.addWidget(list_label)

            case_list = QListWidget()
            # Load basic case list
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT transaction_no, category, amount FROM cases WHERE list != 'Deleted Cases' LIMIT 50")
                for row in cursor.fetchall():
                    case_no, category, amount = row
                    item_text = f"{case_no} - {category} - R{amount or 0}"
                    case_list.addItem(QListWidgetItem(item_text))
                conn.close()
            except Exception as db_error:
                case_list.addItem(QListWidgetItem(f"Error loading cases: {db_error}"))

            layout.addWidget(case_list)

            # Buttons
            button_layout = QHBoxLayout()
            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(lambda: self.refresh_fallback_list(case_list))
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)

            button_layout.addWidget(refresh_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)

            dialog.exec_()

        except Exception as fallback_error:
            QMessageBox.critical(self, "Fallback Error",
                               f"Even the fallback dialog failed: {str(fallback_error)}\n\n"
                               "Please restart the application and try again.")

    def refresh_fallback_list(self, case_list):
        """Refresh the case list in the fallback dialog"""
        try:
            case_list.clear()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT transaction_no, category, amount FROM cases WHERE list != 'Deleted Cases' LIMIT 50")
            for row in cursor.fetchall():
                case_no, category, amount = row
                item_text = f"{case_no} - {category} - R{amount or 0}"
                case_list.addItem(QListWidgetItem(item_text))
            conn.close()
        except Exception as refresh_error:
            case_list.addItem(QListWidgetItem(f"Error refreshing cases: {refresh_error}"))

def exception_handler(exctype, value, traceback):
    """Global exception handler to catch unhandled exceptions"""
    import traceback as tb
    error_msg = ''.join(tb.format_exception(exctype, value, traceback))
    print(f"CRITICAL: Unhandled exception: {error_msg}")

    # Try to save emergency recovery information
    try:
        with open('emergency_recovery.log', 'w') as f:
            f.write(f"Emergency Recovery Log\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Exception: {exctype.__name__}: {value}\n")
            f.write(f"Traceback:\n{error_msg}\n")
        print("CRITICAL: Emergency recovery information saved to emergency_recovery.log")
    except:
        print("CRITICAL: Could not save emergency recovery information")

    # Show error dialog if QApplication exists
    try:
        from PyQt5.QtWidgets import QMessageBox, QApplication
        app = QApplication.instance()
        if app:
            reply = QMessageBox.critical(None, "Critical Application Error",
                                       f"A critical error occurred:\n\n{str(value)}\n\n"
                                       "Emergency recovery information has been saved.\n\n"
                                       "Would you like to restart the application?",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)

            if reply == QMessageBox.Yes:
                print("CRITICAL: User requested application restart")
                # Try to restart the application
                try:
                    import subprocess
                    import sys
                    subprocess.Popen([sys.executable] + sys.argv)
                    print("CRITICAL: Application restart initiated")
                except Exception as restart_error:
                    print(f"CRITICAL: Could not restart application: {restart_error}")
        else:
            QMessageBox.critical(None, "Unexpected Error",
                               f"An unexpected error occurred:\n\n{str(value)}\n\nThe application will now close.")
    except Exception as dialog_error:
        print(f"CRITICAL: Could not show error dialog: {dialog_error}")

    # Exit gracefully
    print("CRITICAL: Application shutting down due to critical error")
    sys.exit(1)

if __name__ == "__main__":
    # Install global exception handler
    sys.excepthook = exception_handler

    # Run Qt diagnostics and apply fixes
    print("DEBUG: Running Qt diagnostics...")
    apply_qt_fixes()
    issues = check_qt_compatibility()
    if issues:
        print("DEBUG: Qt compatibility issues detected:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("DEBUG: No Qt compatibility issues detected")

    try:
        print("DEBUG: Creating QApplication with optimized settings")
        app = QApplication(sys.argv)
        print("DEBUG: QApplication created successfully")

        # Note: Qt message handler not available in this PyQt5 version
        # Qt internal errors will be caught by the global exception handler

        print("DEBUG: Creating main window")
        window = FWManagementApp()
        print("DEBUG: Main window created successfully")

        print("DEBUG: Showing main window")
        window.show()
        print("DEBUG: Main window shown successfully")

        # Force process events before starting main loop
        app.processEvents()
        print("DEBUG: Initial events processed")

        # Run the application with error handling
        print("DEBUG: About to start Qt event loop with app.exec_()")
        try:
            exit_code = app.exec_()
            print(f"DEBUG: Qt event loop completed with exit code: {exit_code}")
        except Exception as event_error:
            print(f"DEBUG: Error in Qt event loop: {event_error}")
            import traceback
            traceback.print_exc()
            exit_code = 1

        print(f"Application exited with code: {exit_code}")
        sys.exit(exit_code)

    except Exception as e:
        print(f"Critical error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)