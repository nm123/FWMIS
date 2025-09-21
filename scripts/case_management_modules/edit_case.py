import sqlite3
from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDate
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.responsibility_utils import load_posting_responsibilities, load_responsibilities
from scripts.Utilities.category_utils import load_categories
from scripts.Utilities.list_utils import load_lists
from scripts.Utilities.tree_utils import get_subtree_resp_ids
from scripts.Utilities.utils import format_currency_amount
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.ui_theme import apply_theme
from collections import defaultdict
from .edit_case_ui import setup_edit_ui, NoWheelComboBox
from .edit_case_logic import EditCaseLogic
from .edit_case_handlers import (
    select_responsibility, on_status_changed, update_conditional_fields,
    browse_source_doc, browse_minutes, browse_evidence,
    on_save_clicked, on_cancel_clicked
)


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
            self.transaction_no = case_data[1]
            self.selected_responsibility_id = case_data[10]
            self.case_data = case_data
            self.supporting_evidence_compulsory = False

            # Validate required data
            if not self.responsibilities:
                raise ValueError("No posting responsibilities found in database")
            if not self.categories:
                raise ValueError("No categories found in database")
            if not self.lists:
                raise ValueError("No lists found in database")

            # Setup UI
            setup_edit_ui(self)

            # Create logic instance
            self.logic = EditCaseLogic(self)

            # Load case data
            self.logic.load_case_data()

            # Connect signals
            self.select_responsibility_button.clicked.connect(lambda: select_responsibility(self))
            self.source_doc_button.clicked.connect(lambda: browse_source_doc(self))
            self.minutes_button.clicked.connect(lambda: browse_minutes(self))
            self.evidence_button.clicked.connect(lambda: browse_evidence(self))
            self.save_button.clicked.connect(lambda: on_save_clicked(self))
            self.delete_button.clicked.connect(lambda: self.logic.delete_case())
            self.cancel_button.clicked.connect(lambda: on_cancel_clicked(self))

            self.category_combo.currentIndexChanged.connect(lambda: update_conditional_fields(self))
            self.list_combo.currentTextChanged.connect(lambda: update_conditional_fields(self))
            self.status_combo.currentTextChanged.connect(lambda status: on_status_changed(self, status))

            # Update conditional fields
            update_conditional_fields(self)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize Edit Case dialog: {str(e)}")
            self.reject()

