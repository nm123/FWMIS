from PyQt5.QtWidgets import (QDialog, QFormLayout, QDoubleSpinBox, QDateEdit, 
                            QDialogButtonBox, QVBoxLayout, QLabel, QMessageBox)
from PyQt5.QtCore import QDate
from scripts.Utilities.db_utils import get_current_delegation, save_delegation

class DelegationManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Write-Off Delegations")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Explanation label
        layout.addWidget(QLabel(
            "Set the CFO's write-off approval limit:\n"
            "- Cases ≤ this amount: CFO approval\n"
            "- Cases > this amount: HOD approval\n\n"
            "Note: HOD has unlimited authority for amounts above the CFO limit."
        ))
        
        # Form layout
        form_layout = QFormLayout()
        
        self.cfo_limit_edit = QDoubleSpinBox()
        self.cfo_limit_edit.setRange(0, 100000000)
        self.cfo_limit_edit.setDecimals(2)
        self.cfo_limit_edit.setPrefix("R ")
        self.cfo_limit_edit.setValue(50000)
        
        self.effective_date_edit = QDateEdit()
        self.effective_date_edit.setCalendarPopup(True)
        self.effective_date_edit.setDate(QDate.currentDate())
        
        form_layout.addRow("CFO Limit:", self.cfo_limit_edit)
        form_layout.addRow("Effective Date:", self.effective_date_edit)
        
        layout.addLayout(form_layout)
        
        # Load current delegation
        self.load_current_delegation()
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_delegation)
        button_box.rejected.connect(self.reject)
        
        # Apply professional styling to buttons
        save_btn = button_box.button(QDialogButtonBox.Save)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a365d;
                color: white;
                border: 1px solid #1a365d;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2c5282;
            }
        """)
        
        cancel_btn = button_box.button(QDialogButtonBox.Cancel)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #f7fafc;
            }
        """)
        
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def load_current_delegation(self):
        delegation = get_current_delegation()
        if delegation:
            self.cfo_limit_edit.setValue(delegation['cfo_limit'])
            self.effective_date_edit.setDate(QDate.fromString(delegation['effective_date'], "yyyy-MM-dd"))
    
    def save_delegation(self):
        cfo_limit = self.cfo_limit_edit.value()
        effective_date = self.effective_date_edit.date().toString("yyyy-MM-dd")
        
        if save_delegation(cfo_limit, effective_date):
            QMessageBox.information(self, "Success", 
                f"Delegation updated successfully!\n"
                f"New CFO limit: R {cfo_limit:,.2f}\n"
                f"Effective: {effective_date}")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", 
                "Failed to save delegation. Please check logs for details.")
