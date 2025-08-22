import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QAction,
    QWidget,
    QVBoxLayout,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from case_management import AddNewCaseDialog, ViewCasesDialog, ManageCasesDialog, ToDoListDialog
from category_management import ManageCategoriesDialog
from email_template_management import ManageEmailTemplatesDialog
from responsibility_management_ui import ResponsibilityManagementDialog
from report_management import ReportManagementDialog

class FWManagementApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fruitless and Wasteful Expenditure Management")
        self.showMaximized()  # Open in full-screen mode
        self.setup_ui()
        self.setup_menu()

    def setup_ui(self):
        # Set an empty central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        # Add a placeholder widget (empty)
        layout.addWidget(QWidget())

    def setup_menu(self):
        menubar = self.menuBar()
        # Add File menu with Exit option
        file_menu = menubar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        # Existing menus
        cases_menu = menubar.addMenu("Cases")
        add_case_action = QAction("Add New Case", self)
        add_case_action.triggered.connect(self.add_new_case)
        cases_menu.addAction(add_case_action)
        view_cases_action = QAction("View Cases", self)
        view_cases_action.triggered.connect(self.view_cases)
        cases_menu.addAction(view_cases_action)
        manage_cases_action = QAction("Manage Cases", self)
        manage_cases_action.triggered.connect(self.manage_cases)
        cases_menu.addAction(manage_cases_action)
        todo_action = QAction("To-Do List", self)
        todo_action.triggered.connect(self.todo_list)
        cases_menu.addAction(todo_action)
        manage_menu = menubar.addMenu("Manage")
        categories_action = QAction("Categories", self)
        categories_action.triggered.connect(self.manage_categories)
        manage_menu.addAction(categories_action)
        responsibilities_action = QAction("Responsibilities", self)
        responsibilities_action.triggered.connect(self.manage_responsibilities)
        manage_menu.addAction(responsibilities_action)
        email_templates_action = QAction("Email Templates", self)
        email_templates_action.triggered.connect(self.manage_email_templates)
        manage_menu.addAction(email_templates_action)
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

    def view_cases(self):
        try:
            dialog = ViewCasesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open View Cases dialog: {str(e)}")

    def manage_cases(self):
        try:
            dialog = ManageCasesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Manage Cases dialog: {str(e)}")

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FWManagementApp()
    window.show()
    sys.exit(app.exec_())