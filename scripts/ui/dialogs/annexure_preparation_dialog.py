from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from scripts.Utilities.annexure_utils import (
    create_annexure,
    get_current_delegation,
    get_current_financial_year_id,
    get_write_off_recommended_cases,
    group_cases_by_delegation,
)
from scripts.Utilities.excel_exporter import export_annexure_to_excel
from scripts.Utilities.pdf_exporter import export_annexure_to_pdf


class AnnexurePreparationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Write-Off Annexure Management")
        self.setMinimumSize(1400, 800)  # Wider to accommodate side-by-side layout

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
        header_label = QLabel("Write-Off Annexure Management")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        # Instructions
        instructions = QLabel(
            "Select specific cases to include in annexures. Cases are grouped by delegation level:\n"
            "• CFO Cases: ≤ current delegation limit (approved by CFO)\n"
            "• HOD Cases: > current delegation limit (approved by HOD)\n\n"
            "Check individual cases to include them in the annexure, or use Select All/None buttons."
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

        # Set column headers - add Include column for checkboxes
        headers = [
            "Include",
            "Case No",
            "Responsibility",
            "Amount",
            "Description",
            "LC Minutes",
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        # Configure table
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Include checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Case No
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Responsibility
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Amount
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Description
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # LC Minutes

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
                self, "No Cases", "No cases found with Write-Off Recommended status."
            )
            return

        # Group cases by delegation
        self.cfo_cases, self.hod_cases = group_cases_by_delegation(self.all_cases)

        # Update summary labels
        delegation = get_current_delegation()
        cfo_limit = delegation["cfo_limit"] if delegation else 50000

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
            # Include checkbox - default to selected
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # Default to selected
            checkbox.stateChanged.connect(
                lambda state, r=row, t=table: self.update_selection(
                    t, r, state == Qt.Checked
                )
            )
            table.setCellWidget(row, 0, checkbox)

            # Case No
            case_no_item = QTableWidgetItem(case["transaction_no"])
            case_no_item.setData(Qt.UserRole, case["id"])  # Store case ID
            table.setItem(row, 1, case_no_item)

            # Responsibility
            table.setItem(row, 2, QTableWidgetItem(case["responsibility_name"]))

            # Amount
            amount_item = QTableWidgetItem(f"R {case['amount']:,.2f}")
            amount_item.setData(Qt.UserRole, case["amount"])
            table.setItem(row, 3, amount_item)

            # Description
            desc_item = QTableWidgetItem(case["description"])
            table.setItem(row, 4, desc_item)

            # LC Minutes status
            lc_minutes = self.get_lc_minutes_status(case["evidence_paths"])
            lc_item = QTableWidgetItem(lc_minutes)
            table.setItem(row, 5, lc_item)

            # Store checkbox reference for select all functionality
            if table == self.cfo_table:
                if not hasattr(self, "cfo_checkboxes"):
                    self.cfo_checkboxes = []
                self.cfo_checkboxes.append(checkbox)
            elif table == self.hod_table:
                if not hasattr(self, "hod_checkboxes"):
                    self.hod_checkboxes = []
                self.hod_checkboxes.append(checkbox)

    def get_lc_minutes_status(self, evidence_paths):
        """Check if LC minutes are available."""
        if not evidence_paths:
            return "Missing"

        try:
            import json

            evidence_data = json.loads(evidence_paths)
            lc_minutes = evidence_data.get("lc_minutes") or evidence_data.get(
                "loss_control_minutes"
            )
            return "Available" if lc_minutes else "Missing"
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            import logging

            logging.warning(f"Failed to parse evidence paths '{evidence_paths}': {e}")
            return "Missing"

    def select_all_cases(self, role, selected):
        """Select or deselect all cases for a role."""
        checkboxes = self.cfo_checkboxes if role == "cfo" else self.hod_checkboxes
        for checkbox in checkboxes:
            checkbox.setChecked(selected)
        self.update_generate_button()

    def update_selection_counts(self):
        """Update the selection counts and enable/disable buttons."""
        # Get selected CFO cases
        self.selected_cfo_cases = []
        for row in range(self.cfo_table.rowCount()):
            checkbox = self.cfo_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                case_id = self.cfo_table.item(row, 1).data(
                    Qt.UserRole
                )  # Case No column is now index 1
                self.selected_cfo_cases.append(case_id)

        # Get selected HOD cases
        self.selected_hod_cases = []
        for row in range(self.hod_table.rowCount()):
            checkbox = self.hod_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                case_id = self.hod_table.item(row, 1).data(
                    Qt.UserRole
                )  # Case No column is now index 1
                self.selected_hod_cases.append(case_id)

        # Update generate button state
        has_selections = (
            len(self.selected_cfo_cases) > 0 or len(self.selected_hod_cases) > 0
        )
        self.generate_btn.setEnabled(has_selections)

    def update_selection(self, table, row, checked):
        """Update selection when individual checkbox changes."""
        self.update_generate_button()

    def update_generate_button(self):
        """Update the generate button state based on selections."""
        # Count selected CFO cases
        cfo_selected = sum(
            1 for cb in getattr(self, "cfo_checkboxes", []) if cb.isChecked()
        )
        hod_selected = sum(
            1 for cb in getattr(self, "hod_checkboxes", []) if cb.isChecked()
        )

        has_selections = cfo_selected > 0 or hod_selected > 0
        self.generate_btn.setEnabled(has_selections)

        # Update summary labels with selection counts
        if hasattr(self, "cfo_summary_label"):
            delegation = get_current_delegation()
            cfo_limit = delegation["cfo_limit"] if delegation else 50000
            total_cfo = len(getattr(self, "cfo_cases", []))
            self.cfo_summary_label.setText(
                f"Cases ≤ R {cfo_limit:,.2f} (CFO Approval)\n"
                f"Total: {total_cfo} cases, Selected: {cfo_selected}"
            )

        if hasattr(self, "hod_summary_label"):
            total_hod = len(getattr(self, "hod_cases", []))
            self.hod_summary_label.setText(
                f"Cases > R {cfo_limit:,.2f} (HOD Approval)\n"
                f"Total: {total_hod} cases, Selected: {hod_selected}"
            )

    def generate_annexures(self):
        """Generate annexures for selected cases."""
        # Update selection counts first
        self.update_selection_counts()

        if not self.selected_cfo_cases and not self.selected_hod_cases:
            QMessageBox.warning(
                self, "No Selection", "Please select cases to include in annexures."
            )
            return

        # Get current financial year
        fy_id = get_current_financial_year_id()
        if not fy_id:
            QMessageBox.critical(self, "Error", "No active financial year found.")
            return

        try:
            # Create CFO annexure if cases selected
            if self.selected_cfo_cases:
                self.cfo_annexure_id = create_annexure(
                    "CFO", fy_id, self.selected_cfo_cases
                )
                if self.cfo_annexure_id:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"CFO annexure created successfully!\n"
                        f"Cases included: {len(self.selected_cfo_cases)}",
                    )

            # Create HOD annexure if cases selected
            if self.selected_hod_cases:
                self.hod_annexure_id = create_annexure(
                    "HOD", fy_id, self.selected_hod_cases
                )
                if self.hod_annexure_id:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"HOD annexure created successfully!\n"
                        f"Cases included: {len(self.selected_hod_cases)}",
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
            QMessageBox.warning(
                self, "No Annexures", "No annexures have been created yet."
            )
            return

        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel File", "write_off_annexures.xlsx", "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        try:
            export_annexure_to_excel(
                [self.cfo_annexure_id, self.hod_annexure_id], file_path
            )
            QMessageBox.information(self, "Success", f"Excel file saved: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export Excel: {str(e)}")

    def export_pdf(self):
        """Export annexures to PDF."""
        if not self.cfo_annexure_id and not self.hod_annexure_id:
            QMessageBox.warning(
                self, "No Annexures", "No annexures have been created yet."
            )
            return

        # Ask user for PDF options
        from PyQt5.QtWidgets import QInputDialog

        export_option, ok = QInputDialog.getItem(
            self,
            "PDF Export Options",
            "Choose export format:",
            [
                "Basic Annexure (Excel-style)",
                "Standard Annexure (with LC Minutes)",
                "Detailed Annexure (indexed evidence)",
            ],
            0,
            False,
        )

        if not ok:
            return

        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF File", "write_off_annexures.pdf", "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        try:
            if export_option == "Basic Annexure (Excel-style)":
                include_lc_minutes = False
                detailed_export = False
            elif export_option == "Standard Annexure (with LC Minutes)":
                include_lc_minutes = True
                detailed_export = False
            else:  # Detailed Annexure
                include_lc_minutes = True
                detailed_export = True

            export_annexure_to_pdf(
                [self.cfo_annexure_id, self.hod_annexure_id],
                file_path,
                include_lc_minutes,
                detailed_export,
            )
            QMessageBox.information(self, "Success", f"PDF file saved: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")
