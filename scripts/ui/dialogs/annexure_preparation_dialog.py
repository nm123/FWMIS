from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTableWidget, QTableWidgetItem, QPushButton, 
                            QGroupBox, QCheckBox, QMessageBox, QFileDialog,
                            QHeaderView, QAbstractItemView, QSplitter,
                            QFrame, QScrollArea, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from scripts.Utilities.annexure_utils import (get_write_off_recommended_cases, 
                                             group_cases_by_delegation,
                                             create_annexure,
                                             get_current_financial_year_id,
                                             get_current_delegation)
from scripts.Utilities.excel_exporter import export_annexure_to_excel
from scripts.Utilities.pdf_exporter import export_annexure_to_pdf

class AnnexurePreparationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Prepare Write-Off Annexures")
        self.setMinimumSize(1000, 700)
        
        # Data storage
        self.all_cases = []
        self.cfo_cases = []
        self.hod_cases = []
        self.selected_cfo_cases = []
        self.selected_hod_cases = []
        self.cfo_annexure_id = None
        self.hod_annexure_id = None
        
        self.setup_ui()
        self.load_cases()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("Write-Off Annexure Preparation")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Instructions
        instructions = QLabel(
            "Select cases to include in annexures. Cases are automatically grouped by delegation:\n"
            "- CFO Cases: ≤ current delegation limit\n"
            "- HOD Cases: > current delegation limit"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { color: #666; margin: 10px; }")
        layout.addWidget(instructions)
        
        # Create splitter for two panels
        splitter = QSplitter(Qt.Horizontal)
        
        # CFO Panel
        cfo_group = self.create_delegation_panel("CFO Cases", "cfo")
        splitter.addWidget(cfo_group)
        
        # HOD Panel  
        hod_group = self.create_delegation_panel("HOD Cases", "hod")
        splitter.addWidget(hod_group)
        
        # Set splitter proportions
        splitter.setSizes([500, 500])
        layout.addWidget(splitter)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Annexures")
        self.generate_btn.clicked.connect(self.generate_annexures)
        self.generate_btn.setEnabled(False)
        
        self.export_excel_btn = QPushButton("Export Excel")
        self.export_excel_btn.clicked.connect(self.export_excel)
        self.export_excel_btn.setEnabled(False)
        
        self.export_pdf_btn = QPushButton("Export PDF")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_pdf_btn.setEnabled(False)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.export_excel_btn)
        button_layout.addWidget(self.export_pdf_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def create_delegation_panel(self, title, role):
        """Create a panel for either CFO or HOD cases."""
        group = QGroupBox(title)
        layout = QVBoxLayout()
        
        # Summary info
        summary_label = QLabel()
        summary_label.setStyleSheet("QLabel { font-weight: bold; color: #333; }")
        layout.addWidget(summary_label)
        
        # Select all checkbox
        select_all_cb = QCheckBox("Select All")
        select_all_cb.stateChanged.connect(
            lambda state, r=role: self.select_all_cases(r, state == Qt.Checked)
        )
        layout.addWidget(select_all_cb)
        
        # Table for cases
        table = QTableWidget()
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        
        # Set column headers
        headers = ["Case No", "Responsibility", "Amount", "Description", "LC Minutes"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        # Configure table
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Case No
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Responsibility
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Amount
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Description
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # LC Minutes
        
        layout.addWidget(table)
        
        # Store references
        if role == "cfo":
            self.cfo_summary_label = summary_label
            self.cfo_select_all_cb = select_all_cb
            self.cfo_table = table
        else:
            self.hod_summary_label = summary_label
            self.hod_select_all_cb = select_all_cb
            self.hod_table = table
        
        group.setLayout(layout)
        return group
        
    def load_cases(self):
        """Load and group cases by delegation."""
        self.all_cases = get_write_off_recommended_cases()
        
        if not self.all_cases:
            QMessageBox.information(
                self, "No Cases", 
                "No cases found with Write-Off Recommended status."
            )
            return
            
        # Group cases by delegation
        self.cfo_cases, self.hod_cases = group_cases_by_delegation(self.all_cases)
        
        # Update summary labels
        delegation = get_current_delegation()
        cfo_limit = delegation['cfo_limit'] if delegation else 50000
        
        self.cfo_summary_label.setText(
            f"Cases ≤ R {cfo_limit:,.2f} (CFO Approval)\n"
            f"Total: {len(self.cfo_cases)} cases"
        )
        
        self.hod_summary_label.setText(
            f"Cases > R {cfo_limit:,.2f} (HOD Approval)\n"
            f"Total: {len(self.hod_cases)} cases"
        )
        
        # Populate tables
        self.populate_table(self.cfo_table, self.cfo_cases)
        self.populate_table(self.hod_table, self.hod_cases)
        
        # Enable generate button if we have cases
        self.generate_btn.setEnabled(len(self.all_cases) > 0)
        
    def populate_table(self, table, cases):
        """Populate a table with case data."""
        table.setRowCount(len(cases))
        
        for row, case in enumerate(cases):
            # Case No
            case_no_item = QTableWidgetItem(case['transaction_no'])
            case_no_item.setData(Qt.UserRole, case['id'])  # Store case ID
            table.setItem(row, 0, case_no_item)
            
            # Responsibility
            table.setItem(row, 1, QTableWidgetItem(case['responsibility_name']))
            
            # Amount
            amount_item = QTableWidgetItem(f"R {case['amount']:,.2f}")
            amount_item.setData(Qt.UserRole, case['amount'])
            table.setItem(row, 2, amount_item)
            
            # Description
            desc_item = QTableWidgetItem(case['description'])
            table.setItem(row, 3, desc_item)
            
            # LC Minutes status
            lc_minutes = self.get_lc_minutes_status(case['evidence_paths'])
            lc_item = QTableWidgetItem(lc_minutes)
            table.setItem(row, 4, lc_item)
            
    def get_lc_minutes_status(self, evidence_paths):
        """Check if LC minutes are available."""
        if not evidence_paths:
            return "Missing"
            
        try:
            import json
            evidence_data = json.loads(evidence_paths)
            lc_minutes = evidence_data.get('lc_minutes') or evidence_data.get('loss_control_minutes')
            return "Available" if lc_minutes else "Missing"
        except:
            return "Missing"
            
    def select_all_cases(self, role, selected):
        """Select or deselect all cases for a role."""
        table = self.cfo_table if role == "cfo" else self.hod_table
        
        for row in range(table.rowCount()):
            table.selectRow(row)
            
        self.update_selection_counts()
        
    def update_selection_counts(self):
        """Update the selection counts and enable/disable buttons."""
        # Get selected CFO cases
        self.selected_cfo_cases = []
        for row in range(self.cfo_table.rowCount()):
            if self.cfo_table.item(row, 0).isSelected():
                case_id = self.cfo_table.item(row, 0).data(Qt.UserRole)
                self.selected_cfo_cases.append(case_id)
                
        # Get selected HOD cases
        self.selected_hod_cases = []
        for row in range(self.hod_table.rowCount()):
            if self.hod_table.item(row, 0).isSelected():
                case_id = self.hod_table.item(row, 0).data(Qt.UserRole)
                self.selected_hod_cases.append(case_id)
                
        # Update generate button state
        has_selections = len(self.selected_cfo_cases) > 0 or len(self.selected_hod_cases) > 0
        self.generate_btn.setEnabled(has_selections)
        
    def generate_annexures(self):
        """Generate annexures for selected cases."""
        if not self.selected_cfo_cases and not self.selected_hod_cases:
            QMessageBox.warning(self, "No Selection", "Please select cases to include in annexures.")
            return
            
        # Get current financial year
        fy_id = get_current_financial_year_id()
        if not fy_id:
            QMessageBox.critical(self, "Error", "No active financial year found.")
            return
            
        try:
            # Create CFO annexure if cases selected
            if self.selected_cfo_cases:
                self.cfo_annexure_id = create_annexure("CFO", fy_id, self.selected_cfo_cases)
                if self.cfo_annexure_id:
                    QMessageBox.information(
                        self, "Success", 
                        f"CFO annexure created successfully!\n"
                        f"Cases included: {len(self.selected_cfo_cases)}"
                    )
                    
            # Create HOD annexure if cases selected
            if self.selected_hod_cases:
                self.hod_annexure_id = create_annexure("HOD", fy_id, self.selected_hod_cases)
                if self.hod_annexure_id:
                    QMessageBox.information(
                        self, "Success", 
                        f"HOD annexure created successfully!\n"
                        f"Cases included: {len(self.selected_hod_cases)}"
                    )
                    
            # Enable export buttons
            if self.cfo_annexure_id or self.hod_annexure_id:
                self.export_excel_btn.setEnabled(True)
                self.export_pdf_btn.setEnabled(True)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create annexures: {str(e)}")
            
    def export_excel(self):
        """Export annexures to Excel."""
        if not self.cfo_annexure_id and not self.hod_annexure_id:
            QMessageBox.warning(self, "No Annexures", "No annexures have been created yet.")
            return
            
        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel File", "write_off_annexures.xlsx", 
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
            
        try:
            export_annexure_to_excel([self.cfo_annexure_id, self.hod_annexure_id], file_path)
            QMessageBox.information(self, "Success", f"Excel file saved: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export Excel: {str(e)}")
            
    def export_pdf(self):
        """Export annexures to PDF."""
        if not self.cfo_annexure_id and not self.hod_annexure_id:
            QMessageBox.warning(self, "No Annexures", "No annexures have been created yet.")
            return
            
        # Ask user for PDF options
        from PyQt5.QtWidgets import QInputDialog
        include_minutes, ok = QInputDialog.getItem(
            self, "PDF Options", "Include LC Minutes in PDF?",
            ["Annexure Only", "Annexure + LC Minutes"], 0, False
        )
        
        if not ok:
            return
            
        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF File", "write_off_annexures.pdf", 
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
            
        try:
            include_lc_minutes = include_minutes == "Annexure + LC Minutes"
            export_annexure_to_pdf([self.cfo_annexure_id, self.hod_annexure_id], file_path, include_lc_minutes)
            QMessageBox.information(self, "Success", f"PDF file saved: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")
