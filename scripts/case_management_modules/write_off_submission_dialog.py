import sqlite3
import csv
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QMessageBox,
    QLabel,
    QGroupBox,
    QTextEdit,
    QCheckBox,
    QFileDialog,
    QWidget,
)
from PyQt5.QtCore import Qt
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.utils import format_currency_amount
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.workflow_utils import create_write_off_group, approve_write_off_submission


class WriteOffSubmissionDialog(QDialog):
    """Dialog for creating write-off submissions with case grouping"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Write-Off Submission")
        self.setFixedSize(1000, 800)
        self.fy = get_financial_year()
        self.selected_case_ids = []
        self.setup_ui()
        self.load_write_off_recommended_cases()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Select multiple cases from Write-Off Recommended list to create a grouped submission.\n"
            "All selected cases will be assigned the same submission ID and can be approved together."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(instructions)

        # Cases Table
        cases_group = QGroupBox("Write-Off Recommended Cases")
        cases_layout = QVBoxLayout(cases_group)

        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(6)
        self.cases_table.setHorizontalHeaderLabels([
            "Select", "Case No", "Date Reported", "Category", "Amount", "Evidence"
        ])

        # Set column widths
        header = self.cases_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.cases_table.setColumnWidth(0, 60)   # Select
        self.cases_table.setColumnWidth(1, 120)  # Case No
        self.cases_table.setColumnWidth(2, 140)  # Date Reported
        self.cases_table.setColumnWidth(3, 150)  # Category
        self.cases_table.setColumnWidth(4, 120)  # Amount
        self.cases_table.setColumnWidth(5, 200)  # Evidence

        cases_layout.addWidget(self.cases_table)
        layout.addWidget(cases_group)

        # Selection summary
        self.summary_label = QLabel("Selected: 0 cases, Total: R 0.00")
        self.summary_label.setStyleSheet("font-weight: bold; margin: 10px 0;")
        layout.addWidget(self.summary_label)

        # Action buttons
        button_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_cases)
        button_layout.addWidget(self.select_all_btn)

        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.clicked.connect(self.clear_selection)
        button_layout.addWidget(self.clear_selection_btn)

        button_layout.addStretch()

        self.generate_submission_btn = QPushButton("Generate Write-Off Submission")
        self.generate_submission_btn.clicked.connect(self.generate_submission)
        self.generate_submission_btn.setStyleSheet("QPushButton { background-color: #007bff; color: white; font-weight: bold; }")
        button_layout.addWidget(self.generate_submission_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_write_off_recommended_cases(self):
        """Load cases that are in Write-Off Recommended status"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            # Get cases with -WOR suffix (Write-Off Recommended)
            cursor.execute("""
                SELECT id, base_transaction_no, date_reported, category, amount, evidence_paths
                FROM cases
                WHERE suffixes LIKE '%-WOR%' AND is_finalized = 0
                ORDER BY base_transaction_no
            """)

            cases = cursor.fetchall()
            self.cases_table.setRowCount(len(cases))

            for row, case_data in enumerate(cases):
                case_id, base_transaction_no, date_reported, category, amount, evidence_paths = case_data

                # Checkbox for selection
                checkbox = QCheckBox()
                checkbox.stateChanged.connect(self.update_selection_summary)
                self.cases_table.setCellWidget(row, 0, checkbox)

                # Case No
                self.cases_table.setItem(row, 1, QTableWidgetItem(base_transaction_no))

                # Date Reported
                self.cases_table.setItem(row, 2, QTableWidgetItem(str(date_reported) if date_reported else ""))

                # Category
                self.cases_table.setItem(row, 3, QTableWidgetItem(str(category) if category else ""))

                # Amount
                amount_item = format_currency_amount(amount, right_align=True)
                self.cases_table.setItem(row, 4, amount_item)

                # Evidence status
                evidence_status = self.get_evidence_status(evidence_paths)
                self.cases_table.setItem(row, 5, QTableWidgetItem(evidence_status))

                # Store case_id in the row
                self.cases_table.item(row, 1).setData(Qt.UserRole, case_id)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load cases: {str(e)}")
        finally:
            conn.close()

    def get_evidence_status(self, evidence_paths):
        """Get a summary of evidence status"""
        if not evidence_paths:
            return "No evidence"

        try:
            import json
            evidence = json.loads(evidence_paths)
            evidence_types = []
            if evidence.get('assessment'):
                evidence_types.append("Assessment")
            if evidence.get('lc_minutes'):
                evidence_types.append("LC Minutes")
            if evidence.get('recovery'):
                evidence_types.append("Recovery")

            return ", ".join(evidence_types) if evidence_types else "No evidence"
        except:
            return "Invalid evidence data"

    def select_all_cases(self):
        """Select all cases in the table"""
        for row in range(self.cases_table.rowCount()):
            checkbox = self.cases_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(True)

    def clear_selection(self):
        """Clear all selections"""
        for row in range(self.cases_table.rowCount()):
            checkbox = self.cases_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(False)

    def update_selection_summary(self):
        """Update the selection summary label"""
        selected_cases = []
        total_amount = 0.0

        for row in range(self.cases_table.rowCount()):
            checkbox = self.cases_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                case_id = self.cases_table.item(row, 1).data(Qt.UserRole)
                amount_text = self.cases_table.item(row, 4).text().replace("R ", "").replace(",", "")
                try:
                    amount = float(amount_text)
                    total_amount += amount
                except ValueError:
                    pass
                selected_cases.append(case_id)

        self.selected_case_ids = selected_cases
        formatted_amount = format_currency_amount(total_amount)
        self.summary_label.setText(f"Selected: {len(selected_cases)} cases, Total: {formatted_amount}")

        # Enable/disable generate button
        self.generate_submission_btn.setEnabled(len(selected_cases) > 0)

    def generate_submission(self):
        """Generate a write-off submission for selected cases"""
        if not self.selected_case_ids:
            QMessageBox.warning(self, "No Selection", "Please select at least one case.")
            return

        # Confirm with user
        reply = QMessageBox.question(
            self, "Generate Write-Off Submission",
            f"Are you sure you want to create a write-off submission for {len(self.selected_case_ids)} cases?\n\n"
            "This will assign a group ID to all selected cases and allow them to be approved together.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # Generate the group ID
            group_id = create_write_off_group(self.selected_case_ids)

            if group_id:
                # Generate annexure (CSV export)
                self.generate_annexure(group_id)

                QMessageBox.information(
                    self, "Success",
                    f"Write-off submission created successfully!\n\n"
                    f"Group ID: {group_id}\n"
                    f"Cases grouped: {len(self.selected_case_ids)}\n\n"
                    f"An annexure has been generated and saved."
                )

                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to create write-off submission.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate submission: {str(e)}")

    def generate_annexure(self, group_id):
        """Generate CSV, PDF, and Excel annexures for the write-off submission"""
        try:
            # Create year folder if it doesn't exist
            from scripts.Utilities.financial_utils import create_year_folder
            year_folder = create_year_folder(self.fy)
            annexure_dir = os.path.join(year_folder, "Annexures")
            os.makedirs(annexure_dir, exist_ok=True)

            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Get case details
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT base_transaction_no, date_reported, category, amount,
                       assessment_status, lc_status, evidence_paths
                FROM cases
                WHERE write_off_group_id = ?
                ORDER BY base_transaction_no
            """, (group_id,))

            cases = cursor.fetchall()
            conn.close()

            # Generate CSV
            csv_filename = f"Write_Off_Annexure_{group_id}_{timestamp}.csv"
            csv_filepath = os.path.join(annexure_dir, csv_filename)

            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'Case Number', 'Date Reported', 'Category', 'Amount',
                    'Assessment Status', 'LC Status', 'Evidence Available'
                ])

                for case in cases:
                    base_transaction_no, date_reported, category, amount, assessment_status, lc_status, evidence_paths = case
                    evidence_status = self.get_evidence_status(evidence_paths)
                    writer.writerow([
                        base_transaction_no, date_reported, category,
                        amount, assessment_status, lc_status, evidence_status
                    ])

            print(f"CSV Annexure generated: {csv_filepath}")

            # Generate PDF
            pdf_filename = f"Write_Off_Annexure_{group_id}_{timestamp}.pdf"
            pdf_filepath = os.path.join(annexure_dir, pdf_filename)

            self.generate_pdf_annexure(pdf_filepath, group_id, cases, timestamp)

            print(f"PDF Annexure generated: {pdf_filepath}")

            # Generate Excel
            excel_filename = f"Write_Off_Annexure_{group_id}_{timestamp}.xlsx"
            excel_filepath = os.path.join(annexure_dir, excel_filename)

            self.generate_excel_annexure(excel_filepath, group_id, cases, timestamp)

            print(f"Excel Annexure generated: {excel_filepath}")

        except Exception as e:
            print(f"Error generating annexure: {e}")
            # Don't show error dialog here as it's called from generate_submission which already handles errors

    def generate_pdf_annexure(self, filepath, group_id, cases, timestamp):
        """Generate a PDF annexure for the write-off submission"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from scripts.Utilities.utils import format_currency_amount

            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title = Paragraph(f"<b>Write-Off Submission Annexure</b>", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 12))

            # Submission details
            details = Paragraph(f"""
            <b>Submission ID:</b> {group_id}<br/>
            <b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br/>
            <b>Total Cases:</b> {len(cases)}<br/>
            <b>Total Amount:</b> R {sum(case[3] for case in cases):,.2f}
            """, styles['Normal'])
            elements.append(details)
            elements.append(Spacer(1, 20))

            # Table data
            data = [['Case Number', 'Date Reported', 'Category', 'Amount', 'Assessment Status', 'LC Status', 'Evidence']]

            for case in cases:
                base_transaction_no, date_reported, category, amount, assessment_status, lc_status, evidence_paths = case
                evidence_status = self.get_evidence_status(evidence_paths)
                formatted_amount = format_currency_amount(amount)
                data.append([
                    base_transaction_no,
                    str(date_reported) if date_reported else '',
                    str(category) if category else '',
                    formatted_amount,
                    assessment_status or '',
                    lc_status or '',
                    evidence_status
                ])

            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(table)

            # Build PDF
            doc.build(elements)

        except ImportError:
            print("Warning: reportlab not installed. PDF annexure generation skipped.")
        except Exception as e:
            print(f"Error generating PDF annexure: {e}")

    def generate_excel_annexure(self, filepath, group_id, cases, timestamp):
        """Generate an Excel annexure for the write-off submission"""
        try:
            import pandas as pd

            # Prepare data for DataFrame - structure case data into dictionary format for pandas
            data = []
            for case in cases:
                base_transaction_no, date_reported, category, amount, assessment_status, lc_status, evidence_paths = case
                evidence_status = self.get_evidence_status(evidence_paths)
                data.append({
                    'Case Number': base_transaction_no,
                    'Date Reported': str(date_reported) if date_reported else '',
                    'Category': str(category) if category else '',
                    'Amount': amount,
                    'Assessment Status': assessment_status or '',
                    'LC Status': lc_status or '',
                    'Evidence Available': evidence_status
                })

            # Create DataFrame from prepared data
            df = pd.DataFrame(data)

            # Create Excel writer with openpyxl engine for advanced formatting
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Write DataFrame to Excel with specified sheet name, excluding DataFrame index
                df.to_excel(writer, sheet_name='Write-Off Annexure', index=False)

                # Get workbook and worksheet references for post-processing formatting
                workbook = writer.book
                worksheet = writer.sheets['Write-Off Annexure']

                # Format amount column as South African currency (R with commas and 2 decimals)
                from openpyxl.styles import NamedStyle
                currency_style = NamedStyle(name='currency', number_format='R #,##0.00')
                workbook.add_named_style(currency_style)

                # Apply currency formatting to Amount column (find column by name, apply to data rows)
                amount_col = None
                for col_num, column_title in enumerate(df.columns, 1):
                    if column_title == 'Amount':
                        amount_col = col_num
                        break

                if amount_col:
                    for row_num in range(2, len(df) + 2):  # Start from row 2 (after header)
                        cell = worksheet.cell(row=row_num, column=amount_col)
                        cell.style = 'currency'

                # Auto-adjust column widths based on content length
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters for readability
                    worksheet.column_dimensions[column_letter].width = adjusted_width

                # Add summary information at the top of the worksheet
                worksheet.insert_rows(1)
                worksheet['A1'] = f'Write-Off Submission Annexure - Group: {group_id}'
                worksheet['A2'] = f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                worksheet['A3'] = f'Total Cases: {len(cases)}'
                worksheet['A4'] = f'Total Amount: R {sum(case[3] for case in cases):,.2f}'

                # Merge cells for title row spanning all columns
                from openpyxl.utils import range_boundaries
                worksheet.merge_cells('A1:G1')

        except ImportError:
            print("Warning: pandas/openpyxl not installed. Excel annexure generation skipped.")
        except Exception as e:
            print(f"Error generating Excel annexure: {e}")


