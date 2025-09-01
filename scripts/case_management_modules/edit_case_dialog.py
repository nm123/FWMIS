import os
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QDateEdit,
    QFileDialog,
    QMessageBox,
    QWidget,
    QLabel,
    QScrollArea,
    QGroupBox,
)
from PyQt5.QtCore import QDate, Qt
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import (
    get_financial_year,
    create_year_folder,
)
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.responsibility_utils import (
    load_posting_responsibilities,
    load_responsibilities,
)
from scripts.Utilities.category_utils import load_categories
from scripts.Utilities.list_utils import load_lists
from scripts.Utilities.tree_utils import get_subtree_resp_ids
from scripts.Utilities.workflow_utils import handle_case_status_change
from collections import defaultdict
from .responsibility_selection import ResponsibilitySelectionDialog
from .determination_dialog import DeterminationDialog


class EditCaseDialog(QDialog):
    def __init__(self, case_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Case Details")
        self.setFixedSize(1200, 900)
        try:
            self.responsibilities = load_posting_responsibilities()
            self.categories = load_categories()
            self.lists = load_lists()
            self.fy = get_financial_year()
            self.transaction_no = case_data[1]  # Pre-populate with existing case data
            self.selected_responsibility_id = case_data[10]  # responsibility_id
            self.case_data = case_data
            self.supporting_evidence_compulsory = False

            # Validate that required data was loaded
            if not self.responsibilities:
                raise ValueError("No posting responsibilities found in database")
            if not self.categories:
                raise ValueError("No categories found in database")
            if not self.lists:
                raise ValueError("No lists found in database")

            self.setup_ui()
            self.load_case_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize Edit Case dialog: {str(e)}")
            self.reject()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)

        # Case Number (read-only)
        self.trans_no_edit = QLineEdit(self.transaction_no)
        self.trans_no_edit.setReadOnly(True)
        form_layout.addRow("Case No:", self.trans_no_edit)

        # Responsibility
        resp_layout = QHBoxLayout()
        self.responsibility_edit = QLineEdit()
        self.responsibility_edit.setReadOnly(True)
        self.responsibility_edit.setPlaceholderText("Click Select to choose responsibility...")
        resp_layout.addWidget(self.responsibility_edit)

        self.select_responsibility_button = QPushButton("Select")
        self.select_responsibility_button.clicked.connect(self.select_responsibility)
        resp_layout.addWidget(self.select_responsibility_button)

        form_layout.addRow("Responsibility:", resp_layout)

        # Date fields (improved grid layout for better alignment)
        date_group = QWidget()
        date_layout = QGridLayout(date_group)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(10)

        # Date Incurred
        date_incurred_label = QLabel("Date Incurred:")
        date_incurred_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        date_layout.addWidget(date_incurred_label, 0, 0)
        self.date_incurred_edit = QDateEdit(QDate.currentDate())
        self.date_incurred_edit.setCalendarPopup(True)
        self.date_incurred_edit.setFixedWidth(120)
        date_layout.addWidget(self.date_incurred_edit, 0, 1)

        # Date Identified
        date_identified_label = QLabel("Date Identified:")
        date_identified_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        date_layout.addWidget(date_identified_label, 0, 2)
        self.date_identified_edit = QDateEdit(QDate.currentDate())
        self.date_identified_edit.setCalendarPopup(True)
        self.date_identified_edit.setFixedWidth(120)
        date_layout.addWidget(self.date_identified_edit, 0, 3)

        # Date Reported
        date_reported_label = QLabel("Date Reported:")
        date_reported_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        date_layout.addWidget(date_reported_label, 0, 4)
        self.date_reported_edit = QDateEdit(QDate.currentDate())
        self.date_reported_edit.setCalendarPopup(True)
        self.date_reported_edit.setFixedWidth(120)
        date_layout.addWidget(self.date_reported_edit, 0, 5)

        form_layout.addRow("Dates:", date_group)

        # Description (larger for paragraphs)
        self.description_edit = QTextEdit()
        self.description_edit.setMinimumHeight(80)
        form_layout.addRow("Description:", self.description_edit)

        # Category
        self.category_combo = QComboBox()
        self.category_combo.addItems([c["name"] for c in self.categories])
        form_layout.addRow("Category:", self.category_combo)

        # List (show all system lists including new ones)
        self.list_combo = QComboBox()
        system_lists = [l["name"] for l in self.lists if l.get("is_system", False)]
        # Add new system-generated lists if not already in database
        new_lists = ["Recovered", "Write-Off Recommended", "Written Off"]
        for new_list in new_lists:
            if new_list not in system_lists:
                system_lists.append(new_list)
        self.list_combo.addItems(system_lists)
        # Select default list
        if system_lists:
            default_list = next((l for l in self.lists if l.get("is_default", False)), None)
            if default_list and default_list["name"] in system_lists:
                self.list_combo.setCurrentText(default_list["name"])
        form_layout.addRow("List:", self.list_combo)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.setCurrentText("Alleged")
        form_layout.addRow("Status:", self.status_combo)

        # Criminal Charges Laid
        self.criminal_charges_combo = QComboBox()
        self.criminal_charges_combo.addItems(["N/A", "Yes", "No"])
        self.criminal_charges_combo.setCurrentText("N/A")
        form_layout.addRow("Criminal Charges Laid:", self.criminal_charges_combo)

        # Disciplinary process
        self.disciplinary_combo = QComboBox()
        self.disciplinary_combo.addItems(["N/A", "Yes", "No"])
        self.disciplinary_combo.setCurrentText("N/A")
        form_layout.addRow("Disciplinary process in progress or completed:", self.disciplinary_combo)

        # Loss recovery
        self.loss_recovery_combo = QComboBox()
        self.loss_recovery_combo.addItems(["N/A", "Yes", "No"])
        self.loss_recovery_combo.setCurrentText("N/A")
        form_layout.addRow("Loss recovery commenced or completed:", self.loss_recovery_combo)

        # Steps to prevent future occurrence
        self.prevention_steps_edit = QTextEdit()
        self.prevention_steps_edit.setMinimumHeight(40)
        form_layout.addRow("Steps taken to prevent future occurrence of F&W expenditure:", self.prevention_steps_edit)

        # Amount
        self.amount_edit = QLineEdit()
        form_layout.addRow("Amount:", self.amount_edit)

        # BAS Payment fields
        self.bas_label = QLabel("BAS Payment No:")
        self.bas_payment_no_edit = QLineEdit()
        form_layout.addRow(self.bas_label, self.bas_payment_no_edit)

        self.bas_date_label = QLabel("BAS Payment Date:")
        self.bas_payment_date_edit = QDateEdit(QDate.currentDate())
        self.bas_payment_date_edit.setCalendarPopup(True)
        form_layout.addRow(self.bas_date_label, self.bas_payment_date_edit)

        # Persal No field
        self.persal_label = QLabel("Persal No:")
        self.persal_no_edit = QLineEdit()
        form_layout.addRow(self.persal_label, self.persal_no_edit)

        # File selection fields (conditional)
        self.source_doc_label = QLabel("Source Document:")
        self.source_doc_edit = QLineEdit()
        self.source_doc_button = QPushButton("Browse")
        self.source_doc_button.clicked.connect(self.browse_source_doc)
        source_doc_layout = QHBoxLayout()
        source_doc_layout.addWidget(self.source_doc_edit)
        source_doc_layout.addWidget(self.source_doc_button)
        form_layout.addRow(self.source_doc_label, source_doc_layout)

        self.minutes_label = QLabel("Loss Control Minutes:")
        self.minutes_edit = QLineEdit()
        self.minutes_button = QPushButton("Browse")
        self.minutes_button.clicked.connect(self.browse_minutes)
        minutes_layout = QHBoxLayout()
        minutes_layout.addWidget(self.minutes_edit)
        minutes_layout.addWidget(self.minutes_button)
        form_layout.addRow(self.minutes_label, minutes_layout)

        self.evidence_label = QLabel("Assessment Evidence:")
        self.evidence_edit = QLineEdit()
        self.evidence_button = QPushButton("Browse")
        self.evidence_button.clicked.connect(self.browse_evidence)
        evidence_layout = QHBoxLayout()
        evidence_layout.addWidget(self.evidence_edit)
        evidence_layout.addWidget(self.evidence_button)
        form_layout.addRow(self.evidence_label, evidence_layout)

        # Assessment fields (conditional)
        self.assessed_by_label = QLabel("Assessed By:")
        self.assessed_by_edit = QLineEdit()
        form_layout.addRow(self.assessed_by_label, self.assessed_by_edit)

        self.assessment_date_label = QLabel("Assessment Date:")
        self.assessment_date_edit = QDateEdit(QDate.currentDate())
        self.assessment_date_edit.setCalendarPopup(True)
        form_layout.addRow(self.assessment_date_label, self.assessment_date_edit)

        # Set up scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Connect signals and update conditional fields after dialog is fully initialized
        self.update_conditional_fields()

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_case)

        self.determination_button = QPushButton("Loss Control Determination")
        self.determination_button.clicked.connect(self.open_determination_dialog)
        self.determination_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")

        self.delete_button = QPushButton("Delete Case")
        self.delete_button.clicked.connect(self.delete_case)
        self.delete_button.setStyleSheet("QPushButton { color: red; font-weight: bold; }")

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.determination_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Connect signals after all methods are defined
        self.category_combo.currentIndexChanged.connect(self.update_conditional_fields)
        self.list_combo.currentTextChanged.connect(self.update_conditional_fields)
        self.status_combo.currentTextChanged.connect(self.on_status_changed)

        # Update determination button visibility
        self.update_determination_button_visibility()

    def load_case_data(self):
        """Load existing case data into the form fields"""
        # Set responsibility
        resp = next((r for r in self.responsibilities if r["id"] == self.case_data[10]), None)
        if resp:
            self.responsibility_edit.setText(resp["name"])

        # Set dates
        if self.case_data[2]:  # date_incurred
            self.date_incurred_edit.setDate(QDate.fromString(self.case_data[2], "yyyy-MM-dd"))
        if self.case_data[3]:  # date_identified
            self.date_identified_edit.setDate(QDate.fromString(self.case_data[3], "yyyy-MM-dd"))
        if self.case_data[4]:  # date_reported
            self.date_reported_edit.setDate(QDate.fromString(self.case_data[4], "yyyy-MM-dd"))

        # Set description
        if self.case_data[5]:  # description
            self.description_edit.setPlainText(self.case_data[5])

        # Set category
        if self.case_data[9]:  # category
            self.category_combo.setCurrentText(self.case_data[9])

        # Set list
        if self.case_data[16]:  # list
            self.list_combo.setCurrentText(self.case_data[16])

        # Set status
        if self.case_data[17]:  # status
            self.status_combo.setCurrentText(self.case_data[17])

        # Set criminal charges
        if len(self.case_data) > 22 and self.case_data[22]:
            self.criminal_charges_combo.setCurrentText(self.case_data[22])

        # Set disciplinary
        if len(self.case_data) > 23 and self.case_data[23]:
            self.disciplinary_combo.setCurrentText(self.case_data[23])

        # Set loss recovery
        if len(self.case_data) > 24 and self.case_data[24]:
            self.loss_recovery_combo.setCurrentText(self.case_data[24])

        # Set prevention steps
        if len(self.case_data) > 25 and self.case_data[25]:
            self.prevention_steps_edit.setPlainText(self.case_data[25])

        # Set amount
        if self.case_data[11]:  # amount
            self.amount_edit.setText(str(self.case_data[11]))

        # Set BAS fields
        if self.case_data[6]:  # bas_payment_no
            self.bas_payment_no_edit.setText(self.case_data[6])
        if self.case_data[7]:  # bas_payment_date
            self.bas_payment_date_edit.setDate(QDate.fromString(self.case_data[7], "yyyy-MM-dd"))

        # Set Persal No
        if self.case_data[8]:  # persal_no
            self.persal_no_edit.setText(self.case_data[8])

        # Set file paths
        if self.case_data[12]:  # source_document
            self.source_doc_edit.setText(self.case_data[12])
        if self.case_data[13]:  # minutes
            self.minutes_edit.setText(self.case_data[13])
        if self.case_data[14]:  # evidence_path
            self.evidence_edit.setText(self.case_data[14])

        # Set assessment fields
        if len(self.case_data) > 18 and self.case_data[18]:  # assessment_assessed_by
            self.assessed_by_edit.setText(self.case_data[18])
        if len(self.case_data) > 19 and self.case_data[19]:  # assessment_date
            self.assessment_date_edit.setDate(QDate.fromString(self.case_data[19], "yyyy-MM-dd"))

        # Update conditional fields to set proper status options based on list
        self.update_conditional_fields()

    def select_responsibility(self):
        dialog = ResponsibilitySelectionDialog(self)
        if dialog.exec_():
            selected = dialog.get_selected_responsibility()
            if selected:
                self.responsibility_edit.setText(selected["name"])
                self.selected_responsibility_id = selected["id"]

    def on_status_changed(self, status):
        """Handle status selection change with special logic for Valid status"""
        if status == "Valid":
            # Show warning dialog for Valid status
            reply = QMessageBox.question(
                self,
                "Confirm Valid Status",
                "Selecting 'Valid' means this case is NOT Fruitless and Wasteful Expenditure.\n\n"
                "Uploading Supporting Evidence is compulsory before the case can be saved.\n\n"
                "This will finalise the case.\n\n"
                "Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.supporting_evidence_compulsory = True
            else:
                # Revert to previous status or default
                self.status_combo.setCurrentText("Alleged")
                self.supporting_evidence_compulsory = False
        else:
            # Reset the compulsory flag for other statuses
            self.supporting_evidence_compulsory = False

    def update_conditional_fields(self):
        """Update visibility of conditional fields based on list and status selection"""
        try:
            # Get current selections safely
            selected_list = self.list_combo.currentText() if self.list_combo.count() > 0 else ""
            selected_status = self.status_combo.currentText() if self.status_combo.count() > 0 else ""
            selected_category = self.category_combo.currentText() if self.category_combo.count() > 0 else ""

            # Update status options based on list selection
            if hasattr(self, 'status_combo'):
                current_status = self.status_combo.currentText()
                self.status_combo.clear()

                if selected_list == "Lead Schedule":
                    self.status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed", "Recovered", "Write Off Recommended"])
                elif selected_list == "Recovered":
                    self.status_combo.addItems(["Recovered"])
                elif selected_list == "Write-Off Recommended":
                    self.status_combo.addItems(["Write Off Recommended"])
                elif selected_list == "Written Off":
                    self.status_combo.addItems(["Written Off"])
                else:
                    self.status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed"])

                # Restore previous selection if still valid
                if current_status and current_status in [self.status_combo.itemText(i) for i in range(self.status_combo.count())]:
                    self.status_combo.setCurrentText(current_status)
                else:
                    self.status_combo.setCurrentText("Alleged")

            # Update category-based compulsory fields
            bas_comp = False
            persal_comp = False

            if selected_category and hasattr(self, 'categories') and self.categories:
                category = next((c for c in self.categories if c["name"] == selected_category), None)
                if category:
                    bas_comp = category.get("bas_payment_compulsory", False)
                    persal_comp = category.get("persal_compulsory", False)

            # Update BAS fields visibility and labels
            if hasattr(self, 'bas_label'):
                self.bas_label.setText("BAS Payment No:" + (" *" if bas_comp else ""))
                self.bas_label.setVisible(bas_comp)
            if hasattr(self, 'bas_payment_no_edit'):
                self.bas_payment_no_edit.setVisible(bas_comp)
            if hasattr(self, 'bas_date_label'):
                self.bas_date_label.setVisible(bas_comp)
            if hasattr(self, 'bas_payment_date_edit'):
                self.bas_payment_date_edit.setVisible(bas_comp)

            # Update Persal field visibility and labels
            if hasattr(self, 'persal_label'):
                self.persal_label.setText("Persal No:" + (" *" if persal_comp else ""))
                self.persal_label.setVisible(persal_comp)
            if hasattr(self, 'persal_no_edit'):
                self.persal_no_edit.setVisible(persal_comp)

            # Update assessment fields visibility (Lead Schedule + Valid/Confirmed)
            show_assessment = (selected_list == "Lead Schedule" and
                              selected_status in ["Valid", "Confirmed"])

            # Assessment fields
            if hasattr(self, 'source_doc_label'):
                self.source_doc_label.setVisible(show_assessment)
            if hasattr(self, 'source_doc_edit'):
                self.source_doc_edit.setVisible(show_assessment)
            if hasattr(self, 'source_doc_button'):
                self.source_doc_button.setVisible(show_assessment)

            if hasattr(self, 'minutes_label'):
                self.minutes_label.setVisible(show_assessment)
            if hasattr(self, 'minutes_edit'):
                self.minutes_edit.setVisible(show_assessment)
            if hasattr(self, 'minutes_button'):
                self.minutes_button.setVisible(show_assessment)

            if hasattr(self, 'evidence_label'):
                self.evidence_label.setVisible(show_assessment)
            if hasattr(self, 'evidence_edit'):
                self.evidence_edit.setVisible(show_assessment)
            if hasattr(self, 'evidence_button'):
                self.evidence_button.setVisible(show_assessment)

            if hasattr(self, 'assessed_by_label'):
                self.assessed_by_label.setVisible(show_assessment)
            if hasattr(self, 'assessed_by_edit'):
                self.assessed_by_edit.setVisible(show_assessment)

            if hasattr(self, 'assessment_date_label'):
                self.assessment_date_label.setVisible(show_assessment)
            if hasattr(self, 'assessment_date_edit'):
                self.assessment_date_edit.setVisible(show_assessment)

            # Update determination button visibility
            self.update_determination_button_visibility()

        except Exception as e:
            print(f"Warning: Error in update_conditional_fields: {e}")

    def browse_source_doc(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Source Document", "", "PDF Files (*.pdf)")
        if file_path:
            self.source_doc_edit.setText(file_path)

    def browse_minutes(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Minutes", "", "PDF Files (*.pdf)")
        if file_path:
            self.minutes_edit.setText(file_path)

    def browse_evidence(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Evidence", "", "PDF Files (*.pdf)")
        if file_path:
            self.evidence_edit.setText(file_path)

    def save_case(self):
        try:
            bas_payment_no = self.bas_payment_no_edit.text().strip()
            persal_no = self.persal_no_edit.text().strip()
            amount_text = self.amount_edit.text().strip()

            # Get compulsory settings from selected category
            category_name = self.category_combo.currentText()
            category = next((c for c in self.categories if c["name"] == category_name), None)
            if category:
                bas_comp = category.get("bas_payment_compulsory", False)
                persal_comp = category.get("persal_compulsory", False)
            else:
                bas_comp = False
                persal_comp = False

            # Check compulsory fields based on category settings
            missing_fields = []
            if bas_comp and not bas_payment_no:
                missing_fields.append("BAS Payment No")
            if persal_comp and not persal_no:
                missing_fields.append("Persal No")
            if not amount_text:
                missing_fields.append("Amount")

            if missing_fields:
                QMessageBox.warning(self, "Invalid Input", f"The following fields are required: {', '.join(missing_fields)}")
                return

            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Amount must be a positive number.")
                return

            if not self.selected_responsibility_id:
                QMessageBox.warning(self, "Invalid Input", "Please select a responsibility.")
                return

            # Convert dates to strings
            date_incurred_str = self.date_incurred_edit.date().toString("yyyy-MM-dd")
            date_identified_str = self.date_identified_edit.date().toString("yyyy-MM-dd")
            date_reported_str = self.date_reported_edit.date().toString("yyyy-MM-dd")
            bas_payment_date_str = self.bas_payment_date_edit.date().toString("yyyy-MM-dd")
            assessment_date_str = self.assessment_date_edit.date().toString("yyyy-MM-dd")

            # Create case dictionary
            category_text = self.category_combo.currentText()
            status_text = self.status_combo.currentText()
            list_text = self.list_combo.currentText()
            criminal_charges_text = self.criminal_charges_combo.currentText()
            disciplinary_text = self.disciplinary_combo.currentText()
            loss_recovery_text = self.loss_recovery_combo.currentText()

            case = {
                "transaction_no": self.transaction_no,
                "date_incurred": str(date_incurred_str),
                "date_identified": str(date_identified_str),
                "date_reported": str(date_reported_str),
                "description": self.description_edit.toPlainText().strip(),
                "bas_payment_no": bas_payment_no,
                "bas_payment_date": str(bas_payment_date_str),
                "persal_no": persal_no,
                "category": category_text,
                "responsibility_id": self.selected_responsibility_id,
                "amount": amount,
                "source_document": self.source_doc_edit.text().strip(),
                "minutes": self.minutes_edit.text().strip(),
                "evidence_path": self.evidence_edit.text().strip(),
                "attachments": "[]",
                "status": status_text,
                "list": list_text,
                "assessment_assessed_by": self.assessed_by_edit.text().strip(),
                "assessment_date": str(assessment_date_str),
                "assessment_result": "",
                "criminal_charges": criminal_charges_text,
                "disciplinary_process": disciplinary_text,
                "loss_recovery": loss_recovery_text,
                "prevention_steps": self.prevention_steps_edit.toPlainText().strip(),
                "fy_id": None,
                "period_id": None,
                "original_list": list_text
            }

            # Handle file operations
            year_folder = create_year_folder(self.fy)
            for field in ["source_document", "minutes", "evidence_path"]:
                if case[field]:
                    dest_path = os.path.join(year_folder, f"{self.transaction_no}_{field}.pdf")
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    os.replace(case[field], dest_path)
                    case[field] = dest_path

            # Save to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE cases SET
                    date_incurred = ?, date_identified = ?, date_reported = ?, description = ?,
                    bas_payment_no = ?, bas_payment_date = ?, persal_no = ?, category = ?, responsibility_id = ?, amount = ?,
                    source_document = ?, minutes = ?, evidence_path = ?, attachments = ?, status = ?, list = ?, assessment_assessed_by = ?,
                    assessment_date = ?, assessment_result = ?, fy_id = ?, period_id = ?, criminal_charges = ?, disciplinary_process = ?,
                    loss_recovery = ?, prevention_steps = ?, original_list = ?
                WHERE transaction_no = ?
            """, (
                case["date_incurred"], case["date_identified"], case["date_reported"],
                case["description"], case["bas_payment_no"], case["bas_payment_date"], case["persal_no"],
                case["category"], case["responsibility_id"], case["amount"], case["source_document"],
                case["minutes"], case["evidence_path"], case["attachments"], case["status"], case["list"],
                case["assessment_assessed_by"], case["assessment_date"], case["assessment_result"],
                case["fy_id"], case["period_id"],
                case["criminal_charges"], case["disciplinary_process"], case["loss_recovery"],
                case["prevention_steps"], case["original_list"],
                case["transaction_no"]
            ))

            conn.commit()
            case_id = self.case_data[0]
            conn.close()

            # Handle workflow transitions based on status change
            old_status = self.case_data[17] if len(self.case_data) > 17 else None
            if old_status != status_text:
                handle_case_status_change(case_id, self.transaction_no, status_text, list_text)

            save_audit_log("edit_case", {
                "timestamp": datetime.now().isoformat(),
                "case_id": case_id,
                "transaction_no": self.transaction_no,
                "details": case
            }, self.fy)

            QMessageBox.information(self, "Success", "Case updated successfully.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save case: {str(e)}")
            self.reject()

    def delete_case(self):
        """Delete case by moving it to Deleted Cases"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete case {self.transaction_no}?\n\n"
            "This will move the case to the Deleted Cases list.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Get current list before updating
                cursor.execute("SELECT list FROM cases WHERE transaction_no = ?", (self.transaction_no,))
                current_list_result = cursor.fetchone()
                current_list = current_list_result[0] if current_list_result else "Unknown"

                # Update case to Deleted Cases
                cursor.execute("""
                    UPDATE cases
                    SET list = 'Deleted Cases', original_list = ?
                    WHERE transaction_no = ?
                """, (current_list, self.transaction_no))

                conn.commit()
                conn.close()

                # Log audit trail
                save_audit_log("delete_case", {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": self.case_data[0],
                    "transaction_no": self.transaction_no,
                    "original_list": current_list,
                    "details": "Case moved to Deleted Cases"
                }, self.fy)

                QMessageBox.information(self, "Success", f"Case {self.transaction_no} has been moved to Deleted Cases.")
                self.accept()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete case: {str(e)}")

    def open_determination_dialog(self):
        """Open the Loss Control Committee determination dialog"""
        try:
            dialog = DeterminationDialog(self.case_data, self)
            if dialog.exec_():
                # Refresh the current dialog data if determination was saved
                QMessageBox.information(self, "Determination Complete",
                                      "Determination has been recorded. Please save the case to apply any status changes.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open determination dialog: {str(e)}")

    def update_determination_button_visibility(self):
        """Update the visibility of the determination button based on case status"""
        try:
            selected_list = self.list_combo.currentText()
            selected_status = self.status_combo.currentText()

            # Show determination button for cases in Lead Schedule with Confirmed status
            # that haven't been through determination yet
            show_determination = (selected_list == "Lead Schedule" and
                                selected_status == "Confirmed")

            if hasattr(self, 'determination_button'):
                self.determination_button.setVisible(show_determination)

        except Exception as e:
            print(f"Warning: Error updating determination button visibility: {e}")
            if hasattr(self, 'determination_button'):
                self.determination_button.setVisible(False)