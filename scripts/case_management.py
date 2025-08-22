import os
import sqlite3
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QDateEdit,
    QFileDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QSplitter,
)
from PyQt5.QtCore import QDate, Qt
from utils import (
    BASE_DIR,
    get_financial_year,
    generate_transaction_no,
    create_year_folder,
    save_audit_log,
    get_effective_contacts,
    is_valid_email,
    get_subtree_resp_ids,
    load_categories,
    load_responsibilities,
)
import win32com.client

class AddNewCaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Case")
        self.setFixedSize(600, 700)
        try:
            self.responsibilities = load_responsibilities()
            self.categories = load_categories()
            self.fy = get_financial_year()
            self.transaction_no = generate_transaction_no(self.fy)
            self.setup_ui()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize Add New Case dialog: {str(e)}")
            self.reject()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.trans_no_edit = QLineEdit(self.transaction_no)
        self.trans_no_edit.setReadOnly(True)
        form_layout.addRow("Transaction No:", self.trans_no_edit)

        self.date_incurred_edit = QDateEdit(QDate.currentDate())
        self.date_incurred_edit.setCalendarPopup(True)
        form_layout.addRow("Date Incurred:", self.date_incurred_edit)

        self.date_identified_edit = QDateEdit(QDate.currentDate())
        self.date_identified_edit.setCalendarPopup(True)
        form_layout.addRow("Date Identified:", self.date_identified_edit)

        self.date_reported_edit = QDateEdit(QDate.currentDate())
        self.date_reported_edit.setCalendarPopup(True)
        form_layout.addRow("Date Reported:", self.date_reported_edit)

        self.description_edit = QTextEdit()
        form_layout.addRow("Description:", self.description_edit)

        self.bas_payment_no_edit = QLineEdit()
        form_layout.addRow("BAS Payment No:", self.bas_payment_no_edit)

        self.bas_payment_date_edit = QDateEdit(QDate.currentDate())
        self.bas_payment_date_edit.setCalendarPopup(True)
        form_layout.addRow("BAS Payment Date:", self.bas_payment_date_edit)

        self.persal_no_edit = QLineEdit()
        form_layout.addRow("Persal No:", self.persal_no_edit)

        self.category_combo = QComboBox()
        self.category_combo.addItems([c["name"] for c in self.categories])  # Fixed: Extract category names
        form_layout.addRow("Category:", self.category_combo)

        self.responsibility_combo = QComboBox()
        self.responsibility_combo.addItems([r["name"] for r in self.responsibilities])
        form_layout.addRow("Responsibility:", self.responsibility_combo)

        self.amount_edit = QLineEdit()
        form_layout.addRow("Amount:", self.amount_edit)

        self.source_doc_edit = QLineEdit()
        self.source_doc_button = QPushButton("Browse")
        self.source_doc_button.clicked.connect(self.browse_source_doc)
        source_doc_layout = QHBoxLayout()
        source_doc_layout.addWidget(self.source_doc_edit)
        source_doc_layout.addWidget(self.source_doc_button)
        form_layout.addRow("Source Document:", source_doc_layout)

        self.minutes_edit = QLineEdit()
        self.minutes_button = QPushButton("Browse")
        self.minutes_button.clicked.connect(self.browse_minutes)
        minutes_layout = QHBoxLayout()
        minutes_layout.addWidget(self.minutes_edit)
        minutes_layout.addWidget(self.minutes_button)
        form_layout.addRow("Minutes:", minutes_layout)

        self.evidence_edit = QLineEdit()
        self.evidence_button = QPushButton("Browse")
        self.evidence_button.clicked.connect(self.browse_evidence)
        evidence_layout = QHBoxLayout()
        evidence_layout.addWidget(self.evidence_edit)
        evidence_layout.addWidget(self.evidence_button)
        form_layout.addRow("Evidence:", evidence_layout)

        self.list_edit = QLineEdit()
        form_layout.addRow("List:", self.list_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Draft", "Awaiting Evidence", "Confirmed"])
        form_layout.addRow("Status:", self.status_combo)

        self.assessed_by_edit = QLineEdit()
        form_layout.addRow("Assessed By:", self.assessed_by_edit)

        self.assessment_date_edit = QDateEdit(QDate.currentDate())
        self.assessment_date_edit.setCalendarPopup(True)
        form_layout.addRow("Assessment Date:", self.assessment_date_edit)

        self.assessment_result_edit = QTextEdit()
        form_layout.addRow("Assessment Result:", self.assessment_result_edit)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_case)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

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
            bas_payment_no = self.bas_payment_no_edit.text().strip()
            persal_no = self.persal_no_edit.text().strip()
            amount_text = self.amount_edit.text().strip()
            if not bas_payment_no or not persal_no or not amount_text:
                QMessageBox.warning(self, "Invalid Input", "BAS Payment No, Persal No, and Amount are required.")
                return
            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Amount must be a positive number.")
                return
            responsibility_name = self.responsibility_combo.currentText()
            responsibility = next((r for r in self.responsibilities if r["name"] == responsibility_name), None)
            if not responsibility:
                QMessageBox.warning(self, "Invalid Input", "Please select a valid responsibility.")
                return
            case = {
                "transaction_no": self.transaction_no,
                "date_incurred": self.date_incurred_edit.date().toString("yyyy-MM-dd"),
                "date_identified": self.date_identified_edit.date().toString("yyyy-MM-dd"),
                "date_reported": self.date_reported_edit.date().toString("yyyy-MM-dd"),
                "description": self.description_edit.toPlainText().strip(),
                "bas_payment_no": bas_payment_no,
                "bas_payment_date": self.bas_payment_date_edit.date().toString("yyyy-MM-dd"),
                "persal_no": persal_no,
                "category": self.category_combo.currentText(),
                "responsibility_id": responsibility["id"],
                "amount": amount,
                "source_document": self.source_doc_edit.text().strip(),
                "minutes": self.minutes_edit.text().strip(),
                "evidence_path": self.evidence_edit.text().strip(),
                "status": self.status_combo.currentText(),
                "list": self.list_edit.text().strip(),
                "assessment_assessed_by": self.assessed_by_edit.text().strip(),
                "assessment_date": self.assessment_date_edit.date().toString("yyyy-MM-dd"),
                "assessment_result": self.assessment_result_edit.toPlainText().strip()
            }
            year_folder = create_year_folder()
            for field in ["source_document", "minutes", "evidence_path"]:
                if case[field]:
                    dest_path = os.path.join(year_folder, f"{self.transaction_no}_{field}.pdf")
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    os.replace(case[field], dest_path)
                    case[field] = dest_path
            conn = sqlite3.connect(os.path.join(BASE_DIR, "fruitless.db"))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cases (
                    transaction_no, date_incurred, date_identified, date_reported, description,
                    bas_payment_no, bas_payment_date, persal_no, category, responsibility_id, amount,
                    source_document, minutes, evidence_path, status, list, assessment_assessed_by,
                    assessment_date, assessment_result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case["transaction_no"], case["date_incurred"], case["date_identified"], case["date_reported"],
                case["description"], case["bas_payment_no"], case["bas_payment_date"], case["persal_no"],
                case["category"], case["responsibility_id"], case["amount"], case["source_document"],
                case["minutes"], case["evidence_path"], case["status"], case["list"],
                case["assessment_assessed_by"], case["assessment_date"], case["assessment_result"]
            ))
            conn.commit()
            case_id = cursor.lastrowid
            conn.close()
            save_audit_log({
                "timestamp": datetime.now().isoformat(),
                "action": "add_case",
                "case_id": case_id,
                "transaction_no": self.transaction_no,
                "details": case
            }, self.fy)
            QMessageBox.information(self, "Success", "Case added successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save case: {str(e)}")
            self.reject()

    def next_case(self):
        self.transaction_no = generate_transaction_no(self.fy)
        self.trans_no_edit.setText(self.transaction_no)
        self.description_edit.clear()
        self.bas_payment_no_edit.clear()
        self.persal_no_edit.clear()
        self.amount_edit.clear()
        self.evidence_edit.clear()

    def send_reminder_email(self):
        resp_id = self.responsibilities[self.responsibility_combo.currentIndex()]["id"]
        contacts = get_effective_contacts(self.responsibilities, resp_id)
        emails = [c["email"] for c in contacts if is_valid_email(c["email"])]
        if not emails:
            QMessageBox.warning(self, "No Contacts", "No valid email contacts found for this responsibility.")
            return

        conn = sqlite3.connect(os.path.join(BASE_DIR, "fruitless.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT body FROM email_templates WHERE name = ?", ("Reminder - Assessment Evidence",))
        template = cursor.fetchone()
        conn.close()

        if not template:
            QMessageBox.warning(self, "No Template", "No email template found.")
            return

        body = template[0]
        body = body.replace("[Recipient]", ", ".join(c["name"] for c in contacts))
        body = body.replace("[Case ID]", self.transaction_no)
        body = body.replace("[Due Date]", QDate.currentDate().addDays(7).toString("yyyy-MM-dd"))
        body = body.replace("[Contact Email]", ", ".join(emails))
        body = body.replace("[Your Name]", "Accounts Payable Team")

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = ";".join(emails)
        mail.Subject = f"Reminder: Assessment Evidence for Case {self.transaction_no}"
        mail.Body = body
        mail.Display()

    def open_assessment(self):
        if not self.evidence_edit.text():
            QMessageBox.warning(self, "No Evidence", "Please upload evidence before assessment.")
            return
        dialog = AssessmentDialog(self)
        if dialog.exec_():
            assessment_data = dialog.get_assessment_data()
            conn = sqlite3.connect(os.path.join(BASE_DIR, "fruitless.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM cases")
            max_id = cursor.fetchone()[0]
            case_id = (max_id or 0) + 1
            cursor.execute("UPDATE cases SET assessment = ?, status = ?, list = ? WHERE transaction_no = ?",
                          (json.dumps(assessment_data), assessment_data["result"], "Lead Schedule", self.transaction_no))
            conn.commit()
            conn.close()
            save_audit_log({
                "timestamp": datetime.now().isoformat(),
                "action": "assess_case",
                "case_id": case_id,
                "transaction_no": self.transaction_no,
                "details": assessment_data
            }, self.fy)

class AssessmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Case Assessment")
        self.setFixedSize(400, 300)
        layout = QFormLayout(self)

        self.assessed_by_edit = QLineEdit()
        layout.addRow("Assessed By:", self.assessed_by_edit)

        self.assessment_date_edit = QDateEdit(QDate.currentDate())
        self.assessment_date_edit.setCalendarPopup(True)
        layout.addRow("Assessment Date:", self.assessment_date_edit)

        self.result_combo = QComboBox()
        self.result_combo.addItems(["Valid", "Confirmed"])
        layout.addRow("Result:", self.result_combo)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

    def get_assessment_data(self):
        return {
            "assessed_by": self.assessed_by_edit.text(),
            "assessment_date": self.assessment_date_edit.date().toString("yyyy-MM-dd"),
            "result": self.result_combo.currentText()
        }

class ViewCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("View Cases")
        self.setFixedSize(1000, 600)
        self.responsibilities = load_responsibilities()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        self.resp_tree = QTreeWidget()
        self.resp_tree.setHeaderLabel("Responsibilities")
        self.resp_tree.itemSelectionChanged.connect(self.on_resp_select)
        splitter.addWidget(self.resp_tree)

        self.case_table = QTableWidget()
        self.case_table.setColumnCount(8)
        self.case_table.setHorizontalHeaderLabels([
            "Trans No", "Date Incurred", "Description", "BAS Payment No",
            "Persal No", "Category", "Amount", "Status"
        ])
        self.case_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        splitter.addWidget(self.case_table)

        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        self.refresh_responsibilities()
        self.refresh_cases()

    def refresh_responsibilities(self):
        self.resp_tree.clear()
        resp_dict = {r["id"]: r for r in self.responsibilities}
        top_level = [r for r in self.responsibilities if r["parent_id"] is None]
        for resp in top_level:
            self.add_resp_item(resp, None, resp_dict)

    def add_resp_item(self, resp, parent_item, resp_dict):
        item = QTreeWidgetItem([resp["name"]])
        item.setData(0, Qt.UserRole, resp["id"])
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

    def refresh_cases(self, resp_ids=None):
        self.case_table.setRowCount(0)
        conn = sqlite3.connect(os.path.join(BASE_DIR, "fruitless.db"))
        cursor = conn.cursor()
        if resp_ids:
            placeholders = ",".join("?" for _ in resp_ids)
            cursor.execute(f"SELECT transaction_no, date_incurred, description, bas_payment_no, persal_no, category, amount, status FROM cases WHERE responsibility_id IN ({placeholders})", resp_ids)
        else:
            cursor.execute("SELECT transaction_no, date_incurred, description, bas_payment_no, persal_no, category, amount, status FROM cases")
        for row_data in cursor.fetchall():
            row = self.case_table.rowCount()
            self.case_table.insertRow(row)
            for col, data in enumerate(row_data):
                self.case_table.setItem(row, col, QTableWidgetItem(str(data)))
        conn.close()

class ManageCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Cases")
        self.setFixedSize(1000, 600)
        self.responsibilities = load_responsibilities()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        self.resp_tree = QTreeWidget()
        self.resp_tree.setHeaderLabel("Responsibilities")
        self.resp_tree.itemSelectionChanged.connect(self.on_resp_select)
        splitter.addWidget(self.resp_tree)

        self.case_table = QTableWidget()
        self.case_table.setColumnCount(9)
        self.case_table.setHorizontalHeaderLabels([
            "Trans No", "Date Incurred", "Description", "BAS Payment No",
            "Persal No", "Category", "Amount", "Status", "Actions"
        ])
        self.case_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        splitter.addWidget(self.case_table)

        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        self.refresh_responsibilities()
        self.refresh_cases()

    def refresh_responsibilities(self):
        self.resp_tree.clear()
        resp_dict = {r["id"]: r for r in self.responsibilities}
        top_level = [r for r in self.responsibilities if r["parent_id"] is None]
        for resp in top_level:
            self.add_resp_item(resp, None, resp_dict)

    def add_resp_item(self, resp, parent_item, resp_dict):
        item = QTreeWidgetItem([resp["name"]])
        item.setData(0, Qt.UserRole, resp["id"])
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

    def refresh_cases(self, resp_ids=None):
        self.case_table.setRowCount(0)
        conn = sqlite3.connect(os.path.join(BASE_DIR, "fruitless.db"))
        cursor = conn.cursor()
        if resp_ids:
            placeholders = ",".join("?" for _ in resp_ids)
            cursor.execute(f"SELECT id, transaction_no, date_incurred, description, bas_payment_no, persal_no, category, amount, status FROM cases WHERE responsibility_id IN ({placeholders})", resp_ids)
        else:
            cursor.execute("SELECT id, transaction_no, date_incurred, description, bas_payment_no, persal_no, category, amount, status FROM cases")
        for row_data in cursor.fetchall():
            row = self.case_table.rowCount()
            self.case_table.insertRow(row)
            for col, data in enumerate(row_data[1:], start=0):
                self.case_table.setItem(row, col, QTableWidgetItem(str(data)))
            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda _, r=row: self.edit_case(row))
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, r=row: self.delete_case(row))
            action_layout = QHBoxLayout()
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            action_widget = QWidget()
            action_widget.setLayout(action_layout)
            self.case_table.setCellWidget(row, 8, action_widget)
        conn.close()

    def edit_case(self, row):
        transaction_no = self.case_table.item(row, 0).text()
        conn = sqlite3.connect(os.path.join(BASE_DIR, "fruitless.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE transaction_no = ?", (transaction_no,))
        case = cursor.fetchone()
        conn.close()
        dialog = AddNewCaseDialog(self)
        dialog.trans_no_edit.setText(case[1])
        dialog.date_incurred_edit.setDate(QDate.fromString(case[2], "yyyy-MM-dd"))
        dialog.date_identified_edit.setDate(QDate.fromString(case[3], "yyyy-MM-dd"))
        dialog.date_reported_edit.setDate(QDate.fromString(case[4], "yyyy-MM-dd"))
        dialog.description_edit.setText(case[5])
        dialog.bas_payment_no_edit.setText(case[6])
        dialog.bas_payment_date_edit.setDate(QDate.fromString(case[7], "yyyy-MM-dd"))
        dialog.persal_no_edit.setText(case[8])
        dialog.category_combo.setCurrentText(case[9])
        resp_index = next(i for i, r in enumerate(self.responsibilities) if r["id"] == case[10])
        dialog.responsibility_combo.setCurrentIndex(resp_index)
        dialog.amount_edit.setText(str(case[11]))
        dialog.evidence_edit.setText(case[14])
        if dialog.exec_():
            self.refresh_cases()

    def delete_case(self, row):
        transaction_no = self.case_table.item(row, 0).text()
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete case {transaction_no}?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = sqlite3.connect(os.path.join(BASE_DIR, "fruitless.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cases WHERE transaction_no = ?", (transaction_no,))
            case_id = cursor.fetchone()[0]
            cursor.execute("DELETE FROM cases WHERE transaction_no = ?", (transaction_no,))
            conn.commit()
            conn.close()
            save_audit_log({
                "timestamp": datetime.now().isoformat(),
                "action": "delete_case",
                "case_id": case_id,
                "transaction_no": transaction_no,
                "details": {}
            }, get_financial_year())
            self.refresh_cases()

class ToDoListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("To-Do List")
        self.setFixedSize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.todo_table = QTableWidget()
        self.todo_table.setColumnCount(5)
        self.todo_table.setHorizontalHeaderLabels(["Trans No", "Description", "Status", "Action", "Due Date"])
        self.todo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.todo_table)
        self.refresh_todo()

    def refresh_todo(self):
        self.todo_table.setRowCount(0)
        conn = sqlite3.connect(os.path.join(BASE_DIR, "fruitless.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT transaction_no, description, status FROM cases WHERE status = 'Alleged'")
        for row_data in cursor.fetchall():
            row = self.todo_table.rowCount()
            self.todo_table.insertRow(row)
            for col, data in enumerate(row_data):
                self.todo_table.setItem(row, col, QTableWidgetItem(str(data)))
            self.todo_table.setItem(row, 3, QTableWidgetItem("Assessment Required"))
            due_date = QDate.currentDate().addDays(7).toString("yyyy-MM-dd")
            self.todo_table.setItem(row, 4, QTableWidgetItem(due_date))
        conn.close()