class WriteOffApprovalDialog(QDialog):
    """Dialog for approving write-off submissions"""

    def __init__(self, group_id, parent=None):
        super().__init__(parent)
        self.group_id = group_id
        self.setWindowTitle(f"Approve Write-Off Submission - {group_id}")
        self.setFixedSize(800, 600)
        self.fy = get_financial_year()
        self.setup_ui()
        self.load_group_details()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Group info
        info_group = QGroupBox("Submission Details")
        info_layout = QVBoxLayout(info_group)

        self.info_label = QLabel()
        info_layout.addWidget(self.info_label)

        layout.addWidget(info_group)

        # Cases table
        cases_group = QGroupBox("Cases in Submission")
        cases_layout = QVBoxLayout(cases_group)

        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(5)
        self.cases_table.setHorizontalHeaderLabels([
            "Case No", "Category", "Amount", "Assessment Status", "Evidence"
        ])

        header = self.cases_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.cases_table.setColumnWidth(0, 120)  # Case No
        self.cases_table.setColumnWidth(1, 150)  # Category
        self.cases_table.setColumnWidth(2, 120)  # Amount
        self.cases_table.setColumnWidth(3, 140)  # Assessment Status
        self.cases_table.setColumnWidth(4, 200)  # Evidence

        cases_layout.addWidget(self.cases_table)
        layout.addWidget(cases_group)

        # Approval notes
        notes_group = QGroupBox("Approval Notes (Optional)")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Enter any approval notes...")
        self.notes_edit.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_edit)

        layout.addWidget(notes_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.approve_btn = QPushButton("Approve Write-Off")
        self.approve_btn.clicked.connect(self.approve_submission)
        self.approve_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; }")
        button_layout.addWidget(self.approve_btn)

        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_group_details(self):
        """Load details of the write-off group"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            # Get group summary
            cursor.execute("""
                SELECT COUNT(*), SUM(amount)
                FROM cases
                WHERE write_off_group_id = ?
            """, (self.group_id,))

            summary = cursor.fetchone()
            if summary:
                case_count, total_amount = summary
                formatted_amount = format_currency_amount(total_amount or 0)
                self.info_label.setText(
                    f"Group ID: {self.group_id}\n"
                    f"Total Cases: {case_count}\n"
                    f"Total Amount: {formatted_amount}"
                )

            # Get case details
            cursor.execute("""
                SELECT base_transaction_no, category, amount, assessment_status, evidence_paths
                FROM cases
                WHERE write_off_group_id = ?
                ORDER BY base_transaction_no
            """, (self.group_id,))

            cases = cursor.fetchall()
            self.cases_table.setRowCount(len(cases))

            for row, case_data in enumerate(cases):
                base_transaction_no, category, amount, assessment_status, evidence_paths = case_data

                self.cases_table.setItem(row, 0, QTableWidgetItem(base_transaction_no))
                self.cases_table.setItem(row, 1, QTableWidgetItem(str(category) if category else ""))
                amount_item = format_currency_amount(amount, right_align=True)
                self.cases_table.setItem(row, 2, amount_item)
                self.cases_table.setItem(row, 3, QTableWidgetItem(assessment_status or ""))

                evidence_status = self.get_evidence_status(evidence_paths)
                self.cases_table.setItem(row, 4, QTableWidgetItem(evidence_status))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load group details: {str(e)}")
        finally:
            conn.close()

    def get_evidence_status(self, evidence_paths):
        """Get a summary of evidence status"""
        if not evidence_paths:
            return "No evidence"

        try:
            import json
            evidence = json.loads(evidence_paths)
            evidence_types = []
            if evidence.get('assessment'):
                evidence_types.append("Assessment")
            if evidence.get('lc_minutes'):
                evidence_types.append("LC Minutes")
            if evidence.get('recovery'):
                evidence_types.append("Recovery")

            return ", ".join(evidence_types) if evidence_types else "No evidence"
        except:
            return "Invalid evidence data"

    def approve_submission(self):
        """Approve the write-off submission"""
        notes = self.notes_edit.toPlainText().strip()

        reply = QMessageBox.question(
            self, "Approve Write-Off",
            f"Are you sure you want to approve write-off submission {self.group_id}?\n\n"
            "This will finalize all cases in the submission and they will appear in the Written Off list.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success = approve_write_off_submission(self.group_id)

                if success:
                    QMessageBox.information(
                        self, "Success",
                        f"Write-off submission {self.group_id} has been approved!\n\n"
                        "All cases have been finalized and moved to Written Off."
                    )
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to approve write-off submission.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to approve submission: {str(e)}")