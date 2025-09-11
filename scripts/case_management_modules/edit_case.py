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
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
)
from PyQt5.QtCore import QDate, Qt, QEvent
from PyQt5.QtGui import QWheelEvent
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year, create_year_folder
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.responsibility_utils import load_posting_responsibilities, load_responsibilities
from scripts.Utilities.category_utils import load_categories
from scripts.Utilities.list_utils import load_lists
from scripts.Utilities.tree_utils import get_subtree_resp_ids
from scripts.Utilities.utils import format_currency_amount
from scripts.Utilities.ui_theme import apply_theme, create_professional_button
from collections import defaultdict
from .responsibility_selection import ResponsibilitySelectionDialog


class NoWheelComboBox(QComboBox):
    """Custom QComboBox that ignores mouse wheel events unless focused"""

    def wheelEvent(self, event: QWheelEvent):
        """Override wheel event to only accept when widget has focus"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # Ignore wheel event when not focused
            event.ignore()


class EditCaseDialog(QDialog):
    def __init__(self, case_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Case Details")
        self.setFixedSize(1200, 900)

        # Apply professional theme
        apply_theme(self)

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
        print("DEBUG: Starting setup_ui")
        print(f"DEBUG: self type: {type(self)}")
        print(f"DEBUG: self is QDialog: {isinstance(self, QDialog)}")

        # Try to create a minimal layout first
        try:
            print("DEBUG: Creating minimal layout")
            layout = QVBoxLayout()
            print("DEBUG: QVBoxLayout created successfully")
            self.setLayout(layout)
            print("DEBUG: Layout set successfully")

            # Create a simple test widget
            test_label = QLabel("Test Label")
            layout.addWidget(test_label)
            print("DEBUG: Test widget added successfully")

            # Now try the full UI
            print("DEBUG: Starting full UI setup")
            self.setup_full_ui()
            print("DEBUG: Full UI setup completed")

        except Exception as e:
            print(f"DEBUG: Exception in setup_ui: {e}")
            import traceback
            traceback.print_exc()
            raise

    def setup_full_ui(self):
        print("DEBUG: In setup_full_ui")
        # Clear existing layout
        if self.layout():
            print("DEBUG: Clearing existing layout")
            # Remove all widgets from layout
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            # Clear the layout
            self.layout().deleteLater()

        print("DEBUG: Creating new layout")
        layout = QVBoxLayout(self)
        print("DEBUG: Main layout created")

        # Create form layout
        form_layout = QFormLayout()
        print("DEBUG: Form layout created")

        # Add basic widgets one by one with error checking
        try:
            print("DEBUG: Adding responsibility field")
            responsibility_layout = QHBoxLayout()
            self.responsibility_edit = QLineEdit()
            self.responsibility_edit.setReadOnly(True)
            self.responsibility_edit.setPlaceholderText("Click Select to choose responsibility...")
            responsibility_layout.addWidget(self.responsibility_edit)

            self.select_responsibility_button = create_professional_button("Select", 'secondary')
            self.select_responsibility_button.clicked.connect(self.select_responsibility)
            responsibility_layout.addWidget(self.select_responsibility_button)

            form_layout.addRow("Responsibility:", responsibility_layout)
            print("DEBUG: Responsibility field added")
        except Exception as e:
            print(f"DEBUG: Error adding responsibility field: {e}")
            raise

        print("DEBUG: Basic fields added successfully")
        layout.addLayout(form_layout)

        print("DEBUG: Full UI setup completed successfully")

        # Case No (first) - read-only
        self.trans_no_edit = QLineEdit(self.transaction_no)
        self.trans_no_edit.setReadOnly(True)
        form_layout.addRow("Case No:", self.trans_no_edit)


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
        self.description_edit.setMinimumHeight(80)  # Make it bigger for paragraphs
        form_layout.addRow("Description:", self.description_edit)

        # Category (moved down)
        self.category_combo = NoWheelComboBox()
        self.category_combo.addItems([c["name"] for c in self.categories])
        form_layout.addRow("Category:", self.category_combo)

        # List (only show Checklist and Lead Schedule)
        self.list_combo = NoWheelComboBox()
        system_lists = [l["name"] for l in self.lists if l.get("is_system", False) and l["name"] != "Deleted Cases"]
        self.list_combo.addItems(system_lists)
        # Select default list
        if system_lists:  # Only try to set current text if there are items
            default_list = next((l for l in self.lists if l.get("is_default", False)), None)
            if default_list and default_list["name"] in system_lists:
                self.list_combo.setCurrentText(default_list["name"])
        form_layout.addRow("List:", self.list_combo)

        # Status (moved here, right below List)
        self.status_combo = NoWheelComboBox()
        # Status options will be set dynamically based on list selection
        self.status_combo.setCurrentText("Alleged")  # Default to Alleged
        form_layout.addRow("Status:", self.status_combo)

        # Criminal Charges Laid
        self.criminal_charges_combo = NoWheelComboBox()
        self.criminal_charges_combo.addItems(["N/A", "Yes", "No"])
        self.criminal_charges_combo.setCurrentText("N/A")
        form_layout.addRow("Criminal Charges Laid:", self.criminal_charges_combo)

        # Disciplinary process
        self.disciplinary_combo = NoWheelComboBox()
        self.disciplinary_combo.addItems(["N/A", "Yes", "No"])
        self.disciplinary_combo.setCurrentText("N/A")
        form_layout.addRow("Disciplinary process in progress or completed:", self.disciplinary_combo)

        # Loss recovery
        self.loss_recovery_combo = NoWheelComboBox()
        self.loss_recovery_combo.addItems(["N/A", "Yes", "No"])
        self.loss_recovery_combo.setCurrentText("N/A")
        form_layout.addRow("Loss recovery commenced or completed:", self.loss_recovery_combo)

        # Steps to prevent future occurrence
        self.prevention_steps_edit = QTextEdit()
        self.prevention_steps_edit.setMinimumHeight(40)  # Make it smaller for paragraphs
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
        self.source_doc_button = create_professional_button("Browse", 'secondary')
        self.source_doc_button.clicked.connect(self.browse_source_doc)
        source_doc_layout = QHBoxLayout()
        source_doc_layout.addWidget(self.source_doc_edit)
        source_doc_layout.addWidget(self.source_doc_button)
        form_layout.addRow(self.source_doc_label, source_doc_layout)

        self.minutes_label = QLabel("Loss Control Minutes:")
        self.minutes_edit = QLineEdit()
        self.minutes_button = create_professional_button("Browse", 'secondary')
        self.minutes_button.clicked.connect(self.browse_minutes)
        minutes_layout = QHBoxLayout()
        minutes_layout.addWidget(self.minutes_edit)
        minutes_layout.addWidget(self.minutes_button)
        form_layout.addRow(self.minutes_label, minutes_layout)

        self.evidence_label = QLabel("Assessment Evidence:")
        self.evidence_edit = QLineEdit()
        self.evidence_button = create_professional_button("Browse", 'secondary')
        self.evidence_button.clicked.connect(self.browse_evidence)
        evidence_layout = QHBoxLayout()
        evidence_layout.addWidget(self.evidence_edit)
        evidence_layout.addWidget(self.evidence_button)
        form_layout.addRow(self.evidence_label, evidence_layout)


        # Other fields - Status moved above

        # Assessment fields (conditional)
        self.assessed_by_label = QLabel("Assessed By:")
        self.assessed_by_edit = QLineEdit()
        form_layout.addRow(self.assessed_by_label, self.assessed_by_edit)

        self.assessment_date_label = QLabel("Assessment Date:")
        self.assessment_date_edit = QDateEdit(QDate.currentDate())
        self.assessment_date_edit.setCalendarPopup(True)
        form_layout.addRow(self.assessment_date_label, self.assessment_date_edit)

        layout.addLayout(form_layout)

        # Connect signals and update conditional fields after dialog is fully initialized
        print("DEBUG: Connecting signals")
        try:
            # Ensure combo boxes have valid selections before connecting signals
            if self.list_combo.count() > 0 and self.list_combo.currentText() == "":
                self.list_combo.setCurrentIndex(0)
            if self.status_combo.count() > 0 and self.status_combo.currentText() == "":
                self.status_combo.setCurrentText("Alleged")

            print("DEBUG: Calling update_conditional_fields")
            self.update_conditional_fields()
            print("DEBUG: Signals connected successfully")
        except Exception as e:
            print(f"DEBUG: Error connecting signals: {e}")
            import traceback
            traceback.print_exc()

        button_layout = QHBoxLayout()
        self.save_button = create_professional_button("Save Changes", 'primary')
        self.save_button.clicked.connect(self.save_case)

        self.delete_button = create_professional_button("Delete Case", 'danger')
        self.delete_button.clicked.connect(self.delete_case)

        self.cancel_button = create_professional_button("Cancel", 'secondary')
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Connect signals after all methods are defined
        self.category_combo.currentIndexChanged.connect(self.update_conditional_fields)
        self.list_combo.currentTextChanged.connect(self.update_conditional_fields)
        self.status_combo.currentTextChanged.connect(self.on_status_changed)

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
                # Update the label to show it's compulsory
                self.evidence_edit.setPlaceholderText("Supporting Evidence is REQUIRED - Select file...")
            else:
                # Revert to previous status or default
                self.status_combo.setCurrentText("Alleged")
                self.supporting_evidence_compulsory = False
                self.evidence_edit.setPlaceholderText("Select file...")
        else:
            # Reset the compulsory flag for other statuses
            self.supporting_evidence_compulsory = False
            self.evidence_edit.setPlaceholderText("Select file...")


    def update_conditional_fields(self):
        """Update visibility of conditional fields based on list and status selection"""
        try:
            # Safety checks for required widgets
            if not hasattr(self, 'list_combo') or not hasattr(self, 'status_combo') or not hasattr(self, 'category_combo'):
                return  # Exit early if required widgets don't exist

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

            # Update BAS fields visibility and labels (with safety checks)
            if hasattr(self, 'bas_label'):
                self.bas_label.setText("BAS Payment No:" + (" *" if bas_comp else ""))
                self.bas_label.setVisible(bas_comp)
            if hasattr(self, 'bas_payment_no_edit'):
                self.bas_payment_no_edit.setVisible(bas_comp)
            if hasattr(self, 'bas_date_label'):
                self.bas_date_label.setVisible(bas_comp)
            if hasattr(self, 'bas_payment_date_edit'):
                self.bas_payment_date_edit.setVisible(bas_comp)

            # Update Persal field visibility and labels (with safety checks)
            if hasattr(self, 'persal_label'):
                self.persal_label.setText("Persal No:" + (" *" if persal_comp else ""))
                self.persal_label.setVisible(persal_comp)
            if hasattr(self, 'persal_no_edit'):
                self.persal_no_edit.setVisible(persal_comp)

            # Update assessment fields visibility (Lead Schedule + Valid/Confirmed)
            show_assessment = (selected_list == "Lead Schedule" and
                              selected_status in ["Valid", "Confirmed"])

            # Assessment fields (with safety checks)
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

        except Exception as e:
            print(f"Warning: Error in update_conditional_fields: {e}")
            # Don't crash, just continue with default visibility


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
            print("DEBUG: Starting save_case method for edit")
            bas_payment_no = self.bas_payment_no_edit.text().strip()
            persal_no = self.persal_no_edit.text().strip()
            amount_text = self.amount_edit.text().strip()
            print(f"DEBUG: bas_payment_no='{bas_payment_no}', persal_no='{persal_no}', amount_text='{amount_text}'")

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

            # Validate supporting evidence if compulsory
            if self.supporting_evidence_compulsory and not self.evidence_edit.text().strip():
                QMessageBox.warning(self, "Supporting Evidence Required",
                                  "Supporting Evidence is compulsory for Valid status cases.\n\n"
                                  "Please select a file before saving.")
                return

            # Convert dates to strings explicitly with error checking
            try:
                date_incurred_str = self.date_incurred_edit.date().toString("yyyy-MM-dd")
                date_identified_str = self.date_identified_edit.date().toString("yyyy-MM-dd")
                date_reported_str = self.date_reported_edit.date().toString("yyyy-MM-dd")
                bas_payment_date_str = self.bas_payment_date_edit.date().toString("yyyy-MM-dd")
                assessment_date_str = self.assessment_date_edit.date().toString("yyyy-MM-dd")
                print(f"DEBUG: Date conversions successful")
            except Exception as e:
                print(f"DEBUG: Date conversion error: {e}")
                raise

            # Create case dictionary with error checking
            try:
                category_text = self.category_combo.currentText()
                status_text = self.status_combo.currentText()
                list_text = self.list_combo.currentText()
                criminal_charges_text = self.criminal_charges_combo.currentText()
                disciplinary_text = self.disciplinary_combo.currentText()
                loss_recovery_text = self.loss_recovery_combo.currentText()

                print(f"DEBUG: Combo box values - category: '{category_text}', status: '{status_text}', list: '{list_text}'")
                print(f"DEBUG: Combo box values - criminal: '{criminal_charges_text}', disciplinary: '{disciplinary_text}', loss: '{loss_recovery_text}'")

                # Get existing fy_id and period_id from case data, or set defaults if missing
                existing_fy_id = self.case_data[21] if len(self.case_data) > 21 else None  # fy_id
                existing_period_id = self.case_data[22] if len(self.case_data) > 22 else None  # period_id

                # If fy_id is missing, get current open financial year
                if existing_fy_id is None:
                    from scripts.Utilities.financial_utils import get_current_open_financial_year
                    current_fy = get_current_open_financial_year()
                    if current_fy:
                        existing_fy_id = current_fy[0]
                        print(f"DEBUG: Fixed NULL fy_id for case {self.transaction_no}, set to {existing_fy_id}")
                    else:
                        QMessageBox.critical(self, "Financial Year Error",
                                            "Cannot save case: No open financial year found.\n\n"
                                            "Please ensure a financial year is open in Financial Year Management.")
                        return

                # If period_id is missing, try to determine it from the date incurred
                if existing_period_id is None and existing_fy_id:
                    try:
                        conn_temp = sqlite3.connect(DB_PATH)
                        cursor_temp = conn_temp.cursor()

                        # Find the period that contains the date incurred
                        cursor_temp.execute("""
                            SELECT p.id FROM periods p
                            INNER JOIN financial_years fy ON p.fy_id = fy.id
                            WHERE p.fy_id = ? AND p.start_date <= ? AND p.end_date >= ?
                            ORDER BY p.period_number DESC LIMIT 1
                        """, (existing_fy_id, date_incurred_str, date_incurred_str))
                        period_result = cursor_temp.fetchone()
                        existing_period_id = period_result[0] if period_result else None

                        conn_temp.close()
                    except Exception as e:
                        print(f"Warning: Could not determine period ID: {e}")
                        existing_period_id = None

                # Handle transaction_no suffix changes based on status
                base_transaction_no = self.transaction_no
                if base_transaction_no.endswith('-LS'):
                    base_transaction_no = base_transaction_no[:-3]  # Remove -LS
                elif base_transaction_no.endswith('-WOR'):
                    base_transaction_no = base_transaction_no[:-4]  # Remove -WOR

                transaction_no_with_suffix = base_transaction_no
                if status_text == "Confirmed":
                    transaction_no_with_suffix = f"{base_transaction_no}-LS"
                    list_text = "Lead Schedule"
                elif status_text == "Write-Off Recommended":
                    transaction_no_with_suffix = f"{base_transaction_no}-WOR"
                    list_text = "Write-Off Recommended"
                else:
                    # For other statuses, ensure no suffix
                    list_text = "Checklist"

                case = {
                    "transaction_no": transaction_no_with_suffix,
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
                    "assessment_result": "",  # Removed field
                    "criminal_charges": criminal_charges_text,
                    "disciplinary_process": disciplinary_text,
                    "loss_recovery": loss_recovery_text,
                    "prevention_steps": self.prevention_steps_edit.toPlainText().strip(),
                    "fy_id": existing_fy_id,
                    "period_id": existing_period_id,
                    "original_list": list_text
                }
                print(f"DEBUG: Case dictionary created successfully with {len(case)} fields")
                print(f"DEBUG: Case dict keys: {list(case.keys())}")
            except Exception as e:
                print(f"DEBUG: Error creating case dictionary: {e}")
                raise
            # Handle file operations with error checking
            try:
                year_folder = create_year_folder(self.fy)
                supporting_evidence_folder = os.path.join(year_folder, "Supporting Evidence")
                case_folder = os.path.join(supporting_evidence_folder, f"Case {self.transaction_no}")
                os.makedirs(case_folder, exist_ok=True)
                print(f"DEBUG: Case folder: {case_folder}")

                # Map fields to proper file names
                file_mappings = {
                    "source_document": f"{self.transaction_no} Source Document.pdf",
                    "minutes": f"{self.transaction_no} Loss Control Minutes.pdf",
                    "evidence_path": f"{self.transaction_no} Assessment Evidence.pdf"
                }

                for field, filename in file_mappings.items():
                    if case[field] and case[field].strip():
                        source_path = case[field].strip()
                        dest_path = os.path.join(case_folder, filename)

                        # Check if source and destination are the same
                        if os.path.abspath(source_path) == os.path.abspath(dest_path):
                            case[field] = dest_path
                            continue

                        if os.path.exists(source_path):
                            # Check if it's a PDF file (only copy PDF files to avoid corruption)
                            if not source_path.lower().endswith('.pdf'):
                                print(f"Warning: Skipping non-PDF file for {field}: {source_path}")
                                continue

                            try:
                                # Ensure destination directory exists
                                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                                # Try to copy the file first (safer than move)
                                import shutil
                                shutil.copy2(source_path, dest_path)
                                case[field] = dest_path
                                print(f"DEBUG: Successfully copied {field} to {dest_path}")
                            except Exception as e:
                                QMessageBox.warning(self, "File Save Error",
                                                  f"Failed to save {field} file: {str(e)}")
                                return
                        else:
                            QMessageBox.warning(self, "File Not Found",
                                              f"The selected {field} file could not be found: {source_path}")
                            return
                    else:
                        print(f"DEBUG: No file for {field}")
            except Exception as e:
                print(f"DEBUG: File operation error: {e}")
                raise
            print("DEBUG: About to connect to database")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            print("DEBUG: Database connection established")

            print("DEBUG: About to execute UPDATE statement")
            try:
                cursor.execute("""
                    UPDATE cases SET
                        transaction_no = ?, date_incurred = ?, date_identified = ?, date_reported = ?, description = ?,
                        bas_payment_no = ?, bas_payment_date = ?, persal_no = ?, category = ?, responsibility_id = ?, amount = ?,
                        source_document = ?, minutes = ?, evidence_path = ?, attachments = ?, status = ?, list = ?, assessment_assessed_by = ?,
                        assessment_date = ?, assessment_result = ?, fy_id = ?, period_id = ?, criminal_charges = ?, disciplinary_process = ?,
                        loss_recovery = ?, prevention_steps = ?, original_list = ?
                    WHERE transaction_no = ?
                """, (
                    case["transaction_no"], case["date_incurred"], case["date_identified"], case["date_reported"],
                    case["description"], case["bas_payment_no"], case["bas_payment_date"], case["persal_no"],
                    case["category"], case["responsibility_id"], case["amount"], case["source_document"],
                    case["minutes"], case["evidence_path"], case["attachments"], case["status"], case["list"],
                    case["assessment_assessed_by"], case["assessment_date"], case["assessment_result"],
                    case["fy_id"], case["period_id"],  # Use values from case dict
                    case["criminal_charges"], case["disciplinary_process"], case["loss_recovery"],
                    case["prevention_steps"], case["original_list"],  # Use value from case dict
                    self.transaction_no  # Use original transaction_no for WHERE clause
                ))
                print("DEBUG: UPDATE statement executed successfully")
            except Exception as e:
                print(f"DEBUG: UPDATE statement failed: {e}")
                print(f"DEBUG: Exception type: {type(e)}")
                raise
            conn.commit()
            case_id = self.case_data[0]  # Use existing case ID
            conn.close()
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


class EditCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Cases")
        self.setFixedSize(1700, 600)  # Match ViewCasesDialog width for consistency
        self.responsibilities = load_responsibilities()
        self.current_list = "Checklist"  # Default context

        # Apply professional theme
        apply_theme(self)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Compact search bars layout
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 5, 5, 5)
        search_layout.setSpacing(10)

        # Case number search - compact layout
        case_label = QLabel("Case No:")
        case_label.setFixedWidth(60)
        self.case_search_edit = QLineEdit()
        self.case_search_edit.setPlaceholderText("Enter case number...")
        self.case_search_edit.setFixedWidth(150)
        self.case_search_edit.returnPressed.connect(self.search_case_by_number)

        search_layout.addWidget(case_label)
        search_layout.addWidget(self.case_search_edit)

        # Separator
        search_layout.addSpacing(20)

        # Responsibility search - compact layout
        resp_label = QLabel("Responsibility:")
        resp_label.setFixedWidth(80)
        self.resp_search_edit = QLineEdit()
        self.resp_search_edit.setPlaceholderText("Type to search...")
        self.resp_search_edit.setFixedWidth(200)
        self.resp_search_edit.textChanged.connect(self.filter_responsibilities)

        search_layout.addWidget(resp_label)
        search_layout.addWidget(self.resp_search_edit)

        # Separator
        search_layout.addSpacing(20)

        # List filter - compact layout
        list_label = QLabel("List:")
        list_label.setFixedWidth(30)
        self.list_filter_combo = NoWheelComboBox()
        self.list_filter_combo.addItems([
            "All Cases", "Checklist", "Lead Schedule", "To-Do List",
            "Recovered", "Write-Off Recommended", "Written Off", "Deleted Cases"
        ])
        self.list_filter_combo.setCurrentText("All Cases")
        self.list_filter_combo.setFixedWidth(140)  # Increased width for longer list names
        self.list_filter_combo.currentTextChanged.connect(lambda: self.refresh_cases())

        search_layout.addWidget(list_label)
        search_layout.addWidget(self.list_filter_combo)

        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Main content layout
        content_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)

        self.resp_tree = QTreeWidget()
        self.resp_tree.setHeaderLabel("Responsibilities")
        self.resp_tree.itemSelectionChanged.connect(self.on_resp_select)
        splitter.addWidget(self.resp_tree)

        self.case_table = QTableWidget()
        self.case_table.setColumnCount(7)
        self.case_table.setHorizontalHeaderLabels([
            "Case No", "Date Reported", "Category", "Amount", "List", "Status", "To-Do"
        ])

        # Enable selection change to highlight responsibility
        self.case_table.itemSelectionChanged.connect(self.on_case_select)
        # Enable double-click to view case details (same as ViewCasesDialog)
        self.case_table.itemDoubleClicked.connect(self.show_case_details)

        # Set minimum width for headers and enable proper resizing
        header = self.case_table.horizontalHeader()
        header.setMinimumSectionSize(80)  # Minimum width for each column
        header.setSectionResizeMode(QHeaderView.Interactive)  # Allow manual resizing
        header.setStretchLastSection(True)  # Last column stretches to fill remaining space

        # Set default column widths for simplified layout (same as ViewCasesDialog)
        self.case_table.setColumnWidth(0, 120)  # Case No
        self.case_table.setColumnWidth(1, 140)  # Date Reported
        self.case_table.setColumnWidth(2, 150)  # Category
        self.case_table.setColumnWidth(3, 120)  # Amount
        self.case_table.setColumnWidth(4, 120)  # List
        self.case_table.setColumnWidth(5, 120)  # Status
        self.case_table.setColumnWidth(6, 80)   # To-Do

        # Set row height for better readability
        self.case_table.verticalHeader().setDefaultSectionSize(25)

        splitter.addWidget(self.case_table)

        splitter.setSizes([300, 700])
        content_layout.addWidget(splitter)
        layout.addLayout(content_layout)

        self.refresh_responsibilities()
        self.refresh_cases()

    def refresh_responsibilities(self):
        self.resp_tree.clear()
        resp_dict = {r["id"]: r for r in self.responsibilities}

        # Query database to find responsibilities with cases (same as ViewCasesDialog)
        self.responsibilities_with_cases = self.get_responsibilities_with_cases()

        top_level = [r for r in self.responsibilities if r["parent_id"] is None]
        for resp in top_level:
            self.add_resp_item(resp, None, resp_dict)

    def get_responsibilities_with_cases(self):
        """Get set of responsibility IDs that have cases, including their parents (same as ViewCasesDialog)"""
        responsibilities_with_cases = set()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get all responsibility IDs that have cases
            cursor.execute("SELECT DISTINCT responsibility_id FROM cases WHERE list != 'Deleted Cases'")
            case_resp_ids = {row[0] for row in cursor.fetchall()}

            # Include parent responsibilities
            for resp_id in case_resp_ids:
                responsibilities_with_cases.add(resp_id)
                # Find and add parent IDs
                resp = next((r for r in self.responsibilities if r["id"] == resp_id), None)
                if resp and resp["parent_id"]:
                    responsibilities_with_cases.add(resp["parent_id"])

            conn.close()
        except sqlite3.Error as e:
            print(f"Error querying responsibilities with cases: {e}")

        return responsibilities_with_cases

    def add_resp_item(self, resp, parent_item, resp_dict):
        item = QTreeWidgetItem([resp["name"]])
        item.setData(0, Qt.UserRole, resp["id"])

        # Bold responsibilities that have cases (same as ViewCasesDialog)
        if resp["id"] in self.responsibilities_with_cases:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        if parent_item is None:
            self.resp_tree.addTopLevelItem(item)
        else:
            parent_item.addChild(item)
        children = [r for r in self.responsibilities if r["parent_id"] == resp["id"]]
        for child in children:
            self.add_resp_item(child, item, resp_dict)

    def on_resp_select(self):
        selected = self.resp_tree.selectedItems()
        if selected:
            resp_id = selected[0].data(0, Qt.UserRole)
            subtree_ids = get_subtree_resp_ids(resp_id, self.responsibilities)
            self.refresh_cases(subtree_ids)
        else:
            self.refresh_cases()

    def on_case_select(self):
        """Highlight the responsibility in the tree when a case is selected"""
        selected_rows = set()
        for item in self.case_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            # Clear selection if no case is selected
            self.resp_tree.clearSelection()
            return

        # Get the first selected case's responsibility
        first_row = min(selected_rows)
        case_no = self.case_table.item(first_row, 0).text()

        # Get responsibility_id for this case
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT responsibility_id FROM cases WHERE transaction_no = ?", (case_no,))
            result = cursor.fetchone()
            conn.close()

            if result:
                responsibility_id = result[0]
                self.highlight_responsibility(responsibility_id)
        except sqlite3.Error as e:
            print(f"Error getting responsibility for case {case_no}: {e}")

    def highlight_responsibility(self, responsibility_id):
        """Find and highlight the responsibility in the tree"""
        def find_item_by_id(parent_item, target_id):
            """Recursively search for an item with the given ID"""
            if parent_item is None:
                # Search top-level items
                for i in range(self.resp_tree.topLevelItemCount()):
                    item = self.resp_tree.topLevelItem(i)
                    if item.data(0, Qt.UserRole) == target_id:
                        return item
                    # Search children
                    result = find_item_by_id(item, target_id)
                    if result:
                        return result
            else:
                # Search children of parent_item
                for i in range(parent_item.childCount()):
                    item = parent_item.child(i)
                    if item.data(0, Qt.UserRole) == target_id:
                        return item
                    # Search grandchildren
                    result = find_item_by_id(item, target_id)
                    if result:
                        return result
            return None

        # Find the responsibility item
        target_item = find_item_by_id(None, responsibility_id)

        if target_item:
            # Clear current selection
            self.resp_tree.clearSelection()
            # Select the target item
            target_item.setSelected(True)
            # Ensure it's visible
            self.resp_tree.scrollToItem(target_item)
            # Expand parent items to make it visible
            parent = target_item.parent()
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()

    def refresh_cases(self, resp_ids=None):
        self.case_table.setRowCount(0)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Build base query with list filtering
        base_conditions = ["list != 'Deleted Cases'"]
        params = []

        # Add list filter condition based on transaction_no suffixes
        selected_list = self.list_filter_combo.currentText()
        if selected_list == "Checklist":
            # Checklist shows all cases (main case numbers without -LS or -WOR suffixes)
            base_conditions.append("transaction_no NOT LIKE '%-LS' AND transaction_no NOT LIKE '%-WOR'")
        elif selected_list == "Lead Schedule":
            # Lead Schedule shows only cases with -LS suffix
            base_conditions.append("transaction_no LIKE '%-LS'")
        elif selected_list == "To-Do List":
            # Show both actual To-Do List cases and GJ cases with outstanding actions
            base_conditions.append("(list = 'To-Do List' OR bas_journal_no IS NOT NULL)")
        elif selected_list == "Write-Off Recommended":
            # Write-Off Recommended shows only cases with -WOR suffix
            base_conditions.append("transaction_no LIKE '%-WOR'")
        elif selected_list == "Recovered":
            base_conditions.append("list = 'Recovered'")
        elif selected_list == "Written Off":
            base_conditions.append("list = 'Written Off'")
        elif selected_list == "Deleted Cases":
            base_conditions.append("list = 'Deleted Cases'")
        # For "All Cases", we don't add any additional list condition

        # Add responsibility filter if provided
        if resp_ids:
            placeholders = ",".join("?" for _ in resp_ids)
            base_conditions.append(f"responsibility_id IN ({placeholders})")
            params.extend(resp_ids)

        where_clause = " AND ".join(base_conditions)
        query = f"SELECT transaction_no, date_reported, category, amount, list, status, bas_journal_no FROM cases WHERE {where_clause}"

        cursor.execute(query, params)
        for row_data in cursor.fetchall():
            row = self.case_table.rowCount()
            self.case_table.insertRow(row)
            for col, data in enumerate(row_data):
                if col == 6:  # To-Do column (bas_journal_no)
                    todo_value = "Yes" if data else "No"
                    self.case_table.setItem(row, col, QTableWidgetItem(todo_value))
                elif col == 3:  # Amount column
                    amount_item = format_currency_amount(data, right_align=True)
                    self.case_table.setItem(row, col, amount_item)
                elif col == 3:  # Amount column
                    amount_item = format_currency_amount(data, right_align=True)
                    self.case_table.setItem(row, col, amount_item)
                else:
                    self.case_table.setItem(row, col, QTableWidgetItem(str(data)))
        conn.close()

    def show_case_details(self, item):
        """Show editable case details when double-clicking a case in Manage Cases"""
        row = item.row()
        case_no = self.case_table.item(row, 0).text()

        # Get full case details from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE transaction_no = ?", (case_no,))
        case_data = cursor.fetchone()
        conn.close()

        if case_data:
            dialog = EditCaseDialog(case_data, self)
            if dialog.exec_():
                # Refresh the table after editing
                self.refresh_cases()

    def search_case_by_number(self):
        """Search for a specific case by case number"""
        case_no = self.case_search_edit.text().strip()
        if not case_no:
            self.refresh_cases()  # Show all cases if search is empty
            return

        self.case_table.setRowCount(0)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Build search query with list filtering
        base_conditions = ["transaction_no LIKE ?"]
        params = [f"%{case_no}%"]

        # Add list filter condition based on transaction_no suffixes
        selected_list = self.list_filter_combo.currentText()
        if selected_list == "Checklist":
            # Checklist shows all cases (main case numbers without -LS or -WOR suffixes)
            base_conditions.append("transaction_no NOT LIKE '%-LS' AND transaction_no NOT LIKE '%-WOR'")
        elif selected_list == "Lead Schedule":
            # Lead Schedule shows only cases with -LS suffix
            base_conditions.append("transaction_no LIKE '%-LS'")
        elif selected_list == "To-Do List":
            # Show both actual To-Do List cases and GJ cases with outstanding actions
            base_conditions.append("(list = 'To-Do List' OR bas_journal_no IS NOT NULL)")
        elif selected_list == "Recovered":
            base_conditions.append("list = 'Recovered'")
        elif selected_list == "Write-Off Recommended":
            # Write-Off Recommended shows only cases with -WOR suffix
            base_conditions.append("transaction_no LIKE '%-WOR'")
        elif selected_list == "Written Off":
            base_conditions.append("list = 'Written Off'")
        elif selected_list == "Deleted Cases":
            base_conditions.append("list = 'Deleted Cases'")
        else:  # "All Cases"
            base_conditions.append("list != 'Deleted Cases'")

        where_clause = " AND ".join(base_conditions)
        query = f"SELECT transaction_no, date_reported, category, amount, list, status, bas_journal_no FROM cases WHERE {where_clause}"

        cursor.execute(query, params)
        for row_data in cursor.fetchall():
            row = self.case_table.rowCount()
            self.case_table.insertRow(row)
            for col, data in enumerate(row_data):
                if col == 6:  # To-Do column (bas_journal_no)
                    todo_value = "Yes" if data else "No"
                    self.case_table.setItem(row, col, QTableWidgetItem(todo_value))
                else:
                    self.case_table.setItem(row, col, QTableWidgetItem(str(data)))
        conn.close()

    def filter_responsibilities(self, text):
        """Filter responsibilities based on search text (similar to ResponsibilitySelectionDialog)"""
        text = text.lower()
        if not text:
            self.refresh_responsibilities()
            return

        self.resp_tree.clear()

        # Find responsibilities that match the search text
        matching_resps = []
        parent_ids_to_include = set()

        for resp in self.responsibilities:
            if text in resp["name"].lower():
                matching_resps.append(resp)
                # Recursively collect all parent IDs up to the root
                current_parent_id = resp["parent_id"]
                while current_parent_id:
                    parent_ids_to_include.add(current_parent_id)
                    # Find the parent and get its parent_id
                    parent_resp = next((r for r in self.responsibilities if r["id"] == current_parent_id), None)
                    if parent_resp:
                        current_parent_id = parent_resp["parent_id"]
                    else:
                        current_parent_id = None

        # Include all parent responsibilities
        for resp in self.responsibilities:
            if resp["id"] in parent_ids_to_include:
                matching_resps.append(resp)

        # Remove duplicates while preserving order
        seen_ids = set()
        filtered_resps = []
        for resp in matching_resps:
            if resp["id"] not in seen_ids:
                filtered_resps.append(resp)
                seen_ids.add(resp["id"])

        # Create parent map for filtered results
        parent_map = defaultdict(list)
        for resp in filtered_resps:
            parent_map[resp["parent_id"]].append(resp)

        def add_filtered_items(parent_item, parent_id):
            for resp in sorted(parent_map[parent_id], key=lambda x: x["name"]):
                item = QTreeWidgetItem([resp["name"]])
                item.setData(0, Qt.UserRole, resp["id"])

                # Bold responsibilities that have cases (same as original)
                if resp["id"] in self.responsibilities_with_cases:
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)

                if parent_id is None:
                    self.resp_tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                add_filtered_items(item, resp["id"])

        add_filtered_items(None, None)
        self.resp_tree.expandAll()

    def edit_case_by_id(self, case_id):
        """Edit case by database ID"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
            case = cursor.fetchone()
            conn.close()

            if case:
                dialog = EditCaseDialog(case, self)
                if dialog.exec_():
                    self.refresh_cases()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to load case: {str(e)}")

    def delete_case_by_id(self, case_id):
        """Delete case by database ID"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT transaction_no, list FROM cases WHERE id = ?", (case_id,))
            case_data = cursor.fetchone()
            conn.close()

            if case_data:
                transaction_no, current_list = case_data
                reply = QMessageBox.question(
                    self, "Confirm Move to Deleted Cases",
                    f"Move case {transaction_no} to Deleted Cases?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE cases SET list = 'Deleted Cases', original_list = ? WHERE id = ?", (current_list, case_id))
                    conn.commit()
                    conn.close()
                    QMessageBox.information(self, "Success", "Case moved to Deleted Cases.")
                    self.refresh_cases()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to delete case: {str(e)}")

    def edit_case(self, row):
        transaction_no = self.case_table.item(row, 0).text()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE transaction_no = ?", (transaction_no,))
        case = cursor.fetchone()
        conn.close()
        dialog = EditCaseDialog(case, self)
        if dialog.exec_():
            # Refresh the table after editing - the EditCaseDialog handles all status changes and suffix updates
            self.refresh_cases()

    def delete_case(self, row):
        transaction_no = self.case_table.item(row, 0).text()
        reply = QMessageBox.question(self, "Confirm Move to Deleted Cases", f"Move case {transaction_no} to Deleted Cases?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT id, list FROM cases WHERE transaction_no = ?", (transaction_no,))
                case_data = cursor.fetchone()
                case_id = case_data[0]
                original_list = case_data[1]
                cursor.execute("UPDATE cases SET list = 'Deleted Cases', original_list = ? WHERE transaction_no = ?", (original_list, transaction_no))
                conn.commit()
                conn.close()
                save_audit_log("move_to_deleted_cases", {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": case_id,
                    "transaction_no": transaction_no,
                    "details": {"original_list": original_list}
                }, get_financial_year())
                QMessageBox.information(self, "Success", "Case moved to Deleted Cases.")
                self.refresh_cases()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to move case: {str(e)}")