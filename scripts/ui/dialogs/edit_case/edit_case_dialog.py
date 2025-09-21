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
from scripts.Utilities.case_save_utils import save_case
from scripts.ui.components.custom_widgets import NoWheelComboBox
from scripts.case_management_modules.case_business_logic import CaseBusinessLogic
from collections import defaultdict
from scripts.case_management_modules.responsibility_selection import ResponsibilitySelectionDialog
from scripts.case_management_modules.determination_dialog import DeterminationDialog
from .edit_case_data_init import initialize_case_data
from .edit_case_basic_ui import setup_basic_ui_components
from .edit_case_list_status_ui import setup_list_status_ui_components
from .edit_case_assessment_ui import setup_assessment_ui_components
from .edit_case_loss_control_ui import setup_loss_control_ui_components
from .edit_case_supporting_ui import setup_supporting_ui_components
from .edit_case_attachments_ui import setup_attachments_ui_components
from .edit_case_load_data import load_case_data_components
from .edit_case_handlers import (
    on_assessment_status_changed,
    on_lc_status_changed,
    browse_evidence,
    browse_assessment_evidence,
    browse_recovery_evidence,
    browse_minutes,
    browse_source_doc,
    browse_supporting_evidence,
    view_assessment_evidence,
    view_recovery_evidence,
    view_minutes,
    view_supporting_evidence,
    view_source_doc,
    update_conditional_fields,
    update_list_status_grid,
    select_bas_payment_date,
    select_bas_journal_date
);
from .edit_case_utils import delete_case, open_determination_dialog, update_determination_button_visibility, schedule_update_conditional_fields
from scripts.Utilities.edit_case_status_display_utils import update_list_status_display

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
            initialize_case_data(self, case_data, selected_list)

            # Performance optimization: debounce update_conditional_fields calls
            self.update_timer = QTimer()
            self.update_timer.setSingleShot(True)
            self.update_timer.timeout.connect(self.update_conditional_fields)

            print("DEBUG: Calling setup_ui()")
            self.setup_ui()
            print("DEBUG: Calling load_case_data()")
            load_case_data_components(self)
            print("DEBUG: EditCaseDialog.__init__ completed successfully")
        except Exception as e:
            print(f"DEBUG: Exception in EditCaseDialog.__init__: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to initialize Edit Case dialog: {str(e)}")
            self.reject()
                
    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        # Create scroll area for the form
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.main_layout = QVBoxLayout(self.scroll_widget)
        setup_basic_ui_components(self)
        setup_list_status_ui_components(self)
        setup_assessment_ui_components(self)
        setup_loss_control_ui_components(self)
        setup_supporting_ui_components(self)
        setup_attachments_ui_components(self)

    def select_responsibility(self):
        dialog = ResponsibilitySelectionDialog(self)
        if dialog.exec_():
            selected = dialog.get_selected_responsibility()
            if selected:
                self.responsibility_edit.setText(selected["name"])
                self.selected_responsibility_id = selected["id"]

    def on_assessment_status_changed(self, new_status):
        on_assessment_status_changed(self, new_status)

    def on_lc_status_changed(self, new_lc_status):
        on_lc_status_changed(self, new_lc_status)

    def schedule_update_conditional_fields(self):
        schedule_update_conditional_fields(self)

    def update_conditional_fields(self):
        update_conditional_fields(self)

    def browse_source_doc(self):
        browse_source_doc(self)

    def browse_minutes(self):
        browse_minutes(self)

    def browse_evidence(self):
        browse_evidence(self)

    def browse_assessment_evidence(self):
        browse_assessment_evidence(self)


    def view_assessment_evidence(self):
        view_assessment_evidence(self)

    def view_minutes(self):
        view_minutes(self)


    def view_supporting_evidence(self):
        view_supporting_evidence(self)

    def view_source_doc(self):
        view_source_doc(self)

    def browse_supporting_evidence(self):
        browse_supporting_evidence(self)


    def update_list_status_grid(self, list_name, status):
        update_list_status_grid(self, list_name, status)

    def browse_recovery_evidence(self):
        browse_recovery_evidence(self)

    def view_recovery_evidence(self):
        view_recovery_evidence(self)



    def select_bas_payment_date(self):
        select_bas_payment_date(self)

    def select_bas_journal_date(self):
        select_bas_journal_date(self)

    def delete_case(self):
        delete_case(self)

    def open_determination_dialog(self):
        open_determination_dialog(self)

    def update_determination_button_visibility(self):
        update_determination_button_visibility(self)






