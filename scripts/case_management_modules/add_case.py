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
    generate_transaction_no,
    create_year_folder,
)
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.contact_utils import get_effective_contacts
from scripts.Utilities.validation_utils import is_valid_email
from scripts.Utilities.ui_theme import apply_theme, create_professional_button
import win32com.client
from scripts.case_management_modules.responsibility_selection import ResponsibilitySelectionDialog


class AddNewCaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Case")
        self.setFixedSize(1100, 900)

        # Apply professional theme
        apply_theme(self)

        # Initialize data with error handling
        try:
            from scripts.Utilities.responsibility_utils import load_posting_responsibilities
            from scripts.Utilities.category_utils import load_categories
            from scripts.Utilities.list_utils import load_lists
            self.responsibilities = load_posting_responsibilities()
            self.categories = load_categories()
            self.lists = load_lists()
            self.fy = get_financial_year()
        except Exception as e:
            print(f"Warning: Error loading data: {e}")
            self.responsibilities = []
            self.categories = []
            self.lists = []
            self.fy = "2024"

        self.transaction_no = None
        self.selected_responsibility_id = None
        self.supporting_evidence_compulsory = False

        # Create main layout
        layout = QVBoxLayout(self)

        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)

        # Case Number (read-only)
        self.trans_no_edit = QLineEdit("To be assigned")
        self.trans_no_edit.setReadOnly(True)
        form_layout.addRow("Case No:", self.trans_no_edit)

        # Responsibility
        resp_layout = QHBoxLayout()
        self.responsibility_edit = QLineEdit()
        self.responsibility_edit.setReadOnly(True)
        self.responsibility_edit.setPlaceholderText("Click Select to choose responsibility...")
        resp_layout.addWidget(self.responsibility_edit)

        self.select_responsibility_button = create_professional_button("Select", 'secondary')
        self.select_responsibility_button.clicked.connect(self.select_responsibility)
        resp_layout.addWidget(self.select_responsibility_button)

        form_layout.addRow("Responsibility:", resp_layout)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMinimumHeight(60)
        form_layout.addRow("Description:", self.description_edit)

        # Category
        self.category_combo = QComboBox()
        if self.categories:
            self.category_combo.addItems([c["name"] for c in self.categories])
        form_layout.addRow("Category:", self.category_combo)

        # Date Incurred
        self.date_incurred_edit = QDateEdit(QDate.currentDate())
        self.date_incurred_edit.setCalendarPopup(True)
        form_layout.addRow("Date Incurred:", self.date_incurred_edit)

        # Date Identified
        self.date_identified_edit = QDateEdit(QDate.currentDate())
        self.date_identified_edit.setCalendarPopup(True)
        form_layout.addRow("Date Identified:", self.date_identified_edit)

        # Date Reported
        self.date_reported_edit = QDateEdit(QDate.currentDate())
        self.date_reported_edit.setCalendarPopup(True)
        form_layout.addRow("Date Reported:", self.date_reported_edit)

        # List
        self.list_combo = QComboBox()
        system_lists = [l["name"] for l in self.lists if l.get("is_system", False) and l["name"] != "Deleted Cases"]
        self.list_combo.addItems(system_lists)
        # Always set to Checklist and disable selection
        if "Checklist" in system_lists:
            self.list_combo.setCurrentText("Checklist")
            self.list_combo.setEnabled(False)
        form_layout.addRow("List:", self.list_combo)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed"])
        self.status_combo.setCurrentText("Alleged")
        form_layout.addRow("Status:", self.status_combo)

        # Amount
        self.amount_edit = QLineEdit()
        form_layout.addRow("Amount:", self.amount_edit)


        # Assessment Evidence
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select file...")
        browse_button = create_professional_button("Browse...", 'secondary')
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(browse_button)
        form_layout.addRow("Assessment Evidence:", file_layout)

        # Supporting Evidence (To prove Existence)
        supporting_layout = QHBoxLayout()
        self.supporting_evidence_edit = QLineEdit()
        self.supporting_evidence_edit.setPlaceholderText("Select file (optional)...")
        supporting_browse_button = create_professional_button("Browse...", 'secondary')
        supporting_browse_button.clicked.connect(self.browse_supporting_evidence)
        supporting_layout.addWidget(self.supporting_evidence_edit)
        supporting_layout.addWidget(supporting_browse_button)
        form_layout.addRow("Supporting Evidence (To prove Existence):", supporting_layout)


        # Conditional fields - add them but hide initially
        self.bas_label = QLabel("BAS Payment No:")
        self.bas_payment_no_edit = QLineEdit()
        self.bas_label.setVisible(False)
        self.bas_payment_no_edit.setVisible(False)
        form_layout.addRow(self.bas_label, self.bas_payment_no_edit)

        self.bas_date_label = QLabel("BAS Payment Date:")
        self.bas_payment_date_edit = QDateEdit(QDate.currentDate())
        self.bas_payment_date_edit.setCalendarPopup(True)
        self.bas_date_label.setVisible(False)
        self.bas_payment_date_edit.setVisible(False)
        form_layout.addRow(self.bas_date_label, self.bas_payment_date_edit)

        self.bas_journal_label = QLabel("BAS Journal No:")
        self.bas_journal_no_edit = QLineEdit()
        self.bas_journal_label.setVisible(False)
        self.bas_journal_no_edit.setVisible(False)
        form_layout.addRow(self.bas_journal_label, self.bas_journal_no_edit)

        self.bas_journal_date_label = QLabel("BAS Journal Date:")
        self.bas_journal_date_edit = QDateEdit(QDate.currentDate())
        self.bas_journal_date_edit.setCalendarPopup(True)
        self.bas_journal_date_label.setVisible(False)
        self.bas_journal_date_edit.setVisible(False)
        form_layout.addRow(self.bas_journal_date_label, self.bas_journal_date_edit)

        self.persal_label = QLabel("Persal No:")
        self.persal_no_edit = QLineEdit()
        self.persal_label.setVisible(False)
        self.persal_no_edit.setVisible(False)
        form_layout.addRow(self.persal_label, self.persal_no_edit)



        # Prevention steps
        self.prevention_steps_edit = QTextEdit()
        self.prevention_steps_edit.setMinimumHeight(40)
        form_layout.addRow("Steps taken to prevent future occurrence of F&W expenditure:", self.prevention_steps_edit)

        # Assessment fields - add them but hide initially
        self.source_doc_label = QLabel("Source Document:")
        self.source_doc_edit = QLineEdit()
        self.source_doc_button = create_professional_button("Browse", 'secondary')
        self.source_doc_button.clicked.connect(self.browse_source_doc)
        source_doc_layout = QHBoxLayout()
        source_doc_layout.addWidget(self.source_doc_edit)
        source_doc_layout.addWidget(self.source_doc_button)
        self.source_doc_label.setVisible(False)
        self.source_doc_edit.setVisible(False)
        self.source_doc_button.setVisible(False)
        form_layout.addRow(self.source_doc_label, source_doc_layout)

        self.minutes_label = QLabel("Loss Control Minutes:")
        self.minutes_edit = QLineEdit()
        self.minutes_button = create_professional_button("Browse", 'secondary')
        self.minutes_button.clicked.connect(self.browse_minutes)
        minutes_layout = QHBoxLayout()
        minutes_layout.addWidget(self.minutes_edit)
        minutes_layout.addWidget(self.minutes_button)
        self.minutes_label.setVisible(False)
        self.minutes_edit.setVisible(False)
        self.minutes_button.setVisible(False)
        form_layout.addRow(self.minutes_label, minutes_layout)

        self.evidence_label = QLabel("Assessment Evidence:")
        self.evidence_edit = QLineEdit()
        self.evidence_button = create_professional_button("Browse", 'secondary')
        self.evidence_button.clicked.connect(self.browse_evidence)
        evidence_layout = QHBoxLayout()
        evidence_layout.addWidget(self.evidence_edit)
        evidence_layout.addWidget(self.evidence_button)
        self.evidence_label.setVisible(False)
        self.evidence_edit.setVisible(False)
        self.evidence_button.setVisible(False)
        form_layout.addRow(self.evidence_label, evidence_layout)

        self.assessed_by_label = QLabel("Assessed By:")
        self.assessed_by_edit = QLineEdit()
        self.assessed_by_label.setVisible(False)
        self.assessed_by_edit.setVisible(False)
        form_layout.addRow(self.assessed_by_label, self.assessed_by_edit)

        self.assessment_date_label = QLabel("Assessment Date:")
        self.assessment_date_edit = QDateEdit(QDate.currentDate())
        self.assessment_date_edit.setCalendarPopup(True)
        self.assessment_date_label.setVisible(False)
        self.assessment_date_edit.setVisible(False)
        form_layout.addRow(self.assessment_date_label, self.assessment_date_edit)

        # Set up scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Connect signals for real-time conditional field updates (will be called after method is defined)
        pass

        # Initialize conditional fields (safely)
        try:
            self.update_conditional_fields()
        except Exception as e:
            print(f"Warning: Could not initialize conditional fields: {e}")

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = create_professional_button("Save & Continue", 'primary')
        self.save_button.clicked.connect(self.save_case)

        self.cancel_button = create_professional_button("Cancel", 'secondary')
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Connect status change signal
        self.status_combo.currentTextChanged.connect(self.on_status_changed)

        # Connect category and list change signals for conditional field updates
        self.category_combo.currentTextChanged.connect(self.update_conditional_fields)
        self.list_combo.currentTextChanged.connect(self.update_conditional_fields)

    def browse_file(self):
        """Browse for a file to attach to the case."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Supporting Evidence", "", "All Files (*.*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def browse_source_doc(self):
        """Browse for source document file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Source Document", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.source_doc_edit.setText(file_path)

    def browse_minutes(self):
        """Browse for minutes file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Minutes", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.minutes_edit.setText(file_path)

    def browse_evidence(self):
        """Browse for evidence file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Evidence", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.evidence_edit.setText(file_path)

    def browse_supporting_evidence(self):
        """Browse for supporting evidence file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Supporting Evidence", "", "All Files (*.*)"
        )
        if file_path:
            self.supporting_evidence_edit.setText(file_path)

    def select_responsibility(self):
        dialog = ResponsibilitySelectionDialog(self)
        if dialog.exec_():
            selected = dialog.get_selected_responsibility()
            if selected:
                self.responsibility_edit.setText(selected["name"])
                self.selected_responsibility_id = selected["id"]

    def on_status_changed(self, status):
        """Handle status selection change with special logic for Valid and Confirmed statuses"""
        if status == "Valid":
            # Show warning dialog for Valid status
            reply = QMessageBox.question(
                self,
                "Confirm Valid Status",
                "Selecting 'Valid' means this case is NOT Fruitless and Wasteful Expenditure.\n\n"
                "Uploading Assessment Evidence is compulsory before the case can be saved.\n\n"
                "This will finalise the case.\n\n"
                "Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.supporting_evidence_compulsory = True
                # Update the label to show it's compulsory
                self.file_path_edit.setPlaceholderText("Assessment Evidence is REQUIRED - Select file...")
            else:
                # Revert to previous status or default
                self.status_combo.setCurrentText("Alleged")
                self.supporting_evidence_compulsory = False
                self.file_path_edit.setPlaceholderText("Select file...")
        elif status == "Confirmed":
            # Show warning dialog for Confirmed status
            reply = QMessageBox.question(
                self,
                "Confirm Confirmed Status",
                "Selecting 'Confirmed' means this case IS Fruitless and Wasteful Expenditure.\n\n"
                "Uploading Assessment Evidence is compulsory before the case can be saved.\n\n"
                "The case will be copied to the Lead Schedule.\n\n"
                "Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.supporting_evidence_compulsory = True
                # Update the label to show it's compulsory
                self.file_path_edit.setPlaceholderText("Assessment Evidence is REQUIRED - Select file...")
            else:
                # Revert to previous status or default
                self.status_combo.setCurrentText("Alleged")
                self.supporting_evidence_compulsory = False
                self.file_path_edit.setPlaceholderText("Select file...")
        else:
            # Reset the compulsory flag for other statuses
            self.supporting_evidence_compulsory = False
            self.file_path_edit.setPlaceholderText("Select file...")

    def update_conditional_fields(self):
        """Update visibility of conditional fields based on list and status selection"""
        # Ensure list combo has items before accessing currentText
        if self.list_combo.count() == 0:
            return

        selected_list = self.list_combo.currentText()

        # Store current status before clearing
        current_status = self.status_combo.currentText() if self.status_combo.count() > 0 else "Alleged"

        # Update status options based on list selection
        self.status_combo.clear()

        if selected_list == "Lead Schedule":
            # For Lead Schedule, include additional statuses
            self.status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed", "Recovered", "Write Off Recommended"])
        else:
            # For Checklist and other lists, show standard statuses
            self.status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed"])

        # Try to restore the previous selection if it's still valid
        if current_status in [self.status_combo.itemText(i) for i in range(self.status_combo.count())]:
            self.status_combo.setCurrentText(current_status)
        else:
            self.status_combo.setCurrentText("Alleged")

        # Get the selected status after updating options
        selected_status = self.status_combo.currentText()

        # Show assessment fields only for Lead Schedule + Valid/Confirmed status
        show_assessment_fields = (selected_list == "Lead Schedule" and
                                selected_status in ["Valid", "Confirmed"])

        # Update visibility of assessment-related fields
        self.source_doc_label.setVisible(show_assessment_fields)
        self.source_doc_edit.setVisible(show_assessment_fields)
        self.source_doc_button.setVisible(show_assessment_fields)

        self.minutes_label.setVisible(show_assessment_fields)
        self.minutes_edit.setVisible(show_assessment_fields)
        self.minutes_button.setVisible(show_assessment_fields)

        self.evidence_label.setVisible(show_assessment_fields)
        self.evidence_edit.setVisible(show_assessment_fields)
        self.evidence_button.setVisible(show_assessment_fields)

        self.assessed_by_label.setVisible(show_assessment_fields)
        self.assessed_by_edit.setVisible(show_assessment_fields)

        self.assessment_date_label.setVisible(show_assessment_fields)
        self.assessment_date_edit.setVisible(show_assessment_fields)

        # Update compulsory fields based on category
        selected_category = self.category_combo.currentText() if self.category_combo.count() > 0 else ""
        if selected_category:
            category = next((c for c in self.categories if c["name"] == selected_category), None)
            if category:
                bas_comp = category.get("bas_payment_compulsory", False)
                persal_comp = category.get("persal_compulsory", False)
            else:
                bas_comp = False
                persal_comp = False
        else:
            bas_comp = False
            persal_comp = False

        # Update BAS fields
        self.bas_label.setText("BAS Payment No:" + (" *" if bas_comp else ""))
        self.bas_label.setVisible(bas_comp)
        self.bas_payment_no_edit.setVisible(bas_comp)
        self.bas_date_label.setText("BAS Payment Date:" + (" *" if bas_comp else ""))
        self.bas_date_label.setVisible(bas_comp)
        self.bas_payment_date_edit.setVisible(bas_comp)

        # Update BAS Journal fields
        self.bas_journal_label.setText("BAS Journal No:" + (" *" if bas_comp else ""))
        self.bas_journal_label.setVisible(bas_comp)
        self.bas_journal_no_edit.setVisible(bas_comp)
        self.bas_journal_date_label.setText("BAS Journal Date:" + (" *" if bas_comp else ""))
        self.bas_journal_date_label.setVisible(bas_comp)
        self.bas_journal_date_edit.setVisible(bas_comp)

        # Update Persal field
        self.persal_label.setText("Persal No:" + (" *" if persal_comp else ""))
        self.persal_label.setVisible(persal_comp)
        self.persal_no_edit.setVisible(persal_comp)

    def save_case(self):
        try:
            # Get form values
            bas_payment_no = self.bas_payment_no_edit.text().strip()
            bas_journal_no = self.bas_journal_no_edit.text().strip()
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

            # Validate compulsory fields
            missing_fields = []
            if bas_comp:
                # Require either BAS Payment details or BAS Journal details
                has_payment_details = bas_payment_no.strip() != ""
                has_journal_details = bas_journal_no.strip() != ""
                if not (has_payment_details or has_journal_details):
                    missing_fields.append("BAS Payment No or BAS Journal No")
            if persal_comp and not persal_no:
                missing_fields.append("Persal No")
            if not amount_text:
                missing_fields.append("Amount")

            if missing_fields:
                QMessageBox.warning(self, "Invalid Input", f"The following fields are required: {', '.join(missing_fields)}")
                return

            # Validate amount
            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Amount must be a positive number.")
                return

            # Validate responsibility selection
            if not self.selected_responsibility_id:
                QMessageBox.warning(self, "Invalid Input", "Please select a responsibility.")
                return

            # Validate supporting evidence if compulsory
            if self.supporting_evidence_compulsory and not self.file_path_edit.text().strip():
                QMessageBox.warning(self, "Assessment Evidence Required",
                                  "Assessment Evidence is compulsory for Valid/Confirmed status cases.\n\n"
                                  "Please select a file before saving.")
                return

            # Generate transaction number
            self.transaction_no = generate_transaction_no(self.fy)
            self.trans_no_edit.setText(self.transaction_no)

            # Convert dates
            date_incurred_str = self.date_incurred_edit.date().toString("yyyy-MM-dd")
            date_identified_str = self.date_identified_edit.date().toString("yyyy-MM-dd")
            date_reported_str = self.date_reported_edit.date().toString("yyyy-MM-dd")
            bas_payment_date_str = self.bas_payment_date_edit.date().toString("yyyy-MM-dd")
            bas_journal_date_str = self.bas_journal_date_edit.date().toString("yyyy-MM-dd")
            assessment_date_str = self.assessment_date_edit.date().toString("yyyy-MM-dd")

            # Get combo box values
            category_text = self.category_combo.currentText()
            status_text = self.status_combo.currentText()
            list_text = self.list_combo.currentText()
            # If status is Confirmed, set list to Lead Schedule
            if status_text == "Confirmed":
                list_text = "Lead Schedule"

            # Determine status
            final_status = status_text
            if bas_comp and has_journal_details and not has_payment_details:
                final_status = "Outstanding BAS Details"

            # Create case dictionary
            case = {
                "transaction_no": self.transaction_no,
                "date_incurred": str(date_incurred_str),
                "date_identified": str(date_identified_str),
                "date_reported": str(date_reported_str),
                "description": self.description_edit.toPlainText().strip(),
                "bas_payment_no": bas_payment_no,
                "bas_payment_date": str(bas_payment_date_str),
                "bas_journal_no": bas_journal_no,
                "bas_journal_date": str(bas_journal_date_str),
                "persal_no": persal_no,
                "category": category_text,
                "responsibility_id": self.selected_responsibility_id,
                "amount": amount,
                "source_document": self.source_doc_edit.text().strip(),
                "minutes": self.minutes_edit.text().strip(),
                "evidence_path": self.evidence_edit.text().strip(),
                "supporting_evidence": self.supporting_evidence_edit.text().strip(),
                "attachments": "[]",
                "status": final_status,
                "list": list_text,
                "assessment_assessed_by": self.assessed_by_edit.text().strip(),
                "assessment_date": str(assessment_date_str),
                "assessment_result": "",
                "prevention_steps": self.prevention_steps_edit.toPlainText().strip(),
                "fy_id": None,
                "period_id": None,
                "original_list": list_text
            }

            # Handle file operations
            year_folder = create_year_folder(self.fy)
            for field in ["source_document", "minutes", "evidence_path", "supporting_evidence"]:
                if case[field]:
                    # Determine file extension
                    _, ext = os.path.splitext(case[field])
                    if not ext:
                        ext = ".pdf"  # Default to PDF if no extension
                    dest_path = os.path.join(year_folder, f"{self.transaction_no}_{field}{ext}")
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    os.replace(case[field], dest_path)
                    case[field] = dest_path

            # Save to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO cases (
                    transaction_no, date_incurred, date_identified, date_reported, description,
                    bas_payment_no, bas_payment_date, bas_journal_no, bas_journal_date, persal_no, category, responsibility_id, amount,
                    source_document, minutes, evidence_path, supporting_evidence, attachments, status, list, assessment_assessed_by,
                    assessment_date, assessment_result, fy_id, period_id, prevention_steps, original_list
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case["transaction_no"], case["date_incurred"], case["date_identified"], case["date_reported"],
                case["description"], case["bas_payment_no"], case["bas_payment_date"], case["bas_journal_no"], case["bas_journal_date"], case["persal_no"],
                case["category"], case["responsibility_id"], case["amount"], case["source_document"],
                case["minutes"], case["evidence_path"], case["supporting_evidence"], case["attachments"], case["status"], case["list"],
                case["assessment_assessed_by"], case["assessment_date"], case["assessment_result"],
                case["fy_id"], case["period_id"], case["prevention_steps"], case["original_list"]
            ))

            conn.commit()
            case_id = cursor.lastrowid
            conn.close()

            # Log audit trail
            save_audit_log("add_case", {
                "timestamp": datetime.now().isoformat(),
                "case_id": case_id,
                "transaction_no": self.transaction_no,
                "details": case
            }, self.fy)

            # Check if supporting evidence is missing
            if not case["supporting_evidence"]:
                # Update status to indicate missing supporting evidence
                conn.execute("UPDATE cases SET status = ? WHERE transaction_no = ?", ("Missing Supporting Evidence", self.transaction_no))
                conn.commit()
                QMessageBox.warning(self, "Supporting Evidence Missing",
                                  "Case saved successfully, but Supporting Evidence (To prove Existence) is missing.\n\n"
                                  "This case has been added to the To-Do List for follow-up.")
            else:
                QMessageBox.information(self, "Success", "Case added successfully.")

            self.reset_form_for_next_case()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save case: {str(e)}")
            self.reject()

    def save_case_and_close(self):
        """Save the case and close the dialog"""
        self.save_case()
        self.accept()

    def reset_form_for_next_case(self):
        """Reset the form for entering the next case"""
        # Generate new transaction number
        self.transaction_no = generate_transaction_no(self.fy)
        self.trans_no_edit.setText(self.transaction_no)

        # Clear text fields
        self.description_edit.clear()
        self.bas_payment_no_edit.clear()
        self.bas_journal_no_edit.clear()
        self.persal_no_edit.clear()
        self.amount_edit.clear()
        self.evidence_edit.clear()
        self.supporting_evidence_edit.clear()
        self.source_doc_edit.clear()
        self.minutes_edit.clear()
        self.assessed_by_edit.clear()

        # Reset combo boxes to defaults
        self.status_combo.setCurrentText("Alleged")
        self.prevention_steps_edit.clear()

        # Always reset list combo to Checklist
        if "Checklist" in [l["name"] for l in self.lists if l.get("is_system", False) and l["name"] != "Deleted Cases"]:
            self.list_combo.setCurrentText("Checklist")

        # Reset dates to current date
        current_date = QDate.currentDate()
        self.date_incurred_edit.setDate(current_date)
        self.date_identified_edit.setDate(current_date)
        self.date_reported_edit.setDate(current_date)
        self.bas_payment_date_edit.setDate(current_date)
        self.bas_journal_date_edit.setDate(current_date)
        self.assessment_date_edit.setDate(current_date)

        # Clear responsibility selection
        self.responsibility_edit.clear()
        self.selected_responsibility_id = None

        # Clear attachments (keeping empty array for database)
        pass

        # Reset focus to first field
        self.responsibility_edit.setFocus()

    def next_case(self):
        # Generate new transaction number for next case
        self.transaction_no = generate_transaction_no(self.fy)
        self.trans_no_edit.setText(self.transaction_no)
        self.description_edit.clear()
        self.bas_payment_no_edit.clear()
        self.bas_journal_no_edit.clear()
        self.persal_no_edit.clear()
        self.amount_edit.clear()
        self.evidence_edit.clear()
        self.prevention_steps_edit.clear()
        # Always reset list combo to Checklist
        if "Checklist" in [l["name"] for l in self.lists if l.get("is_system", False) and l["name"] != "Deleted Cases"]:
            self.list_combo.setCurrentText("Checklist")

        # Reset supporting evidence compulsory flag
        self.supporting_evidence_compulsory = False
        self.file_path_edit.setPlaceholderText("Select file...")

    def send_reminder_email(self):
        if not self.selected_responsibility_id:
            QMessageBox.warning(self, "No Responsibility", "Please select a responsibility first.")
            return
        resp_id = self.selected_responsibility_id
        contacts = get_effective_contacts(self.responsibilities, resp_id)
        emails = [c["email"] for c in contacts if is_valid_email(c["email"])]
        if not emails:
            QMessageBox.warning(self, "No Contacts", "No valid email contacts found for this responsibility.")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT body FROM email_templates WHERE name = ?", ("Reminder - Assessment Evidence",))
        template = cursor.fetchone()
        conn.close()

        if not template:
            QMessageBox.warning(self, "No Template", "No email template found.")
            return

        body = template[0]
        body = body.replace("[Recipient]", ", ".join(c["name"] for c in contacts))
        body = body.replace("[Case ID]", self.transaction_no)
        body = body.replace("[Due Date]", QDate.currentDate().addDays(7).toString("yyyy-MM-dd"))
        body = body.replace("[Contact Email]", ", ".join(emails))
        body = body.replace("[Your Name]", "Accounts Payable Team")

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = ";".join(emails)
        mail.Subject = f"Reminder: Assessment Evidence for Case {self.transaction_no}"
        mail.Body = body
        mail.Display()

    def open_assessment(self):
        if not self.evidence_edit.text():
            QMessageBox.warning(self, "No Evidence", "Please upload evidence before assessment.")
            return
        dialog = AssessmentDialog(self)
        if dialog.exec_():
            assessment_data = dialog.get_assessment_data()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM cases")
            max_id = cursor.fetchone()[0]
            case_id = (max_id or 0) + 1
            cursor.execute("UPDATE cases SET assessment_assessed_by = ?, assessment_date = ?, assessment_result = ?, status = ?, list = ? WHERE transaction_no = ?",
                            (assessment_data["assessed_by"], assessment_data["assessment_date"], assessment_data["result"], assessment_data["result"], "Lead Schedule", self.transaction_no))
            conn.commit()
            conn.close()
            save_audit_log("assess_case", {
                "timestamp": datetime.now().isoformat(),
                "case_id": case_id,
                "transaction_no": self.transaction_no,
                "details": assessment_data
            }, self.fy)


class AssessmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Case Assessment")
        self.setFixedSize(400, 300)

        # Apply professional theme
        apply_theme(self)

        layout = QFormLayout(self)

        self.assessed_by_edit = QLineEdit()
        layout.addRow("Assessed By:", self.assessed_by_edit)

        self.assessment_date_edit = QDateEdit(QDate.currentDate())
        self.assessment_date_edit.setCalendarPopup(True)
        layout.addRow("Assessment Date:", self.assessment_date_edit)

        self.result_combo = QComboBox()
        self.result_combo.addItems(["Valid", "Confirmed"])
        layout.addRow("Result:", self.result_combo)

        button_layout = QHBoxLayout()
        save_button = create_professional_button("Save", 'primary')
        save_button.clicked.connect(self.accept)
        cancel_button = create_professional_button("Cancel", 'secondary')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

    def get_assessment_data(self):
        return {
            "assessed_by": self.assessed_by_edit.text(),
            "assessment_date": self.assessment_date_edit.date().toString("yyyy-MM-dd"),
            "result": self.result_combo.currentText()
        }