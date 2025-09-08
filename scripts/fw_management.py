import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QAction,
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QLabel,
)
from PyQt5.QtCore import Qt
from scripts.Utilities.ui_theme import apply_theme, create_status_label
from scripts.case_management import AddNewCaseDialog, ViewCasesDialog, EditCasesDialog, ToDoListDialog, ViewDeletedCasesDialog, import_undisclosed_cases
from scripts.case_management_modules.bulk_case_entry import BulkCaseEntryWizard
from scripts.case_management_modules.write_off_submission_dialog import WriteOffSubmissionDialog
from scripts.case_management_modules.write_off_management_dialog import WriteOffManagementDialog
from scripts.category_management import ManageCategoriesDialog
from scripts.list_management import ManageListsDialog
from scripts.email_template_management import ManageEmailTemplatesDialog
from scripts.responsibility_management_ui import ResponsibilityManagementDialog
from scripts.report_management import ReportManagementDialog
from scripts.financial_year_management import FinancialYearManagementDialog
from scripts.Utilities.config import initialize_shared_documents_table
from scripts.Utilities.financial_utils import get_active_period_display

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
        initialize_shared_documents_table()

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
            dialog = EditCasesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Edit Cases dialog: {str(e)}")

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FWManagementApp()
    window.show()
    sys.exit(app.exec_())