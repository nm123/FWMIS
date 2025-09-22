import os
import sqlite3
from datetime import datetime

from PyQt5.QtCore import QDate, QEvent, Qt
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import (QComboBox, QDateEdit, QDialog, QFileDialog,
                             QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
                             QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QMessageBox, QPushButton, QScrollArea,
                             QTableWidget, QTableWidgetItem, QTextEdit,
                             QVBoxLayout, QWidget, QWizard, QWizardPage)
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH, initialize_shared_documents_table
from scripts.Utilities.financial_utils import (generate_transaction_no,
                                               get_financial_year)
from scripts.Utilities.utils import format_currency_amount


class NoWheelComboBox(QComboBox):
    """Custom QComboBox that ignores mouse wheel events unless focused"""

    def wheelEvent(self, event: QWheelEvent):
        """Override wheel event to only accept when widget has focus"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # Ignore wheel event when not focused
            event.ignore()


class BulkCaseEntryWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bulk Case Entry")
        self.setFixedSize(1000, 700)

        # Initialize database
        initialize_shared_documents_table()

        # Shared data
        self.shared_document_id = None
        self.cases_data = []
        self.document_path = ""
        self.document_name = ""
        self.document_description = ""

        # Add pages
        self.addPage(DocumentUploadPage(self))
        self.addPage(CaseEntryPage(self))
        self.addPage(ReviewPage(self))

        # Set wizard properties
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoCancelButtonOnLastPage, False)

        # Connect finish signal
        self.button(QWizard.FinishButton).clicked.connect(self.on_finish)

    def get_cases_data(self):
        return self.cases_data

    def set_shared_document_id(self, doc_id):
        self.shared_document_id = doc_id

    def add_case_data(self, case_data):
        self.cases_data.append(case_data)

    def on_finish(self):
        """Handle wizard completion"""
        if save_bulk_cases(self):
            QMessageBox.information(
                self,
                "Success",
                f"Successfully created {len(self.cases_data)} cases with shared document.",
            )
        else:
            QMessageBox.critical(
                self, "Error", "Failed to save cases. Please try again."
            )


class DocumentUploadPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Step 1: Upload Shared Assessment Evidence")
        self.setSubTitle(
            "Upload the document that will be shared across multiple cases"
        )

        self.document_path = ""
        self.document_name = ""
        self.description = ""

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Document upload section
        upload_group = QGroupBox("Document Upload")
        upload_layout = QFormLayout(upload_group)

        # Document path display
        self.doc_path_edit = QLineEdit()
        self.doc_path_edit.setReadOnly(True)
        self.doc_path_edit.setPlaceholderText("No document selected")

        # Browse button
        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.doc_path_edit)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_document)
        browse_layout.addWidget(browse_button)

        upload_layout.addRow("Document:", browse_layout)

        # Document name
        self.doc_name_edit = QLineEdit()
        self.doc_name_edit.setPlaceholderText("Enter document name/description")
        upload_layout.addRow("Document Name:", self.doc_name_edit)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText(
            "Optional: Describe what this document covers"
        )
        upload_layout.addRow("Description:", self.description_edit)

        layout.addWidget(upload_group)

        # Register fields for validation
        self.registerField("document_path*", self.doc_path_edit)
        self.registerField("document_name*", self.doc_name_edit)

    def browse_document(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Shared Assessment Evidence", "", "All Files (*.*)"
        )
        if file_path:
            self.document_path = file_path
            self.doc_path_edit.setText(os.path.basename(file_path))
            if not self.doc_name_edit.text():
                self.doc_name_edit.setText(
                    os.path.splitext(os.path.basename(file_path))[0]
                )

            # Create shared document record
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO shared_documents (document_path, document_name, upload_date, fy_id, document_type)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        file_path,  # Temporary path, will be updated when saved
                        os.path.splitext(os.path.basename(file_path))[0],
                        datetime.now().isoformat(),
                        get_financial_year(),
                        "assessment_evidence",
                    ),
                )
                doc_id = cursor.lastrowid
                conn.commit()
                conn.close()

                # Set document ID in wizard
                self.wizard().set_shared_document_id(doc_id)

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to create document record: {str(e)}"
                )

    def validatePage(self):
        if not self.document_path:
            QMessageBox.warning(
                self, "Document Required", "Please select a document to upload."
            )
            return False
        if not self.doc_name_edit.text().strip():
            QMessageBox.warning(
                self, "Document Name Required", "Please enter a document name."
            )
            return False
        return True

    def nextId(self):
        return 1  # Case Entry Page


class CaseEntryPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Step 2: Enter Cases")
        self.setSubTitle("Add multiple cases that will share the uploaded document")

        self.cases = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Cases list
        cases_group = QGroupBox("Cases to Add")
        cases_layout = QVBoxLayout(cases_group)

        # Cases table
        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(4)
        self.cases_table.setHorizontalHeaderLabels(
            ["Case No", "Description", "Amount", "Status"]
        )
        self.cases_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cases_table.setMaximumHeight(200)
        cases_layout.addWidget(self.cases_table)

        # Add case button
        add_case_button = QPushButton("Add Case")
        add_case_button.clicked.connect(self.add_case)
        cases_layout.addWidget(add_case_button)

        # Remove case button
        remove_case_button = QPushButton("Remove Selected Case")
        remove_case_button.clicked.connect(self.remove_case)
        cases_layout.addWidget(remove_case_button)

        layout.addWidget(cases_group)

        # Case entry form
        form_group = QGroupBox("Case Details")
        self.form_layout = QFormLayout(form_group)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        self.form_layout.addRow("Description:", self.description_edit)

        # Amount
        self.amount_edit = QLineEdit()
        self.form_layout.addRow("Amount:", self.amount_edit)

        # Status
        self.status_combo = NoWheelComboBox()
        self.status_combo.addItems(
            ["Alleged", "Under Assessment", "Valid", "Confirmed"]
        )
        self.status_combo.setCurrentText("Alleged")
        self.form_layout.addRow("Status:", self.status_combo)

        # Add to form button
        add_to_list_button = QPushButton("Add to List")
        add_to_list_button.clicked.connect(self.add_to_list)
        self.form_layout.addRow("", add_to_list_button)

        layout.addWidget(form_group)

    def add_case(self):
        # This would open a simplified case entry dialog
        # For now, we'll use the form above
        pass

    def add_to_list(self):
        description = self.description_edit.toPlainText().strip()
        amount = self.amount_edit.text().strip()
        status = self.status_combo.currentText()

        if not description:
            QMessageBox.warning(
                self, "Description Required", "Please enter a case description."
            )
            return
        if not amount:
            QMessageBox.warning(self, "Amount Required", "Please enter an amount.")
            return

        try:
            amount_val = float(amount)
            if amount_val <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Amount", "Amount must be a positive number."
            )
            return

        # Generate case number
        fy = get_financial_year()
        case_no = generate_transaction_no(fy)

        # Add to table
        row = self.cases_table.rowCount()
        self.cases_table.insertRow(row)
        self.cases_table.setItem(row, 0, QTableWidgetItem(case_no))
        self.cases_table.setItem(row, 1, QTableWidgetItem(description))
        amount_item = format_currency_amount(amount, right_align=True)
        self.cases_table.setItem(row, 2, amount_item)
        self.cases_table.setItem(row, 3, QTableWidgetItem(status))

        # Store case data
        case_data = {
            "transaction_no": case_no,
            "description": description,
            "amount": amount_val,
            "status": status,
        }
        self.cases.append(case_data)
        self.wizard().add_case_data(case_data)

        # Clear form
        self.description_edit.clear()
        self.amount_edit.clear()
        self.status_combo.setCurrentText("Alleged")

    def remove_case(self):
        current_row = self.cases_table.currentRow()
        if current_row >= 0:
            self.cases_table.removeRow(current_row)
            if current_row < len(self.cases):
                self.cases.pop(current_row)

    def validatePage(self):
        if len(self.cases) == 0:
            QMessageBox.warning(self, "No Cases", "Please add at least one case.")
            return False
        return True

    def nextId(self):
        return 2  # Review Page


class ReviewPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Step 3: Review and Save")
        self.setSubTitle("Review all cases before saving")

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Summary
        summary_group = QGroupBox("Summary")
        summary_layout = QFormLayout(summary_group)

        self.doc_name_label = QLabel()
        summary_layout.addRow("Shared Document:", self.doc_name_label)

        self.cases_count_label = QLabel()
        summary_layout.addRow("Number of Cases:", self.cases_count_label)

        layout.addWidget(summary_group)

        # Cases review
        review_group = QGroupBox("Cases to be Created")
        review_layout = QVBoxLayout(review_group)

        self.review_table = QTableWidget()
        self.review_table.setColumnCount(4)
        self.review_table.setHorizontalHeaderLabels(
            ["Case No", "Description", "Amount", "Status"]
        )
        self.review_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        review_layout.addWidget(self.review_table)

        layout.addWidget(review_group)

    def initializePage(self):
        wizard = self.wizard()

        # Get document info from upload page
        upload_page = wizard.page(0)
        if hasattr(upload_page, "doc_name_edit"):
            doc_name = upload_page.doc_name_edit.text().strip()
            self.doc_name_label.setText(doc_name if doc_name else "Document uploaded")

        # Populate cases table
        cases_data = wizard.get_cases_data()
        self.cases_count_label.setText(str(len(cases_data)))

        self.review_table.setRowCount(0)
        for case in cases_data:
            row = self.review_table.rowCount()
            self.review_table.insertRow(row)
            self.review_table.setItem(row, 0, QTableWidgetItem(case["transaction_no"]))
            self.review_table.setItem(row, 1, QTableWidgetItem(case["description"]))
            amount_item = format_currency_amount(case["amount"], right_align=True)
            self.review_table.setItem(row, 2, amount_item)
            self.review_table.setItem(row, 3, QTableWidgetItem(case["status"]))

    def validatePage(self):
        return True


def save_bulk_cases(wizard):
    """Save the shared document and all cases"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get wizard data
        doc_page = wizard.page(0)  # DocumentUploadPage
        cases_data = wizard.get_cases_data()

        if not wizard.shared_document_id:
            raise Exception("No shared document ID found")

        # Save shared document
        fy = get_financial_year()
        year_folder = os.path.join(os.path.dirname(DB_PATH), "documents", "shared", fy)
        os.makedirs(year_folder, exist_ok=True)

        # Copy document to shared location
        doc_filename = f"SHARED_{wizard.shared_document_id}_{os.path.basename(doc_page.document_path)}"
        dest_path = os.path.join(year_folder, doc_filename)

        # Copy file
        with open(doc_page.document_path, "rb") as src:
            with open(dest_path, "wb") as dst:
                dst.write(src.read())

        # Update shared document record
        cursor.execute(
            """
            UPDATE shared_documents
            SET document_path = ?, document_name = ?, upload_date = ?, fy_id = ?, description = ?
            WHERE id = ?
        """,
            (
                dest_path,
                doc_page.doc_name_edit.text().strip(),
                datetime.now().isoformat(),
                fy,
                doc_page.description_edit.toPlainText().strip(),
                wizard.shared_document_id,
            ),
        )

        # Get proper fy_id
        from scripts.Utilities.financial_utils import \
            get_current_open_financial_year

        current_fy = get_current_open_financial_year()
        fy_id = current_fy[0] if current_fy else None

        if fy_id is None:
            raise Exception(
                "Cannot save bulk cases: No open financial year found. Please ensure a financial year is open in Financial Year Management."
            )

        # Save cases
        for case in cases_data:
            cursor.execute(
                """
                INSERT INTO cases (
                    transaction_no, description, amount, status, list,
                    shared_document_id, fy_id, date_reported
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    case["transaction_no"],
                    case["description"],
                    case["amount"],
                    case["status"],
                    "Checklist",  # Default to Checklist
                    wizard.shared_document_id,
                    fy_id,
                    datetime.now().strftime("%Y-%m-%d"),
                ),
            )

        conn.commit()
        conn.close()

        # Log audit trail
        save_audit_log(
            "bulk_case_entry",
            {
                "timestamp": datetime.now().isoformat(),
                "shared_document_id": wizard.shared_document_id,
                "cases_count": len(cases_data),
                "cases": cases_data,
            },
            fy,
        )

        return True

    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to save bulk cases: {str(e)}")
        return False
