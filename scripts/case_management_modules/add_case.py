from PyQt5.QtWidgets import QDialog
from scripts.case_management_modules.add_case_logic import AddCaseLogic
from scripts.ui.components.add_case_ui import AssessmentDialog, setup_add_ui


class AddNewCaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Case")
        self.setFixedSize(1100, 900)

        # Set up logic first
        self.logic = AddCaseLogic(self)

        # Set up UI
        setup_add_ui(self)

    def select_responsibility(self):
        from scripts.case_management_modules.responsibility_selection import \
            ResponsibilitySelectionDialog

        dialog = ResponsibilitySelectionDialog(self)
        if dialog.exec_():
            selected = dialog.get_selected_responsibility()
            if selected:
                self.responsibility_edit.setText(selected["name"])
                self.selected_responsibility_id = selected["id"]

    def browse_file(self):
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def browse_supporting_evidence(self):
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Supporting Evidence", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.supporting_evidence_edit.setText(file_path)

    def browse_source_doc(self):
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Source Document", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.source_doc_edit.setText(file_path)

    def browse_evidence(self):
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Evidence", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.evidence_edit.setText(file_path)

    def browse_minutes(self):
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Minutes", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.minutes_edit.setText(file_path)

    def on_status_changed(self, status):
        self.logic.on_status_changed(status)

    def update_conditional_fields(self):
        self.logic.update_conditional_fields()

    def save_case(self):
        self.logic.save_case()

        # Connect methods
        self.select_responsibility_button.clicked.connect(self.select_responsibility)
        self.status_combo.currentTextChanged.connect(self.on_status_changed)
        self.category_combo.currentTextChanged.connect(self.update_conditional_fields)
        self.list_combo.currentTextChanged.connect(self.update_conditional_fields)
        self.save_button.clicked.connect(self.save_case)
        self.cancel_button.clicked.connect(self.reject)
