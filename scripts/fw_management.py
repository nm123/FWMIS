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
from list_management import ManageListsDialog
from email_template_management import ManageEmailTemplatesDialog
from responsibility_management_ui import ResponsibilityManagementDialog
from report_management import ReportManagementDialog
from financial_year_management import FinancialYearManagementDialog

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
        view_cases_action = QAction("View Cases", self)
        view_cases_action.triggered.connect(self.view_cases)
        cases_menu.addAction(view_cases_action)
        edit_cases_action = QAction("Edit Cases", self)
        edit_cases_action.triggered.connect(self.manage_cases)  # Reusing existing method
        cases_menu.addAction(edit_cases_action)

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
            from case_management import ViewDeletedCasesDialog
            dialog = ViewDeletedCasesDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Deleted Cases view: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FWManagementApp()
    window.show()
    sys.exit(app.exec_())