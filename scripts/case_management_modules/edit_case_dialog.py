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
    QCalendarWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
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
from scripts.ui.components.custom_widgets import NoWheelComboBox
from .case_business_logic import CaseBusinessLogic
from collections import defaultdict
from .responsibility_selection import ResponsibilitySelectionDialog
from .determination_dialog import DeterminationDialog




class EditCaseDialog(QDialog):
    def __init__(self, case_data, parent=None, selected_list=None):
        super().__init__(parent)
        # Set title with list context for better user understanding
        self.list_name = case_data[16] if len(case_data) > 16 else "Unknown"
        title_list = selected_list or self.list_name
        # Override title based on transaction_no suffix
        if "-LS" in case_data[1]:
            title_list = "Lead Schedule"
        elif "-WOR" in case_data[1]:
            title_list = "Write-Off Recommended"
        self.setWindowTitle(f"Edit Case Details - {title_list}")
        self.setFixedSize(1200, 900)
        try:
            self.responsibilities = load_posting_responsibilities()
            self.categories = load_categories()
            self.lists = load_lists()
            self.fy = get_financial_year()
            self.transaction_no = case_data[1]  # Pre-populate with existing case data
            self.selected_responsibility_id = case_data[10]  # responsibility_id
            self.case_data = case_data
            self.selected_list = selected_list  # From parent dialog's filter
            self.supporting_evidence_compulsory = False
            self.business_logic = CaseBusinessLogic(self.fy)

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
        self.main_layout = QVBoxLayout(scroll_widget)

        # ===== BASIC CASE INFORMATION GROUP =====
        basic_group = QGroupBox("Basic Case Information")
        basic_layout = QFormLayout(basic_group)

        # Case Number (read-only)
        self.trans_no_edit = QLineEdit(self.transaction_no)
        self.trans_no_edit.setReadOnly(True)
        basic_layout.addRow("Case No:", self.trans_no_edit)

        # Responsibility
        resp_layout = QHBoxLayout()
        self.responsibility_edit = QLineEdit()
        self.responsibility_edit.setReadOnly(True)
        self.responsibility_edit.setPlaceholderText("Click Select to choose responsibility...")
        resp_layout.addWidget(self.responsibility_edit)

        self.select_responsibility_button = QPushButton("Select")
        self.select_responsibility_button.clicked.connect(self.select_responsibility)
        resp_layout.addWidget(self.select_responsibility_button)

        basic_layout.addRow("Responsibility:", resp_layout)

        # Amount (moved here as it's crucial information)
        self.amount_edit = QLineEdit()
        basic_layout.addRow("Amount:", self.amount_edit)

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

        basic_layout.addRow("Dates:", date_group)

        # Description (larger for paragraphs)
        self.description_edit = QTextEdit()
        self.description_edit.setMinimumHeight(80)
        basic_layout.addRow("Description:", self.description_edit)

        # Category and List
        category_list_layout = QHBoxLayout()
        self.category_combo = NoWheelComboBox()
        self.category_combo.addItems([c["name"] for c in self.categories])
        category_list_layout.addWidget(QLabel("Category:"))
        category_list_layout.addWidget(self.category_combo)

        category_list_layout.addSpacing(20)

        self.list_combo = NoWheelComboBox()
        system_lists = [l["name"] for l in self.lists if l.get("is_system", False)]
        self.list_combo.addItems(system_lists)
        # Select default list
        if system_lists:
            default_list = next((l for l in self.lists if l.get("is_default", False)), None)
            if default_list and default_list["name"] in system_lists:
                self.list_combo.setCurrentText(default_list["name"])
        # Make list combo read-only since lists are managed by workflow
        self.list_combo.setEnabled(False)
        category_list_layout.addWidget(QLabel("List:"))
        category_list_layout.addWidget(self.list_combo)

        # Add visual indicator for list context
        current_list = self.list_combo.currentText()
        if current_list == "Lead Schedule":
            context_label = QLabel("🔍 Loss Control Committee Review")
            context_label.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 12px;")
            category_list_layout.addSpacing(20)
            category_list_layout.addWidget(context_label)
        elif current_list == "Write-Off Recommended":
            context_label = QLabel("⚖️ Write-Off Approval Pending")
            context_label.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 12px;")
            category_list_layout.addSpacing(20)
            category_list_layout.addWidget(context_label)

        basic_layout.addRow("", category_list_layout)

        self.main_layout.addWidget(basic_group)

        # ===== LIST STATUS INFORMATION GROUP =====
        list_status_group = QGroupBox("List Status Information")
        list_status_layout = QVBoxLayout(list_status_group)

        # Create a simple grid layout for reliable text display
        self.list_status_grid_widget = QWidget()
        grid_layout = QGridLayout(self.list_status_grid_widget)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        grid_layout.setSpacing(5)

        # Headers
        headers = ["Checklist", "Lead Schedule", "Recovered", "Write-Off Recommended", "Written Off", "Deleted Cases"]

        # Get comprehensive status information for all lists this case appears in
        transaction_no = self.case_data[1]  # transaction_no is always at index 1

        # Query database to get status for this case across all lists
        list_statuses_dict = self.get_case_statuses_across_lists(transaction_no)

        # Determine status for each list based on database query results
        list_statuses = []
        for header in headers:
            if header in list_statuses_dict:
                # Show the actual status for lists where this case exists
                list_statuses.append(list_statuses_dict[header])
            else:
                # Show N/A for lists the case is not in
                list_statuses.append("N/A")

        # Add headers (row 0)
        for i, header in enumerate(headers):
            header_label = QLabel(header)
            header_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    padding: 8px;
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    text-align: center;
                }
            """)
            header_label.setAlignment(Qt.AlignCenter)
            header_label.setMinimumHeight(40)
            grid_layout.addWidget(header_label, 0, i)

        # Add status values (row 1)
        for i, status in enumerate(list_statuses):
            status_label = QLabel(status)
            status_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    border: 1px solid #ddd;
                    text-align: center;
                    background-color: white;
                }
            """)
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setMinimumHeight(40)
            status_label.setWordWrap(True)  # Allow text to wrap if needed
            grid_layout.addWidget(status_label, 1, i)

        list_status_layout.addWidget(self.list_status_grid_widget)
        self.main_layout.addWidget(list_status_group)

        # ===== ASSESSMENT GROUP =====
        assessment_group = QGroupBox("Assessment")
        assessment_layout = QFormLayout(assessment_group)

        # Status
        self.status_combo = NoWheelComboBox()
        # Populate with default items initially
        self.status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed"])
        self.status_combo.setCurrentText("Alleged")
        assessment_layout.addRow("Status:", self.status_combo)

        # Assessment Evidence (conditional)
        self.evidence_label = QLabel("Assessment Evidence:")
        self.evidence_edit = QLineEdit()
        self.evidence_button = QPushButton("Browse")
        self.evidence_button.clicked.connect(self.browse_evidence)
        self.evidence_view_button = QPushButton("View")
        self.evidence_view_button.clicked.connect(self.view_evidence)
        evidence_layout = QHBoxLayout()
        evidence_layout.addWidget(self.evidence_edit)
        evidence_layout.addWidget(self.evidence_button)
        evidence_layout.addWidget(self.evidence_view_button)
        assessment_layout.addRow(self.evidence_label, evidence_layout)

        self.main_layout.addWidget(assessment_group)

        # ===== LOSS CONTROL GROUP =====
        loss_control_group = QGroupBox("Loss Control Committee")
        loss_control_layout = QFormLayout(loss_control_group)

        # Status
        self.loss_control_status_combo = NoWheelComboBox()
        loss_control_layout.addRow("Status:", self.loss_control_status_combo)

        # Recommendation field removed - merged into Status field above

        # Recovery Evidence (conditional)
        self.recovery_evidence_label = QLabel("Recovery Evidence:")
        self.recovery_evidence_edit = QLineEdit()
        self.recovery_evidence_button = QPushButton("Browse")
        self.recovery_evidence_button.clicked.connect(self.browse_recovery_evidence)
        self.recovery_evidence_view_button = QPushButton("View")
        self.recovery_evidence_view_button.clicked.connect(self.view_recovery_evidence)
        recovery_evidence_layout = QHBoxLayout()
        recovery_evidence_layout.addWidget(self.recovery_evidence_edit)
        recovery_evidence_layout.addWidget(self.recovery_evidence_button)
        recovery_evidence_layout.addWidget(self.recovery_evidence_view_button)
        loss_control_layout.addRow(self.recovery_evidence_label, recovery_evidence_layout)

        # LC Minutes
        self.minutes_label = QLabel("LC Minutes:")
        self.minutes_edit = QLineEdit()
        self.minutes_button = QPushButton("Browse")
        self.minutes_button.clicked.connect(self.browse_minutes)
        self.minutes_view_button = QPushButton("View")
        self.minutes_view_button.clicked.connect(self.view_minutes)
        minutes_layout = QHBoxLayout()
        minutes_layout.addWidget(self.minutes_edit)
        minutes_layout.addWidget(self.minutes_button)
        minutes_layout.addWidget(self.minutes_view_button)
        loss_control_layout.addRow(self.minutes_label, minutes_layout)

        self.main_layout.addWidget(loss_control_group)

        # ===== SUPPORTING EVIDENCE GROUP =====
        supporting_group = QGroupBox("Supporting Evidence (To Prove Existence)")
        supporting_layout = QFormLayout(supporting_group)

        # BAS Payment fields
        self.bas_label = QLabel("BAS Payment No:")
        self.bas_payment_no_edit = QLineEdit()
        supporting_layout.addRow(self.bas_label, self.bas_payment_no_edit)

        # BAS Payment Date with manual date picker
        bas_payment_date_layout = QHBoxLayout()
        self.bas_date_label = QLabel("BAS Payment Date:")
        self.bas_payment_date_edit = QLineEdit()
        self.bas_payment_date_edit.setPlaceholderText("YYYY-MM-DD")
        self.bas_payment_date_button = QPushButton("...")
        self.bas_payment_date_button.setFixedWidth(30)
        self.bas_payment_date_button.clicked.connect(self.select_bas_payment_date)
        bas_payment_date_layout.addWidget(self.bas_payment_date_edit)
        bas_payment_date_layout.addWidget(self.bas_payment_date_button)
        supporting_layout.addRow(self.bas_date_label, bas_payment_date_layout)

        # BAS Journal fields
        self.bas_journal_label = QLabel("BAS Journal No:")
        self.bas_journal_no_edit = QLineEdit()
        supporting_layout.addRow(self.bas_journal_label, self.bas_journal_no_edit)

        # BAS Journal Date with manual date picker
        bas_journal_date_layout = QHBoxLayout()
        self.bas_journal_date_label = QLabel("BAS Journal Date:")
        self.bas_journal_date_edit = QLineEdit()
        self.bas_journal_date_edit.setPlaceholderText("YYYY-MM-DD")
        self.bas_journal_date_button = QPushButton("...")
        self.bas_journal_date_button.setFixedWidth(30)
        self.bas_journal_date_button.clicked.connect(self.select_bas_journal_date)
        bas_journal_date_layout.addWidget(self.bas_journal_date_edit)
        bas_journal_date_layout.addWidget(self.bas_journal_date_button)
        supporting_layout.addRow(self.bas_journal_date_label, bas_journal_date_layout)

        # Persal No field
        self.persal_label = QLabel("Persal No:")
        self.persal_no_edit = QLineEdit()
        supporting_layout.addRow(self.persal_label, self.persal_no_edit)

        # Supporting Evidence Document upload
        self.supporting_evidence_label = QLabel("Supporting Evidence Document:")
        self.supporting_evidence_edit = QLineEdit()
        self.supporting_evidence_button = QPushButton("Browse")
        self.supporting_evidence_button.clicked.connect(self.browse_supporting_evidence)
        self.supporting_evidence_view_button = QPushButton("View")
        self.supporting_evidence_view_button.clicked.connect(self.view_supporting_evidence)
        supporting_evidence_layout = QHBoxLayout()
        supporting_evidence_layout.addWidget(self.supporting_evidence_edit)
        supporting_evidence_layout.addWidget(self.supporting_evidence_button)
        supporting_evidence_layout.addWidget(self.supporting_evidence_view_button)
        supporting_layout.addRow(self.supporting_evidence_label, supporting_evidence_layout)

        self.main_layout.addWidget(supporting_group)

        # ===== ADDITIONAL INFORMATION GROUP =====
        additional_group = QGroupBox("Additional Information")
        additional_layout = QFormLayout(additional_group)

        # Amount moved to Basic Case Information group

        # Criminal Charges Laid
        self.criminal_charges_combo = NoWheelComboBox()
        self.criminal_charges_combo.addItems(["N/A", "Yes", "No"])
        self.criminal_charges_combo.setCurrentText("N/A")
        additional_layout.addRow("Criminal Charges Laid:", self.criminal_charges_combo)

        # Disciplinary process
        self.disciplinary_combo = NoWheelComboBox()
        self.disciplinary_combo.addItems(["N/A", "Yes", "No"])
        self.disciplinary_combo.setCurrentText("N/A")
        additional_layout.addRow("Disciplinary process in progress or completed:", self.disciplinary_combo)

        # Loss recovery
        self.loss_recovery_combo = NoWheelComboBox()
        self.loss_recovery_combo.addItems(["N/A", "Yes", "No"])
        self.loss_recovery_combo.setCurrentText("N/A")
        additional_layout.addRow("Loss recovery commenced or completed:", self.loss_recovery_combo)

        # Steps to prevent future occurrence
        self.prevention_steps_edit = QTextEdit()
        self.prevention_steps_edit.setMinimumHeight(40)
        additional_layout.addRow("Steps taken to prevent future occurrence of F&W expenditure:", self.prevention_steps_edit)

        self.main_layout.addWidget(additional_group)

        # ===== FILE ATTACHMENTS GROUP =====
        attachments_group = QGroupBox("File Attachments")
        attachments_layout = QFormLayout(attachments_group)

        # Source Document
        self.source_doc_label = QLabel("Source Document:")
        self.source_doc_edit = QLineEdit()
        self.source_doc_button = QPushButton("Browse")
        self.source_doc_button.clicked.connect(self.browse_source_doc)
        self.source_doc_view_button = QPushButton("View")
        self.source_doc_view_button.clicked.connect(self.view_source_doc)
        source_doc_layout = QHBoxLayout()
        source_doc_layout.addWidget(self.source_doc_edit)
        source_doc_layout.addWidget(self.source_doc_button)
        source_doc_layout.addWidget(self.source_doc_view_button)
        attachments_layout.addRow(self.source_doc_label, source_doc_layout)

        self.main_layout.addWidget(attachments_group)

        # Set up scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Connect signals - conditional fields will be updated in load_case_data
        # self.update_conditional_fields()  # Commented out to avoid double call

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
        self.loss_control_status_combo.currentTextChanged.connect(self.on_loss_control_status_changed)

        # Update determination button visibility
        self.update_determination_button_visibility()

    def load_case_data(self):
        """Load existing case data into the form fields"""
        # Temporarily disconnect signals to prevent triggering update_conditional_fields during loading
        self.category_combo.currentIndexChanged.disconnect(self.update_conditional_fields)
        self.list_combo.currentTextChanged.disconnect(self.update_conditional_fields)
        self.status_combo.currentTextChanged.disconnect(self.on_status_changed)

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

        # Set list - use selected_list from parent if provided, otherwise from case data
        list_text = self.selected_list if self.selected_list else (self.case_data[16] if self.case_data[16] else "")
        if list_text:
            self.list_combo.setCurrentText(list_text)

        # Update conditional fields first to populate status combo with correct items
        self.update_conditional_fields()

        # Set status
        if self.case_data[15]:  # status at index 15
            self.status_combo.setCurrentText(self.case_data[15])

        # Update conditional fields again to show/hide fields based on the loaded status
        self.update_conditional_fields()

        # Reconnect signals
        self.category_combo.currentIndexChanged.connect(self.update_conditional_fields)
        self.list_combo.currentTextChanged.connect(self.update_conditional_fields)
        self.status_combo.currentTextChanged.connect(self.on_status_changed)

        # Check if case is finalized and disable editing if so
        if len(self.case_data) > 37 and self.case_data[37]:  # is_finalized
            self.setWindowTitle(f"Edit Case Details - {self.list_name} (FINALIZED)")
            # Disable all input fields for finalized cases
            self.description_edit.setReadOnly(True)
            self.amount_edit.setReadOnly(True)
            self.date_incurred_edit.setReadOnly(True)
            self.date_identified_edit.setReadOnly(True)
            self.date_reported_edit.setReadOnly(True)
            self.status_combo.setEnabled(False)
            self.evidence_edit.setReadOnly(True)
            self.evidence_button.setEnabled(False)
            self.bas_payment_no_edit.setReadOnly(True)
            self.bas_payment_date_edit.setReadOnly(True)
            self.bas_payment_date_button.setEnabled(False)
            self.bas_journal_no_edit.setReadOnly(True)
            self.bas_journal_date_edit.setReadOnly(True)
            self.bas_journal_date_button.setEnabled(False)
            self.persal_no_edit.setReadOnly(True)
            self.minutes_edit.setReadOnly(True)
            self.minutes_button.setEnabled(False)
            self.source_doc_edit.setReadOnly(True)
            self.source_doc_button.setEnabled(False)
            self.supporting_evidence_edit.setReadOnly(True)
            self.supporting_evidence_button.setEnabled(False)
            self.criminal_charges_combo.setEnabled(False)
            self.disciplinary_combo.setEnabled(False)
            self.loss_recovery_combo.setEnabled(False)
            self.prevention_steps_edit.setReadOnly(True)

            # Disable save button for finalized cases
            self.save_button.setEnabled(False)
            self.save_button.setText("Case Finalized - No Changes Allowed")

            # Add finalization notice
            if len(self.case_data) > 36 and self.case_data[36]:  # finalization_reason
                finalization_label = QLabel(f"📋 Finalized: {self.case_data[36]}")
                finalization_label.setStyleSheet("color: #d32f2f; font-weight: bold; font-size: 14px; margin-top: 10px;")
                self.main_layout.insertWidget(0, finalization_label)

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
            self.bas_payment_date_edit.setText(self.case_data[7])
        else:
            self.bas_payment_date_edit.clear()  # Clear date if NULL

        # Set BAS Journal fields
        if len(self.case_data) > 29 and self.case_data[29]:  # bas_journal_no
            self.bas_journal_no_edit.setText(self.case_data[29])
        if len(self.case_data) > 30 and self.case_data[30]:  # bas_journal_date
            self.bas_journal_date_edit.setText(self.case_data[30])
        else:
            self.bas_journal_date_edit.clear()  # Clear date if NULL

        # Set Persal No
        if self.case_data[8]:  # persal_no
            self.persal_no_edit.setText(self.case_data[8])

        # Set file paths - only if files still exist
        if self.case_data[12] and os.path.exists(self.case_data[12]):  # source_document
            self.source_doc_edit.setText(self.case_data[12])
        elif self.case_data[12]:
            print(f"Warning: Source document file not found: {self.case_data[12]}")
            # Clear the field so user can select a new file
            self.source_doc_edit.clear()

        # Set supporting evidence path
        if len(self.case_data) > 13 and self.case_data[13] and os.path.exists(self.case_data[13]):  # supporting_evidence_path
            self.supporting_evidence_edit.setText(self.case_data[13])
        elif len(self.case_data) > 13 and self.case_data[13]:
            print(f"Warning: Supporting evidence file not found: {self.case_data[13]}")
            self.supporting_evidence_edit.clear()

        if len(self.case_data) > 13 and self.case_data[13] and os.path.exists(self.case_data[13]):  # minutes at 13
            self.minutes_edit.setText(self.case_data[13])
        elif len(self.case_data) > 13 and self.case_data[13]:
            print(f"Warning: Minutes file not found: {self.case_data[13]}")
            self.minutes_edit.clear()

        if len(self.case_data) > 14 and self.case_data[14] and os.path.exists(self.case_data[14]):  # evidence_path at 14
            self.evidence_edit.setText(self.case_data[14])
        elif len(self.case_data) > 14 and self.case_data[14]:
            print(f"Warning: Evidence file not found: {self.case_data[14]}")
            self.evidence_edit.clear()

        # Set Loss Control fields - use status from loss_control_recommendation field (index 40)
        if len(self.case_data) > 40 and self.case_data[40]:  # loss_control_recommendation at index 40
            self.loss_control_status_combo.setCurrentText(self.case_data[40])
            # Update recovery evidence visibility, LC Minutes placeholder, and list status grid based on status

            # First, reset all statuses to N/A
            self.update_list_status_grid("Recovered", "N/A")
            self.update_list_status_grid("Write-Off Recommended", "N/A")

            status = self.case_data[40]
            if status == "Recovered":
                self.recovery_evidence_label.setVisible(True)
                self.recovery_evidence_edit.setVisible(True)
                self.recovery_evidence_button.setVisible(True)
                self.recovery_evidence_view_button.setVisible(True)
                self.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")
                # Update List Status Information grid
                self.update_list_status_grid("Recovered", "Recovered")
            elif status == "Write Off Recommended":
                self.recovery_evidence_label.setVisible(False)
                self.recovery_evidence_edit.setVisible(False)
                self.recovery_evidence_button.setVisible(False)
                self.recovery_evidence_view_button.setVisible(False)
                self.recovery_evidence_edit.clear()
                self.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")
                # Update List Status Information grid
                self.update_list_status_grid("Write-Off Recommended", "Write Off Recommended")
            else:
                self.recovery_evidence_label.setVisible(False)
                self.recovery_evidence_edit.setVisible(False)
                self.recovery_evidence_button.setVisible(False)
                self.recovery_evidence_view_button.setVisible(False)
                self.recovery_evidence_edit.clear()
                self.minutes_edit.setPlaceholderText("")

        if len(self.case_data) > 19 and self.case_data[19] and os.path.exists(self.case_data[19]):  # recovery_evidence_path
            self.recovery_evidence_edit.setText(self.case_data[19])
        elif len(self.case_data) > 19 and self.case_data[19]:
            print(f"Warning: Recovery evidence file not found: {self.case_data[19]}")
            self.recovery_evidence_edit.clear()


    def select_responsibility(self):
        dialog = ResponsibilitySelectionDialog(self)
        if dialog.exec_():
            selected = dialog.get_selected_responsibility()
            if selected:
                self.responsibility_edit.setText(selected["name"])
                self.selected_responsibility_id = selected["id"]

    def on_status_changed(self, status):
        """Handle status selection change with validation and special logic"""
        current_list = self.list_combo.currentText()
        current_status = self.status_combo.currentText()

        # Validate status progression based on current list
        if not self.is_valid_status_transition(current_list, current_status, status):
            QMessageBox.warning(self, "Invalid Status Transition",
                              f"Cannot change status from '{current_status}' to '{status}' in {current_list}.\n\n"
                              "Please follow the proper workflow progression.")
            # Revert to current status
            self.status_combo.setCurrentText(current_status)
            return

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
                # Revert to previous status
                self.status_combo.setCurrentText(current_status)
                self.supporting_evidence_compulsory = False
        elif status == "Confirmed":
            # Show warning dialog for Confirmed status
            reply = QMessageBox.question(
                self,
                "Confirm Confirmed Status",
                "Selecting 'Confirmed' means this case IS Fruitless and Wasteful Expenditure.\n\n"
                "The case will be copied to the Lead Schedule for further processing.\n\n"
                "Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                # Revert to previous status
                self.status_combo.setCurrentText(current_status)
        else:
            # Reset the compulsory flag for other statuses
            self.supporting_evidence_compulsory = False

        # Update List Status Information grid based on new status
        if status == "Confirmed" and current_list == "Checklist":
            # When status becomes Confirmed in Checklist, show it will be copied to Lead Schedule
            self.update_list_status_grid("Checklist", "Confirmed")
            self.update_list_status_grid("Lead Schedule", "Awaiting LC determination")
            # Reset other lists
            self.update_list_status_grid("Recovered", "N/A")
            self.update_list_status_grid("Write-Off Recommended", "N/A")
            self.update_list_status_grid("Written Off", "N/A")
            self.update_list_status_grid("Deleted Cases", "N/A")
        elif status != "Confirmed":
            # For non-Confirmed statuses, reset Lead Schedule and other workflow lists
            self.update_list_status_grid("Lead Schedule", "N/A")
            self.update_list_status_grid("Recovered", "N/A")
            self.update_list_status_grid("Write-Off Recommended", "N/A")
            self.update_list_status_grid("Written Off", "N/A")
            self.update_list_status_grid("Deleted Cases", "N/A")
            # Update current list status
            if current_list in ["Checklist", "Lead Schedule", "Recovered", "Write-Off Recommended", "Written Off", "Deleted Cases"]:
                self.update_list_status_grid(current_list, status)

        # Update conditional fields to show/hide assessment evidence based on new status
        # Temporarily disconnect signal to avoid recursion
        self.status_combo.currentTextChanged.disconnect(self.on_status_changed)
        self.update_conditional_fields()
        self.status_combo.currentTextChanged.connect(self.on_status_changed)

    def update_conditional_fields(self):
        """Update visibility of conditional fields based on list and status selection"""
        try:
            # Get current selections safely
            selected_list = self.list_combo.currentText() if self.list_combo.count() > 0 else ""
            selected_status = self.status_combo.currentText() if self.status_combo.count() > 0 else ""
            selected_category = self.category_combo.currentText() if self.category_combo.count() > 0 else ""


            # Update status options based on transaction_no (more reliable than list field)
            if hasattr(self, 'status_combo'):
                current_status = self.status_combo.currentText()

                # Determine the correct items based on transaction_no suffix
                if "-LS" in self.transaction_no:
                    new_items = ["Awaiting LC determination", "Recovered", "Write Off Recommended"]
                elif "-WOR" in self.transaction_no:
                    new_items = ["Write Off Recommended", "Written Off"]
                else:
                    new_items = ["Alleged", "Under Assessment", "Valid", "Confirmed"]

                # Only update if items have actually changed
                current_items = [self.status_combo.itemText(i) for i in range(self.status_combo.count())]
                if current_items != new_items:
                    self.status_combo.clear()
                    self.status_combo.addItems(new_items)

                    # Restore the previous selection if it's still valid
                    if current_status and current_status in new_items:
                        self.status_combo.setCurrentText(current_status)
                    else:
                        # Set appropriate default based on transaction_no
                        if "-LS" in self.transaction_no:
                            self.status_combo.setCurrentText("Awaiting LC determination")
                        elif "-WOR" in self.transaction_no:
                            self.status_combo.setCurrentText("Write Off Recommended")
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
            if hasattr(self, 'bas_payment_date_button'):
                self.bas_payment_date_button.setVisible(bas_comp)

            # Update Persal field visibility and labels
            if hasattr(self, 'persal_label'):
                self.persal_label.setText("Persal No:" + (" *" if persal_comp else ""))
                self.persal_label.setVisible(persal_comp)
            if hasattr(self, 'persal_no_edit'):
                self.persal_no_edit.setVisible(persal_comp)

            # Update assessment fields visibility (Checklist or Lead Schedule + Valid/Confirmed)
            # Use transaction_no to determine if it's a case that can have assessment
            show_assessment = (not "-WOR" in self.transaction_no and
                              selected_status in ["Valid", "Confirmed"])

            # Assessment Evidence fields (Status + Evidence)
            if hasattr(self, 'evidence_label'):
                self.evidence_label.setVisible(show_assessment)
            if hasattr(self, 'evidence_edit'):
                self.evidence_edit.setVisible(show_assessment)
            if hasattr(self, 'evidence_button'):
                self.evidence_button.setVisible(show_assessment)
            if hasattr(self, 'evidence_view_button'):
                self.evidence_view_button.setVisible(show_assessment)

            # Update Loss Control fields visibility - show for all cases
            show_loss_control = True

            print(f"DEBUG: Setting Loss Control visibility to {show_loss_control}")

            # Set the group box visibility
            if hasattr(self, 'loss_control_group'):
                self.loss_control_group.setVisible(show_loss_control)

            if show_loss_control:
                # Populate status combo with merged options
                loss_control_items = ["Awaiting LC determination", "Recovered", "Write Off Recommended"]
                if self.loss_control_status_combo.count() != len(loss_control_items) or [self.loss_control_status_combo.itemText(i) for i in range(self.loss_control_status_combo.count())] != loss_control_items:
                    self.loss_control_status_combo.clear()
                    self.loss_control_status_combo.addItems(loss_control_items)
                    # Set to Awaiting LC determination
                    self.loss_control_status_combo.setCurrentText("Awaiting LC determination")
                # Make it editable for user selection
                self.loss_control_status_combo.setEnabled(True)

            self.loss_control_status_combo.setVisible(show_loss_control)

            # Recovery Evidence and LC Minutes visibility based on status
            status = self.loss_control_status_combo.currentText()
            show_recovery = show_loss_control and status == "Recovered"
            self.recovery_evidence_label.setVisible(show_recovery)
            self.recovery_evidence_edit.setVisible(show_recovery)
            self.recovery_evidence_button.setVisible(show_recovery)
            self.recovery_evidence_view_button.setVisible(show_recovery)

            # Update List Status Information grid - reset all first, then set current
            if show_loss_control:
                # Reset all statuses
                self.update_list_status_grid("Recovered", "N/A")
                self.update_list_status_grid("Write-Off Recommended", "N/A")

                # Set current status
                if status == "Recovered":
                    self.update_list_status_grid("Recovered", "Recovered")
                elif status == "Write Off Recommended":
                    self.update_list_status_grid("Write-Off Recommended", "Write Off Recommended")

            # Set LC Minutes placeholder based on status
            if show_loss_control and status in ["Recovered", "Write Off Recommended"]:
                self.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")
            elif show_loss_control:
                self.minutes_edit.setPlaceholderText("")

            self.minutes_label.setVisible(show_loss_control)
            self.minutes_edit.setVisible(show_loss_control)
            self.minutes_button.setVisible(show_loss_control)
            self.minutes_view_button.setVisible(show_loss_control)

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

    def view_evidence(self):
        """Open the assessment evidence file with the default application"""
        file_path = self.evidence_edit.text().strip()
        if file_path and os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")
        else:
            QMessageBox.warning(self, "File Not Found", "The assessment evidence file could not be found.")

    def view_minutes(self):
        """Open the Loss Control minutes file with the default application"""
        file_path = self.minutes_edit.text().strip()
        if file_path and os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")
        else:
            QMessageBox.warning(self, "File Not Found", "The Loss Control minutes file could not be found.")


    def view_supporting_evidence(self):
        """Open the supporting evidence file with the default application"""
        file_path = self.supporting_evidence_edit.text().strip()
        if file_path and os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")
        else:
            QMessageBox.warning(self, "File Not Found", "The supporting evidence file could not be found.")

    def view_source_doc(self):
        """Open the source document file with the default application"""
        file_path = self.source_doc_edit.text().strip()
        if file_path and os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")
        else:
            QMessageBox.warning(self, "File Not Found", "The source document file could not be found.")

    def browse_supporting_evidence(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Supporting Evidence", "", "PDF Files (*.pdf)")
        if file_path:
            self.supporting_evidence_edit.setText(file_path)

    def on_loss_control_status_changed(self, status):
        """Handle Loss Control Status change"""
        # First, reset all statuses to N/A to clear any previous selections
        self.update_list_status_grid("Recovered", "N/A")
        self.update_list_status_grid("Write-Off Recommended", "N/A")

        if status == "Recovered":
            # Show recovery evidence fields
            self.recovery_evidence_label.setVisible(True)
            self.recovery_evidence_edit.setVisible(True)
            self.recovery_evidence_button.setVisible(True)
            self.recovery_evidence_view_button.setVisible(True)
            self.recovery_evidence_edit.setPlaceholderText("Recovery evidence is REQUIRED")

            # Show LC Minutes as required
            self.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")

            # Update List Status Information grid
            self.update_list_status_grid("Recovered", "Recovered")

        elif status == "Write Off Recommended":
            # Hide recovery evidence fields (not needed for Write Off)
            self.recovery_evidence_label.setVisible(False)
            self.recovery_evidence_edit.setVisible(False)
            self.recovery_evidence_button.setVisible(False)
            self.recovery_evidence_view_button.setVisible(False)
            self.recovery_evidence_edit.clear()

            # Show LC Minutes as required
            self.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")

            # Update List Status Information grid
            self.update_list_status_grid("Write-Off Recommended", "Write Off Recommended")

        else:
            # Hide recovery evidence fields
            self.recovery_evidence_label.setVisible(False)
            self.recovery_evidence_edit.setVisible(False)
            self.recovery_evidence_button.setVisible(False)
            self.recovery_evidence_view_button.setVisible(False)
            self.recovery_evidence_edit.clear()

            # Reset LC Minutes placeholder
            self.minutes_edit.setPlaceholderText("")

    def update_list_status_grid(self, list_name, status):
        """Update the List Status Information grid for a specific list"""
        try:
            if hasattr(self, 'list_status_grid_widget'):
                grid_layout = self.list_status_grid_widget.layout()
                if isinstance(grid_layout, QGridLayout):
                    # The headers are in row 0, status values in row 1
                    headers = ["Checklist", "Lead Schedule", "Recovered", "Write-Off Recommended", "Written Off", "Deleted Cases"]

                    # Find the column index for the list_name
                    if list_name in headers:
                        col_index = headers.index(list_name)

                        # Get the status label at row 1, col_index
                        status_item = grid_layout.itemAtPosition(1, col_index)
                        if status_item and status_item.widget():
                            status_label = status_item.widget()
                            if isinstance(status_label, QLabel):
                                status_label.setText(status)
        except Exception as e:
            print(f"Warning: Error updating list status grid: {e}")

    def browse_recovery_evidence(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Recovery Evidence", "", "PDF Files (*.pdf)")
        if file_path:
            self.recovery_evidence_edit.setText(file_path)

    def view_recovery_evidence(self):
        """Open the recovery evidence file with the default application"""
        file_path = self.recovery_evidence_edit.text().strip()
        if file_path and os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")
        else:
            QMessageBox.warning(self, "File Not Found", "The recovery evidence file could not be found.")



    def select_bas_payment_date(self):
        """Open calendar dialog for BAS Payment Date selection"""
        from PyQt5.QtWidgets import QCalendarWidget, QDialog, QVBoxLayout, QHBoxLayout, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Select BAS Payment Date")
        dialog.setFixedSize(300, 250)

        layout = QVBoxLayout(dialog)

        calendar = QCalendarWidget()
        current_text = self.bas_payment_date_edit.text().strip()
        if current_text:
            try:
                calendar.setSelectedDate(QDate.fromString(current_text, "yyyy-MM-dd"))
            except:
                calendar.setSelectedDate(QDate.currentDate())
        else:
            calendar.setSelectedDate(QDate.currentDate())

        layout.addWidget(calendar)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        def on_ok():
            selected_date = calendar.selectedDate()
            self.bas_payment_date_edit.setText(selected_date.toString("yyyy-MM-dd"))
            dialog.accept()

        def on_cancel():
            dialog.reject()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.exec_()

    def select_bas_journal_date(self):
        """Open calendar dialog for BAS Journal Date selection"""
        from PyQt5.QtWidgets import QCalendarWidget, QDialog, QVBoxLayout, QHBoxLayout, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Select BAS Journal Date")
        dialog.setFixedSize(300, 250)

        layout = QVBoxLayout(dialog)

        calendar = QCalendarWidget()
        current_text = self.bas_journal_date_edit.text().strip()
        if current_text:
            try:
                calendar.setSelectedDate(QDate.fromString(current_text, "yyyy-MM-dd"))
            except:
                calendar.setSelectedDate(QDate.currentDate())
        else:
            calendar.setSelectedDate(QDate.currentDate())

        layout.addWidget(calendar)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        def on_ok():
            selected_date = calendar.selectedDate()
            self.bas_journal_date_edit.setText(selected_date.toString("yyyy-MM-dd"))
            dialog.accept()

        def on_cancel():
            dialog.reject()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.exec_()

    def save_case(self):
        try:
            # Check if case is finalized
            if len(self.case_data) > 37 and self.case_data[37]:  # is_finalized
                QMessageBox.warning(self, "Case Finalized",
                                  "This case has been finalized and cannot be modified.\n\n"
                                  "Finalized cases are read-only for audit purposes.")
                return

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

            # Check compulsory fields based on category settings
            # Only validate BAS/Persal when those fields are visible (i.e., when category requires them)
            missing_fields = []
            # BAS requirement satisfied by either Payment No OR Journal No
            if bas_comp and not (bas_payment_no or bas_journal_no):
                missing_fields.append("BAS Payment No or BAS Journal No")
            if persal_comp and not persal_no:
                missing_fields.append("Persal No")
            if not amount_text:
                missing_fields.append("Amount")

            # Only show validation errors for BAS/Persal if the fields are actually visible
            # This prevents blocking saves when user is only uploading assessment evidence
            bas_validation_errors = []
            if bas_comp and not (bas_payment_no or bas_journal_no):
                bas_validation_errors.append("BAS Payment No or BAS Journal No")
            if persal_comp and not persal_no:
                bas_validation_errors.append("Persal No")

            # If only BAS/Persal validation errors and fields are not visible, don't block the save
            if bas_validation_errors and not any([bas_comp, persal_comp]):
                # User is not editing supporting evidence fields, allow save
                pass
            elif missing_fields:
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

            # Validate Loss Control fields
            loss_control_status = self.loss_control_status_combo.currentText()
            if loss_control_status == "Recovered" and not self.recovery_evidence_edit.text().strip():
                QMessageBox.warning(self, "Recovery Evidence Required",
                                  "Recovery evidence is required when status is 'Recovered'.\n\n"
                                  "Please select a recovery evidence file before saving.")
                return

            # Validate LC Minutes for Recovered or Write Off Recommended
            if loss_control_status in ["Recovered", "Write Off Recommended"] and not self.minutes_edit.text().strip():
                QMessageBox.warning(self, "Loss Control Minutes Required",
                                  f"Loss Control Minutes are required when status is '{loss_control_status}'.\n\n"
                                  "Please select a Loss Control Minutes file before saving.")
                return

            # Validate Assessment Evidence for Valid/Confirmed statuses
            selected_list = self.list_combo.currentText()
            selected_status = self.status_combo.currentText()
            if ((selected_list in ["Checklist", "Lead Schedule"]) and
                selected_status in ["Valid", "Confirmed"] and
                not self.evidence_edit.text().strip()):
                QMessageBox.warning(self, "Assessment Evidence Required",
                                  f"Assessment Evidence is compulsory when status is '{selected_status}'.\n\n"
                                  "Please select an assessment evidence file before saving.")
                return

            # Convert dates to strings, handling NULL dates
            date_incurred_str = self.date_incurred_edit.date().toString("yyyy-MM-dd")
            date_identified_str = self.date_identified_edit.date().toString("yyyy-MM-dd")
            date_reported_str = self.date_reported_edit.date().toString("yyyy-MM-dd")

            # Handle BAS dates - use NULL if text field is empty
            bas_payment_date_text = self.bas_payment_date_edit.text().strip()
            bas_payment_date_str = bas_payment_date_text if bas_payment_date_text else None

            bas_journal_date_text = self.bas_journal_date_edit.text().strip()
            bas_journal_date_str = bas_journal_date_text if bas_journal_date_text else None

            # Create case dictionary
            category_text = self.category_combo.currentText()
            status_text = self.status_combo.currentText()
            list_text = self.list_combo.currentText()
            criminal_charges_text = self.criminal_charges_combo.currentText()
            disciplinary_text = self.disciplinary_combo.currentText()
            loss_recovery_text = self.loss_recovery_combo.currentText()

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

            case = {
                "transaction_no": self.transaction_no,
                "date_incurred": str(date_incurred_str),
                "date_identified": str(date_identified_str),
                "date_reported": str(date_reported_str),
                "description": self.description_edit.toPlainText().strip(),
                "bas_payment_no": bas_payment_no,
                "bas_payment_date": bas_payment_date_str,
                "bas_journal_no": self.bas_journal_no_edit.text().strip(),
                "bas_journal_date": bas_journal_date_str,
                "persal_no": persal_no,
                "category": category_text,
                "responsibility_id": self.selected_responsibility_id,
                "amount": amount,
                "source_document": self.source_doc_edit.text().strip(),
                "supporting_evidence_path": self.supporting_evidence_edit.text().strip(),
                "minutes": self.minutes_edit.text().strip(),
                "evidence_path": self.evidence_edit.text().strip(),
                "attachments": "[]",
                "status": status_text,
                "list": list_text,
                "assessment_assessed_by": "",
                "assessment_date": "",
                "assessment_result": "",
                "loss_control_recommendation": self.loss_control_status_combo.currentText(),
                "recovery_evidence_path": self.recovery_evidence_edit.text().strip(),
                "criminal_charges": criminal_charges_text,
                "disciplinary_process": disciplinary_text,
                "loss_recovery": loss_recovery_text,
                "prevention_steps": self.prevention_steps_edit.toPlainText().strip(),
                "fy_id": existing_fy_id,
                "period_id": existing_period_id,
                "original_list": list_text
            }

            # Handle file operations - create case-specific folder structure
            year_folder = create_year_folder(self.fy)
            supporting_evidence_folder = os.path.join(year_folder, "Supporting Evidence")
            case_folder = os.path.join(supporting_evidence_folder, f"Case {self.transaction_no}")
            os.makedirs(case_folder, exist_ok=True)

            # Map fields to proper file names
            file_mappings = {
                "source_document": f"{self.transaction_no} Source Document.pdf",
                "supporting_evidence_path": f"{self.transaction_no} Supporting Evidence.pdf",
                "minutes": f"{self.transaction_no} Loss Control Minutes.pdf",
                "evidence_path": f"{self.transaction_no} Assessment Evidence.pdf",
                "recovery_evidence_path": f"{self.transaction_no} Recovery Evidence.pdf"
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
                        except Exception as e:
                            QMessageBox.warning(self, "File Save Error",
                                              f"Failed to save {field} file: {str(e)}")
                            return
                    else:
                        QMessageBox.warning(self, "File Not Found",
                                          f"The selected {field} file could not be found: {source_path}")
                        return

            # Save to database
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE cases SET
                        date_incurred = ?, date_identified = ?, date_reported = ?, description = ?,
                        bas_payment_no = ?, bas_payment_date = ?, bas_journal_no = ?, bas_journal_date = ?, persal_no = ?, category = ?, responsibility_id = ?, amount = ?,
                        source_document = ?, supporting_evidence_path = ?, minutes = ?, evidence_path = ?, attachments = ?, status = ?, list = ?, assessment_assessed_by = ?,
                        assessment_date = ?, assessment_result = ?, loss_control_recommendation = ?, recovery_evidence_path = ?, fy_id = ?, period_id = ?, criminal_charges = ?, disciplinary_process = ?,
                        loss_recovery = ?, prevention_steps = ?, original_list = ?
                    WHERE transaction_no = ?
                """, (
                    case["date_incurred"], case["date_identified"], case["date_reported"],
                    case["description"], case["bas_payment_no"], case["bas_payment_date"], case["bas_journal_no"], case["bas_journal_date"], case["persal_no"],
                    case["category"], case["responsibility_id"], case["amount"], case["source_document"], case["supporting_evidence_path"],
                    case["minutes"], case["evidence_path"], case["attachments"], case["status"], case["list"],
                    case["assessment_assessed_by"], case["assessment_date"], case["assessment_result"], case["loss_control_recommendation"], case["recovery_evidence_path"],
                    case["fy_id"], case["period_id"],
                    case["criminal_charges"], case["disciplinary_process"], case["loss_recovery"],
                    case["prevention_steps"], case["original_list"],
                    case["transaction_no"]
                ))

                conn.commit()
                case_id = self.case_data[0]
                conn.close()

                # Handle workflow transitions based on status change
                old_status = self.case_data[15] if len(self.case_data) > 15 else None  # Assessment status
                if old_status != status_text:
                    try:
                        handle_case_status_change(case_id, self.transaction_no, status_text, list_text)
                    except Exception as workflow_error:
                        QMessageBox.warning(self, "Workflow Error", f"Case saved but workflow transition failed: {str(workflow_error)}")

                # Handle Loss Control status changes
                old_loss_control_status = self.case_data[40] if len(self.case_data) > 40 else None  # Loss Control status at index 40
                new_loss_control_status = self.loss_control_status_combo.currentText()
                if old_loss_control_status != new_loss_control_status and new_loss_control_status in ["Recovered", "Write Off Recommended"]:
                    try:
                        from scripts.Utilities.workflow_utils import handle_loss_control_status_change
                        success = handle_loss_control_status_change(case_id, self.transaction_no, new_loss_control_status)
                        if not success:
                            QMessageBox.warning(self, "Workflow Error", f"Failed to process Loss Control status change to {new_loss_control_status}.")
                    except Exception as workflow_error:
                        QMessageBox.warning(self, "Workflow Error", f"Case saved but Loss Control workflow failed: {str(workflow_error)}")

                try:
                    save_audit_log("edit_case", {
                        "timestamp": datetime.now().isoformat(),
                        "case_id": case_id,
                        "transaction_no": self.transaction_no,
                        "details": case
                    }, self.fy)
                except Exception as audit_error:
                    print(f"Warning: Failed to save audit log: {audit_error}")

                QMessageBox.information(self, "Success", "Case updated successfully.")

                # Try a different approach - don't call accept() immediately
                # Instead, schedule the dialog to close after a short delay
                from PyQt5.QtCore import QTimer

                def delayed_close():
                    try:
                        self.accept()
                    except Exception as delayed_error:
                        try:
                            self.done(1)  # Alternative to accept()
                        except Exception as done_error:
                            pass  # Silent failure for dialog closing

                # Schedule the close to happen after current event processing
                QTimer.singleShot(100, delayed_close)

            except Exception as e:
                print(f"DEBUG: Error during database operations: {e}")
                QMessageBox.critical(self, "Database Error", f"Failed to save case to database: {str(e)}")
                return

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

            # Show determination button for Lead Schedule cases with Confirmed status
            # that haven't been through determination yet
            show_determination = ("-LS" in self.transaction_no and
                                selected_status == "Confirmed")

            if hasattr(self, 'determination_button'):
                self.determination_button.setVisible(show_determination)

        except Exception as e:
            print(f"Warning: Error updating determination button visibility: {e}")
            if hasattr(self, 'determination_button'):
                self.determination_button.setVisible(False)

    def get_case_statuses_across_lists(self, transaction_no):
        """
        Get status information for a case across all lists it appears in

        Args:
            transaction_no: The transaction number of the case

        Returns:
            dict: Mapping of list names to their statuses
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Query for all related cases (original, -LS, -WOR variants)
            cursor.execute("""
                SELECT list, status
                FROM cases
                WHERE (transaction_no = ? OR transaction_no = ? || '-LS' OR transaction_no = ? || '-WOR')
                AND is_finalized = 0
                ORDER BY
                    CASE
                        WHEN list = 'Checklist' THEN 1
                        WHEN list = 'Lead Schedule' THEN 2
                        WHEN list = 'Recovered' THEN 3
                        WHEN list = 'Write-Off Recommended' THEN 4
                        WHEN list = 'Written Off' THEN 5
                        WHEN list = 'Deleted Cases' THEN 6
                        ELSE 7
                    END
            """, (transaction_no, transaction_no, transaction_no))

            results = cursor.fetchall()
            conn.close()

            # Build dictionary of list -> status
            list_statuses = {}
            for list_name, status in results:
                list_statuses[list_name] = status

            return list_statuses

        except Exception as e:
            print(f"Error getting case statuses across lists: {e}")
            return {}

    def is_valid_status_transition(self, current_list, current_status, new_status):
        """Validate if a status transition is allowed based on workflow rules"""
        return self.business_logic.is_valid_status_transition(current_list, current_status, new_status)