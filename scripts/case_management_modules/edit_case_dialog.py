import json
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
from PyQt5.QtCore import QDate, Qt, QTimer, pyqtSignal
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
from scripts.Utilities.workflow_utils import handle_case_status_change, handle_loss_control_status_change, get_case_workflow_status, get_display_transaction_no
from scripts.ui.components.custom_widgets import NoWheelComboBox
from .case_business_logic import CaseBusinessLogic
from collections import defaultdict
from .responsibility_selection import ResponsibilitySelectionDialog
from .determination_dialog import DeterminationDialog




class EditCaseDialog(QDialog):
    # Signal emitted when case data is modified and parent should refresh
    case_modified = pyqtSignal()

    def __init__(self, case_data, parent=None, selected_list=None):
        print(f"DEBUG: EditCaseDialog.__init__ called with case_data type: {type(case_data)}")
        if hasattr(case_data, '__len__'):
            print(f"DEBUG: case_data length: {len(case_data)}")
            print(f"DEBUG: case_data first 5 elements: {case_data[:5] if len(case_data) > 5 else case_data}")

        super().__init__(parent)
        # Set title with list context for better user understanding
        self.list_name = selected_list or "Checklist"
        self.setWindowTitle(f"Edit Case Details - {self.list_name}")
        self.setFixedSize(1200, 900)
        try:
            print("DEBUG: Loading responsibilities, categories, and lists")
            self.responsibilities = load_posting_responsibilities()
            self.categories = load_categories()
            self.lists = load_lists()
            self.fy = get_financial_year()
            self.case_data = case_data
            self.selected_list = selected_list  # From parent dialog's filter
            self.supporting_evidence_compulsory = False
            self.business_logic = CaseBusinessLogic(self.fy)

            # Performance optimization: debounce update_conditional_fields calls
            self.update_timer = QTimer()
            self.update_timer.setSingleShot(True)
            self.update_timer.timeout.connect(self.update_conditional_fields)

            # Extract key fields from new schema
            self.case_id = case_data[0]
            print(f"DEBUG: case_id = {self.case_id}")
            # Handle both tuple (from SELECT *) and dict formats
            if isinstance(case_data, dict):
                self.base_transaction_no = case_data.get('base_transaction_no') or str(case_data.get('transaction_no', '')).split('-')[0]
                self.transaction_no = case_data.get('transaction_no', '')
                self.assessment_status = case_data.get('assessment_status', 'Alleged')
                self.lc_status = case_data.get('lc_status')
                self.suffixes = case_data.get('suffixes', '')
                self.is_finalized = case_data.get('is_finalized', False)
            else:
                # Tuple format from SELECT * - use correct column indices based on actual database schema
                self.transaction_no = case_data[1] if len(case_data) > 1 else ''  # transaction_no
                self.base_transaction_no = case_data[41] if len(case_data) > 41 and case_data[41] else str(case_data[1]).split('-')[0]  # base_transaction_no
                self.assessment_status = case_data[42] if len(case_data) > 42 and case_data[42] else 'Alleged'  # assessment_status
                self.lc_status = case_data[43] if len(case_data) > 43 and case_data[43] else None  # lc_status
                self.suffixes = case_data[44] if len(case_data) > 44 and case_data[44] else ''  # suffixes
                self.is_finalized = case_data[37] if len(case_data) > 37 and case_data[37] else False  # is_finalized

            print(f"DEBUG: Extracted fields - base_transaction_no: {self.base_transaction_no}, assessment_status: {self.assessment_status}, lc_status: {self.lc_status}, suffixes: {self.suffixes}")

            # Cache workflow status now that we have the case_id
            try:
                from scripts.Utilities.workflow_utils import get_case_workflow_status
                self.workflow_status_cache = get_case_workflow_status(self.case_id)
                print(f"DEBUG: Workflow status cache loaded: {self.workflow_status_cache is not None}")
            except Exception as e:
                print(f"DEBUG: Failed to load workflow status cache: {e}")
                self.workflow_status_cache = None

            # Validate that required data was loaded
            if not self.responsibilities:
                raise ValueError("No posting responsibilities found in database")
            if not self.categories:
                raise ValueError("No categories found in database")
            if not self.lists:
                raise ValueError("No lists found in database")

            print("DEBUG: Calling setup_ui()")
            self.setup_ui()
            print("DEBUG: Calling load_case_data()")
            self.load_case_data()
            print("DEBUG: EditCaseDialog.__init__ completed successfully")
        except Exception as e:
            print(f"DEBUG: Exception in EditCaseDialog.__init__: {e}")
            import traceback
            traceback.print_exc()
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

        # Case Number (read-only) - show base number + current suffixes
        display_transaction_no = get_display_transaction_no(self.base_transaction_no, self.suffixes)
        self.trans_no_edit = QLineEdit(display_transaction_no)
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

        # Get workflow status for this single case (using cached result)
        workflow_status = self.workflow_status_cache

        # Determine visibility for each list based on case status and suffixes
        list_statuses = []
        for header in headers:
            if workflow_status and header in workflow_status.get('appears_in_lists', []):
                if header == "Checklist":
                    list_statuses.append(self.assessment_status)
                elif header == "Lead Schedule":
                    list_statuses.append(self.lc_status or "Awaiting LC determination")
                elif header == "Recovered":
                    list_statuses.append("Recovered")
                elif header == "Write-Off Recommended":
                    list_statuses.append("Write Off Recommended")
                elif header == "Written Off":
                    list_statuses.append("Written Off")
                else:
                    list_statuses.append("Active")
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

        # ===== WORKFLOW DIAGRAM GROUP =====
        workflow_group = QGroupBox("Case Workflow Diagram")
        workflow_layout = QVBoxLayout(workflow_group)

        # Create workflow diagram as a text label
        workflow_text = QLabel()
        workflow_text.setText("""
<b>F&W Case Workflow:</b><br><br>

<pre style="font-family: 'Courier New', monospace; font-size: 11px; line-height: 1.3;">
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   Alleged   │────▶│ Under Assessment │────▶│    Valid    │
│             │     │                 │     │ (Finalized) │
└─────────────┘     └─────────────────┘     └─────────────┘
       │                       │
       ▼                       ▼
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│  Confirmed  │────▶│  Lead Schedule  │────▶│LC Determination│
│             │     │                 │     │               │
└─────────────┘     └─────────────────┘     └─────────────┘
                                                       │
                    ┌─────────────────┐                │
                    │   Recovered     │◀───────────────┘
                    │  (Finalized)    │
                    └─────────────────┘
                               │
                    ┌─────────────────┐
                    │Write Off Rec'd │
                    └─────────────────┘
                               │
                    ┌─────────────────┐     ┌─────────────┐
                    │Write-Off Submit│────▶│ Written Off │
                    │                │     │ (Finalized) │
                    └─────────────────┘     └─────────────┘
</pre><br>

<b>Requirements:</b><br>
• <b>Assessment Evidence:</b> Required for Valid/Confirmed status<br>
• <b>LC Evidence:</b> Required for Recovered/Write-Off Recommended<br>
• <b>Finalized cases:</b> Read-only for audit purposes<br>
• <b>List visibility:</b> Controlled by suffixes (-LS, -REC, -WOR, -WO)
        """)
        workflow_text.setWordWrap(True)
        workflow_text.setStyleSheet("""
            QLabel {
                font-family: monospace;
                font-size: 10px;
                line-height: 1.4;
                padding: 10px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        workflow_layout.addWidget(workflow_text)
        self.main_layout.addWidget(workflow_group)

        # ===== ASSESSMENT GROUP =====
        assessment_group = QGroupBox("Assessment")
        assessment_layout = QFormLayout(assessment_group)

        # Assessment Status
        self.assessment_status_combo = NoWheelComboBox()
        self.assessment_status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed"])
        self.assessment_status_combo.setCurrentText(self.assessment_status)
        assessment_layout.addRow("Assessment Status:", self.assessment_status_combo)

        # Loss Control Status (only shown for Confirmed cases)
        self.lc_status_combo = NoWheelComboBox()
        self.lc_status_combo.addItems(["Awaiting LC determination", "Recovered", "Write Off Recommended"])
        if self.lc_status:
            self.lc_status_combo.setCurrentText(self.lc_status)
        assessment_layout.addRow("Loss Control Status:", self.lc_status_combo)

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
        self.category_combo.currentIndexChanged.connect(self.schedule_update_conditional_fields)
        self.assessment_status_combo.currentTextChanged.connect(self.on_assessment_status_changed)
        self.lc_status_combo.currentTextChanged.connect(self.on_lc_status_changed)

        # Update determination button visibility
        self.update_determination_button_visibility()

    def load_case_data(self):
        """Load existing case data into the form fields"""
        # Temporarily disconnect signals to prevent triggering during loading
        try:
            self.category_combo.currentIndexChanged.disconnect(self.update_conditional_fields)
        except TypeError:
            pass  # Signal was not connected
        try:
            self.assessment_status_combo.currentTextChanged.disconnect(self.on_assessment_status_changed)
        except TypeError:
            pass  # Signal was not connected

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

        # Set assessment status
        if hasattr(self, 'assessment_status_combo') and len(self.case_data) > 42 and self.case_data[42]:
            self.assessment_status_combo.setCurrentText(str(self.case_data[42]))

        # Set LC status
        if hasattr(self, 'lc_status_combo') and len(self.case_data) > 43 and self.case_data[43]:
            self.lc_status_combo.setCurrentText(str(self.case_data[43]))

        # Update conditional fields again to show/hide fields based on the loaded status
        self.update_conditional_fields()

        # Reconnect signals
        self.category_combo.currentIndexChanged.connect(self.schedule_update_conditional_fields)
        self.assessment_status_combo.currentTextChanged.connect(self.on_assessment_status_changed)

        # Check if case is finalized and disable editing if so
        if self.is_finalized:
            self.setWindowTitle(f"Edit Case Details - {self.list_name} (FINALIZED)")
            # Disable all input fields for finalized cases
            self.description_edit.setReadOnly(True)
            self.amount_edit.setReadOnly(True)
            self.date_incurred_edit.setReadOnly(True)
            self.date_identified_edit.setReadOnly(True)
            self.date_reported_edit.setReadOnly(True)
            self.assessment_status_combo.setEnabled(False)
            self.lc_status_combo.setEnabled(False)
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
            self.recovery_evidence_edit.setReadOnly(True)
            self.recovery_evidence_button.setEnabled(False)
            self.criminal_charges_combo.setEnabled(False)
            self.disciplinary_combo.setEnabled(False)
            self.loss_recovery_combo.setEnabled(False)
            self.prevention_steps_edit.setReadOnly(True)

            # Disable save button for finalized cases
            self.save_button.setEnabled(False)
            self.save_button.setText("Case Finalized - No Changes Allowed")

            # Add finalization notice
            finalization_reason = 'Case has been finalized'  # Default reason since we don't have this field in the current schema
            finalization_label = QLabel(f"📋 Finalized: {finalization_reason}")
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

        # Set Loss Control fields - use status from loss_control_recommendation field (index 38)
        if len(self.case_data) > 38 and self.case_data[38]:  # loss_control_recommendation at index 38
            self.loss_control_status_combo.setCurrentText(str(self.case_data[38]))
            # Update recovery evidence visibility, LC Minutes placeholder, and list status grid based on status

            # First, reset all statuses to N/A
            self.update_list_status_grid("Recovered", "N/A")
            self.update_list_status_grid("Write-Off Recommended", "N/A")

            status = str(self.case_data[38])
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

        if len(self.case_data) > 39 and self.case_data[39] and os.path.exists(self.case_data[39]):  # recovery_evidence_path at index 39
            self.recovery_evidence_edit.setText(self.case_data[39])
        elif len(self.case_data) > 39 and self.case_data[39]:
            print(f"Warning: Recovery evidence file not found: {self.case_data[39]}")
            self.recovery_evidence_edit.clear()


    def select_responsibility(self):
        dialog = ResponsibilitySelectionDialog(self)
        if dialog.exec_():
            selected = dialog.get_selected_responsibility()
            if selected:
                self.responsibility_edit.setText(selected["name"])
                self.selected_responsibility_id = selected["id"]

    def on_assessment_status_changed(self, new_status):
        """Handle assessment status change"""
        if new_status == "Valid":
            # Check if evidence is uploaded before allowing status change
            evidence_path = self.evidence_edit.text().strip()
            if not evidence_path:
                QMessageBox.critical(self, "Evidence Required",
                                   "Assessment evidence must be uploaded before marking case as Valid.\n\n"
                                   "Please select an assessment evidence file first.")
                self.assessment_status_combo.setCurrentText(self.assessment_status)
                return

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
                # Apply the status change
                if not handle_case_status_change(self.case_id, self.base_transaction_no, new_status):
                    QMessageBox.critical(self, "Error", "Failed to update assessment status")
                    self.assessment_status_combo.setCurrentText(self.assessment_status)
                    return
                self.assessment_status = new_status
            else:
                # Revert to previous status
                self.assessment_status_combo.setCurrentText(self.assessment_status)
                self.supporting_evidence_compulsory = False
                return

        elif new_status == "Confirmed":
            # Check if evidence is uploaded before allowing status change
            evidence_path = self.evidence_edit.text().strip()
            if not evidence_path:
                QMessageBox.critical(self, "Evidence Required",
                                   "Assessment evidence must be uploaded before marking case as Confirmed.\n\n"
                                   "Please select an assessment evidence file first.")
                self.assessment_status_combo.setCurrentText(self.assessment_status)
                return

            # Show warning dialog for Confirmed status
            reply = QMessageBox.question(
                self,
                "Confirm Confirmed Status",
                "Selecting 'Confirmed' means this case IS Fruitless and Wasteful Expenditure.\n\n"
                "The case will appear in the Lead Schedule for Loss Control Committee review.\n\n"
                "Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Apply the status change
                if not handle_case_status_change(self.case_id, self.base_transaction_no, new_status):
                    QMessageBox.critical(self, "Error", "Failed to update assessment status")
                    self.assessment_status_combo.setCurrentText(self.assessment_status)
                    return
                self.assessment_status = new_status
                self.case_modified.emit()  # Signal parent to refresh
                self.supporting_evidence_compulsory = True
            else:
                # Revert to previous status
                self.assessment_status_combo.setCurrentText(self.assessment_status)
                return

        else:
            # Apply the status change for other statuses
            if not handle_case_status_change(self.case_id, self.base_transaction_no, new_status):
                QMessageBox.critical(self, "Error", "Failed to update assessment status")
                self.assessment_status_combo.setCurrentText(self.assessment_status)
                return
            self.assessment_status = new_status
            self.supporting_evidence_compulsory = False
            self.case_modified.emit()  # Signal parent to refresh

        # Update conditional fields
        self.update_conditional_fields()

    def on_lc_status_changed(self, new_lc_status):
        """Handle Loss Control status change"""
        # Check if evidence is uploaded before allowing LC status change
        evidence_path = self.evidence_edit.text().strip()
        if not evidence_path:
            QMessageBox.critical(self, "Evidence Required",
                               "Assessment evidence must be uploaded before changing Loss Control status.\n\n"
                               "Please select an assessment evidence file first.")
            # Revert to previous status
            if self.lc_status:
                self.lc_status_combo.setCurrentText(self.lc_status)
            return

        if not handle_loss_control_status_change(self.case_id, self.base_transaction_no, new_lc_status):
            QMessageBox.critical(self, "Error", "Failed to update Loss Control status")
            # Revert to previous status
            if self.lc_status:
                self.lc_status_combo.setCurrentText(self.lc_status)
            return

        self.lc_status = new_lc_status
        self.update_conditional_fields()
        self.case_modified.emit()  # Signal parent to refresh

    def schedule_update_conditional_fields(self):
        """Schedule a debounced update of conditional fields to prevent excessive calls"""
        self.update_timer.start(150)  # 150ms debounce delay

    def update_conditional_fields(self):
        """Update visibility of conditional fields based on assessment status"""
        try:
            # Get current selections safely
            selected_assessment_status = self.assessment_status_combo.currentText() if self.assessment_status_combo.count() > 0 else ""
            selected_category = self.category_combo.currentText() if self.category_combo.count() > 0 else ""

            # Show/hide LC status combo based on assessment status
            if hasattr(self, 'lc_status_combo'):
                show_lc_status = selected_assessment_status == "Confirmed"
                self.lc_status_combo.setVisible(show_lc_status)
                # Also find and hide/show the label
                for i in range(self.main_layout.count()):
                    item = self.main_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if hasattr(widget, 'layout') and widget.layout():
                            # Check if this is the assessment group
                            if isinstance(widget, QGroupBox) and "Assessment" in widget.title():
                                # Find the LC status row in the form layout
                                form_layout = widget.layout()
                                if isinstance(form_layout, QFormLayout):
                                    for row in range(form_layout.rowCount()):
                                        label_item = form_layout.itemAt(row, QFormLayout.LabelRole)
                                        if label_item and label_item.widget():
                                            label = label_item.widget()
                                            if isinstance(label, QLabel) and "Loss Control" in label.text():
                                                # This is the LC status row
                                                label.setVisible(show_lc_status)
                                                break

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
                              selected_assessment_status in ["Valid", "Confirmed"])

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
            selected_assessment_status = self.assessment_status_combo.currentText()
            if selected_assessment_status in ["Valid", "Confirmed"] and not self.evidence_edit.text().strip():
                QMessageBox.warning(self, "Assessment Evidence Required",
                                  f"Assessment Evidence is compulsory when assessment status is '{selected_assessment_status}'.\n\n"
                                  "Please select an assessment evidence file before saving.")
                return

            # Validate LC evidence for LC statuses
            selected_lc_status = self.lc_status_combo.currentText()
            if selected_lc_status in ["Recovered", "Write Off Recommended"]:
                if selected_lc_status == "Recovered" and not self.recovery_evidence_edit.text().strip():
                    QMessageBox.warning(self, "Recovery Evidence Required",
                                      "Recovery evidence is required when Loss Control status is 'Recovered'.")
                    return
                if not self.minutes_edit.text().strip():
                    QMessageBox.warning(self, "Loss Control Minutes Required",
                                      f"Loss Control Minutes are required when status is '{selected_lc_status}'.")
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
            assessment_status_text = self.assessment_status_combo.currentText()
            lc_status_text = self.lc_status_combo.currentText() if self.lc_status_combo.isVisible() else None
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
                    print(f"DEBUG: Fixed NULL fy_id for case {self.base_transaction_no}, set to {existing_fy_id}")
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
                "base_transaction_no": self.base_transaction_no,
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
                "recovery_evidence_path": self.recovery_evidence_edit.text().strip(),
                "criminal_charges": criminal_charges_text,
                "disciplinary_process": disciplinary_text,
                "loss_recovery": loss_recovery_text,
                "prevention_steps": self.prevention_steps_edit.toPlainText().strip(),
                "fy_id": existing_fy_id,
                "period_id": existing_period_id
            }

            # Handle file operations - create case-specific folder structure
            year_folder = create_year_folder(self.fy)
            supporting_evidence_folder = os.path.join(year_folder, "Supporting Evidence")
            case_folder = os.path.join(supporting_evidence_folder, f"Case {self.base_transaction_no}")
            os.makedirs(case_folder, exist_ok=True)

            # Map fields to proper file names
            file_mappings = {
                "source_document": f"{self.base_transaction_no} Source Document.pdf",
                "supporting_evidence_path": f"{self.base_transaction_no} Supporting Evidence.pdf",
                "minutes": f"{self.base_transaction_no} Loss Control Minutes.pdf",
                "evidence_path": f"{self.base_transaction_no} Assessment Evidence.pdf",
                "recovery_evidence_path": f"{self.base_transaction_no} Recovery Evidence.pdf"
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
                            dest_dir = os.path.dirname(dest_path)
                            try:
                                os.makedirs(dest_dir, exist_ok=True)
                            except PermissionError:
                                QMessageBox.critical(self, "Permission Error",
                                                   f"Cannot create directory for {field} file.\n\n"
                                                   f"Directory: {dest_dir}\n\n"
                                                   "Please check folder permissions and try again.")
                                return
                            except Exception as dir_error:
                                QMessageBox.critical(self, "Directory Error",
                                                   f"Failed to create directory for {field} file.\n\n"
                                                   f"Directory: {dest_dir}\n\n"
                                                   f"Error: {str(dir_error)}")
                                return

                            # Check if destination file already exists and is read-only
                            if os.path.exists(dest_path):
                                try:
                                    # Test if we can write to the file
                                    with open(dest_path, 'ab') as test_file:
                                        pass
                                except PermissionError:
                                    QMessageBox.critical(self, "File Permission Error",
                                                       f"Cannot overwrite existing {field} file.\n\n"
                                                       f"File: {dest_path}\n\n"
                                                       "The file may be read-only or in use by another program.")
                                    return

                            # Try to copy the file (safer than move)
                            import shutil
                            try:
                                shutil.copy2(source_path, dest_path)
                                case[field] = dest_path
                            except PermissionError:
                                QMessageBox.critical(self, "File Copy Permission Error",
                                                   f"Cannot copy {field} file due to permission restrictions.\n\n"
                                                   f"Source: {source_path}\n"
                                                   f"Destination: {dest_path}\n\n"
                                                   "Please check file permissions and ensure the source file is not in use.")
                                return
                            except OSError as os_error:
                                QMessageBox.critical(self, "File System Error",
                                                   f"Failed to copy {field} file due to file system error.\n\n"
                                                   f"Source: {source_path}\n"
                                                   f"Destination: {dest_path}\n\n"
                                                   f"Error: {str(os_error)}")
                                return
                            except Exception as copy_error:
                                QMessageBox.critical(self, "File Copy Error",
                                                   f"Unexpected error while copying {field} file.\n\n"
                                                   f"Source: {source_path}\n"
                                                   f"Destination: {dest_path}\n\n"
                                                   f"Error: {str(copy_error)}")
                                return

                        except Exception as e:
                            QMessageBox.critical(self, "File Processing Error",
                                               f"Failed to process {field} file.\n\n"
                                               f"Error: {str(e)}")
                            return
                    else:
                        QMessageBox.warning(self, "File Not Found",
                                          f"The selected {field} file could not be found: {source_path}")
                        return

            # Save to database
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Build evidence paths JSON
                evidence_paths = {}
                if case["evidence_path"]:
                    evidence_paths["assessment"] = case["evidence_path"]
                if case["recovery_evidence_path"]:
                    evidence_paths["recovery"] = case["recovery_evidence_path"]
                if case["minutes"]:
                    evidence_paths["lc_minutes"] = case["minutes"]
                if case["supporting_evidence_path"]:
                    evidence_paths["supporting"] = case["supporting_evidence_path"]
                if case["source_document"]:
                    evidence_paths["source"] = case["source_document"]

                evidence_paths_json = json.dumps(evidence_paths) if evidence_paths else None

                cursor.execute("""
                    UPDATE cases SET
                        date_incurred = ?, date_identified = ?, date_reported = ?, description = ?,
                        bas_payment_no = ?, bas_payment_date = ?, bas_journal_no = ?, bas_journal_date = ?, persal_no = ?, category = ?, responsibility_id = ?, amount = ?,
                        evidence_paths = ?, assessment_status = ?, lc_status = ?, criminal_charges = ?, disciplinary_process = ?,
                        loss_recovery = ?, prevention_steps = ?
                    WHERE id = ?
                """, (
                    case["date_incurred"], case["date_identified"], case["date_reported"],
                    case["description"], case["bas_payment_no"], case["bas_payment_date"], case["bas_journal_no"], case["bas_journal_date"], case["persal_no"],
                    case["category"], case["responsibility_id"], case["amount"],
                    evidence_paths_json, assessment_status_text, lc_status_text,
                    case["criminal_charges"], case["disciplinary_process"], case["loss_recovery"],
                    case["prevention_steps"],
                    self.case_id
                ))

                conn.commit()
                case_id = self.case_data[0]
                conn.close()

                # Workflow transitions are now handled in the status change handlers
                # No additional workflow processing needed here

                try:
                    save_audit_log("edit_case", {
                        "timestamp": datetime.now().isoformat(),
                        "case_id": case_id,
                        "base_transaction_no": self.base_transaction_no,
                        "details": case
                    }, self.fy)
                except Exception as audit_error:
                    print(f"Warning: Failed to save audit log: {audit_error}")

                QMessageBox.information(self, "Success", "Case updated successfully.")

                # Signal parent that case was modified
                self.case_modified.emit()

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
        display_no = get_display_transaction_no(self.base_transaction_no, self.suffixes)
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete case {display_no}?\n\n"
            "This will move the case to the Deleted Cases list.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Update case to add -DEL suffix and mark as deleted
                new_suffixes = self.suffixes
                if new_suffixes:
                    new_suffixes += ",-DEL"
                else:
                    new_suffixes = "-DEL"

                cursor.execute("""
                    UPDATE cases
                    SET suffixes = ?
                    WHERE id = ?
                """, (new_suffixes, self.case_id))

                conn.commit()
                conn.close()

                # Log audit trail
                save_audit_log("delete_case", {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": self.case_id,
                    "base_transaction_no": self.base_transaction_no,
                    "details": "Case marked as deleted with -DEL suffix"
                }, self.fy)

                QMessageBox.information(self, "Success", f"Case {display_no} has been moved to Deleted Cases.")
                self.case_modified.emit()  # Signal parent to refresh
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
            selected_assessment_status = self.assessment_status_combo.currentText()

            # Show determination button for Confirmed cases that appear in Lead Schedule
            # (have -LS suffix) and haven't been through LC determination yet
            show_determination = (selected_assessment_status == "Confirmed" and
                                "-LS" in self.suffixes and
                                (not self.lc_status or self.lc_status == "Awaiting LC determination"))

            if hasattr(self, 'determination_button'):
                self.determination_button.setVisible(show_determination)

        except Exception as e:
            print(f"Warning: Error updating determination button visibility: {e}")
            if hasattr(self, 'determination_button'):
                self.determination_button.setVisible(False)
