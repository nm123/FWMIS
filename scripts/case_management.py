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
    QWidget,
    QLabel,
)
from collections import defaultdict
from PyQt5.QtCore import QDate, Qt
from Utilities.utils import (
    BASE_DIR,
    DB_PATH,
    get_financial_year,
    generate_transaction_no,
    create_year_folder,
    save_audit_log,
    get_effective_contacts,
    is_valid_email,
    get_subtree_resp_ids,
    load_categories,
    load_responsibilities,
    load_posting_responsibilities,
    load_lists,
)
import win32com.client

class ResponsibilitySelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Responsibility")
        self.setFixedSize(800, 600)
        self.selected_responsibility = None
        self.setup_ui()
        self.load_responsibilities()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to search responsibilities...")
        self.search_edit.textChanged.connect(self.filter_responsibilities)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Posting Level Responsibilities")
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.tree)

        # Buttons
        button_layout = QHBoxLayout()
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.select_responsibility)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def load_responsibilities(self):
        self.tree.clear()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # First, get all posting level responsibilities
            cursor.execute("SELECT id, name, parent_id, is_posting_level FROM responsibilities WHERE is_posting_level = 1 ORDER BY name")
            posting_resps = [{"id": row[0], "name": row[1], "parent_id": row[2], "is_posting_level": row[3]} for row in cursor.fetchall()]

            # Get all unique parent IDs of posting responsibilities
            parent_ids = set()
            for resp in posting_resps:
                if resp["parent_id"]:
                    parent_ids.add(resp["parent_id"])

            # Load parent responsibilities (even if not posting level)
            parent_resps = []
            if parent_ids:
                placeholders = ",".join("?" for _ in parent_ids)
                cursor.execute(f"SELECT id, name, parent_id, is_posting_level FROM responsibilities WHERE id IN ({placeholders})", list(parent_ids))
                parent_resps = [{"id": row[0], "name": row[1], "parent_id": row[2], "is_posting_level": row[3]} for row in cursor.fetchall()]

            # Combine all responsibilities
            self.responsibilities = parent_resps + posting_resps
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load responsibilities: {e}")
            return

        print(f"DEBUG: Loaded {len(self.responsibilities)} total responsibilities")
        for resp in self.responsibilities:
            print(f"DEBUG: {resp['name']} (id: {resp['id']}, parent: {resp['parent_id']}, posting: {resp['is_posting_level']})")

        parent_map = defaultdict(list)
        for resp in self.responsibilities:
            parent_map[resp["parent_id"]].append(resp)

        def add_items(parent_item, parent_id):
            for resp in sorted(parent_map[parent_id], key=lambda x: x["name"]):
                item = QTreeWidgetItem([resp["name"]])
                item.setData(0, Qt.UserRole, resp["id"])
                item.setData(1, Qt.UserRole, resp["is_posting_level"])  # Store posting level status

                # Visual styling for non-posting items
                if resp["is_posting_level"] == 0:
                    font = item.font(0)
                    font.setItalic(True)
                    item.setFont(0, font)
                    item.setToolTip(0, "Non-posting level responsibility - cannot be selected")
                else:
                    item.setToolTip(0, "Posting level responsibility - can be selected")

                if parent_id is None:
                    self.tree.addTopLevelItem(item)
                    print(f"DEBUG: Added top-level item: {resp['name']} (posting: {resp['is_posting_level']})")
                else:
                    parent_item.addChild(item)
                    print(f"DEBUG: Added child item: {resp['name']} to {parent_item.text(0)} (posting: {resp['is_posting_level']})")
                add_items(item, resp["id"])

        add_items(None, None)
        self.tree.expandAll()

        print(f"DEBUG: Tree has {self.tree.topLevelItemCount()} top-level items")
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            print(f"DEBUG: Top-level item {i}: {item.text(0)}")
            for j in range(item.childCount()):
                child = item.child(j)
                print(f"DEBUG:   Child {j}: {child.text(0)}")

    def filter_responsibilities(self, text):
        text = text.lower()
        if not text:
            self.load_responsibilities()
            return

        self.tree.clear()

        # Find responsibilities that match the search text
        matching_resps = []
        parent_ids_to_include = set()

        for resp in self.responsibilities:
            if text in resp["name"].lower():
                matching_resps.append(resp)
                # Also include the parent if it exists
                if resp["parent_id"]:
                    parent_ids_to_include.add(resp["parent_id"])

        # Include parent responsibilities
        for resp in self.responsibilities:
            if resp["id"] in parent_ids_to_include:
                matching_resps.append(resp)

        # Remove duplicates while preserving order
        seen_ids = set()
        filtered_resps = []
        for resp in matching_resps:
            if resp["id"] not in seen_ids:
                filtered_resps.append(resp)
                seen_ids.add(resp["id"])

        # Create parent map for filtered results
        parent_map = defaultdict(list)
        for resp in filtered_resps:
            parent_map[resp["parent_id"]].append(resp)

        def add_filtered_items(parent_item, parent_id):
            for resp in sorted(parent_map[parent_id], key=lambda x: x["name"]):
                item = QTreeWidgetItem([resp["name"]])
                item.setData(0, Qt.UserRole, resp["id"])
                item.setData(1, Qt.UserRole, resp["is_posting_level"])

                # Visual styling for non-posting items
                if resp["is_posting_level"] == 0:
                    font = item.font(0)
                    font.setItalic(True)
                    item.setFont(0, font)
                    item.setToolTip(0, "Non-posting level responsibility - cannot be selected")
                else:
                    item.setToolTip(0, "Posting level responsibility - can be selected")

                if parent_id is None:
                    self.tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                add_filtered_items(item, resp["id"])

        add_filtered_items(None, None)
        self.tree.expandAll()

    def on_item_double_clicked(self, item, column):
        """Handle double-click on tree item with validation"""
        self.select_responsibility()

    def select_responsibility(self):
        try:
            selected_item = self.tree.currentItem()
            if not selected_item:
                QMessageBox.warning(self, "No Selection", "Please select a responsibility from the tree first.")
                return

            is_posting = selected_item.data(1, Qt.UserRole)  # Get posting level status
            print(f"DEBUG: Selected item posting level: {is_posting}")

            if is_posting == 1:
                resp_id = selected_item.data(0, Qt.UserRole)
                resp_name = selected_item.text(0)
                print(f"DEBUG: Selected responsibility: {resp_name} (ID: {resp_id})")

                if resp_id is None:
                    QMessageBox.critical(self, "Error", "Selected responsibility has no ID.")
                    return

                self.selected_responsibility = {"id": resp_id, "name": resp_name}
                print(f"DEBUG: Accepting selection: {self.selected_responsibility}")
                self.accept()
            else:
                QMessageBox.warning(self, "Invalid Selection",
                                  "You can only select posting level responsibilities.\n\n"
                                  "Non-posting level responsibilities are shown in italics and cannot be selected.")
        except Exception as e:
            print(f"DEBUG: Exception in select_responsibility: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while selecting the responsibility:\n\n{str(e)}")

    def get_selected_responsibility(self):
        return self.selected_responsibility

class AddNewCaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Case")
        self.setFixedSize(1200, 900)
        try:
            self.responsibilities = load_posting_responsibilities()
            self.categories = load_categories()
            self.lists = load_lists()
            self.fy = get_financial_year()
            self.transaction_no = None  # Will be generated when saving
            self.selected_responsibility_id = None
            self.setup_ui()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize Add New Case dialog: {str(e)}")
            self.reject()


    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Case No (first)
        self.trans_no_edit = QLineEdit("To be assigned")
        self.trans_no_edit.setReadOnly(True)
        form_layout.addRow("Case No:", self.trans_no_edit)

        # Responsibility (moved up, second) - now using selection dialog
        responsibility_layout = QHBoxLayout()
        self.responsibility_edit = QLineEdit()
        self.responsibility_edit.setReadOnly(True)
        self.responsibility_edit.setPlaceholderText("Click Select to choose responsibility...")
        responsibility_layout.addWidget(self.responsibility_edit)

        self.select_responsibility_button = QPushButton("Select")
        self.select_responsibility_button.clicked.connect(self.select_responsibility)
        responsibility_layout.addWidget(self.select_responsibility_button)

        form_layout.addRow("Responsibility:", responsibility_layout)

        # Date fields (horizontal layout)
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date Incurred:"))
        self.date_incurred_edit = QDateEdit(QDate.currentDate())
        self.date_incurred_edit.setCalendarPopup(True)
        self.date_incurred_edit.setFixedWidth(120)
        date_layout.addWidget(self.date_incurred_edit)

        date_layout.addSpacing(20)
        date_layout.addWidget(QLabel("Date Identified:"))
        self.date_identified_edit = QDateEdit(QDate.currentDate())
        self.date_identified_edit.setCalendarPopup(True)
        self.date_identified_edit.setFixedWidth(120)
        date_layout.addWidget(self.date_identified_edit)

        date_layout.addSpacing(20)
        date_layout.addWidget(QLabel("Date Reported:"))
        self.date_reported_edit = QDateEdit(QDate.currentDate())
        self.date_reported_edit.setCalendarPopup(True)
        self.date_reported_edit.setFixedWidth(120)
        date_layout.addWidget(self.date_reported_edit)

        date_layout.addStretch()
        form_layout.addRow(date_layout)

        # Description (larger for paragraphs)
        self.description_edit = QTextEdit()
        self.description_edit.setMinimumHeight(80)  # Make it bigger for paragraphs
        form_layout.addRow("Description:", self.description_edit)

        # Category (moved down)
        self.category_combo = QComboBox()
        self.category_combo.addItems([c["name"] for c in self.categories])
        self.category_combo.currentIndexChanged.connect(self.update_conditional_fields)
        form_layout.addRow("Category:", self.category_combo)

        # List (only show Checklist and Lead Schedule)
        self.list_combo = QComboBox()
        system_lists = [l["name"] for l in self.lists if l.get("is_system", False) and l["name"] != "Deleted Cases"]
        self.list_combo.addItems(system_lists)
        # Select default list
        default_list = next((l for l in self.lists if l.get("is_default", False)), None)
        if default_list and default_list["name"] in system_lists:
            self.list_combo.setCurrentText(default_list["name"])
        self.list_combo.currentTextChanged.connect(self.update_conditional_fields)
        form_layout.addRow("List:", self.list_combo)

        # Status (moved here, right below List)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Alleged", "Under Assessment", "Valid", "Confirmed"])
        self.status_combo.setCurrentText("Alleged")  # Default to Alleged
        self.status_combo.currentTextChanged.connect(self.update_conditional_fields)
        form_layout.addRow("Status:", self.status_combo)

        # Criminal Charges Laid
        self.criminal_charges_combo = QComboBox()
        self.criminal_charges_combo.addItems(["N/A", "Yes", "No"])
        self.criminal_charges_combo.setCurrentText("N/A")
        form_layout.addRow("Criminal Charges Laid:", self.criminal_charges_combo)

        # Disciplinary process
        self.disciplinary_combo = QComboBox()
        self.disciplinary_combo.addItems(["N/A", "Yes", "No"])
        self.disciplinary_combo.setCurrentText("N/A")
        form_layout.addRow("Disciplinary process in progress or completed:", self.disciplinary_combo)

        # Loss recovery
        self.loss_recovery_combo = QComboBox()
        self.loss_recovery_combo.addItems(["N/A", "Yes", "No"])
        self.loss_recovery_combo.setCurrentText("N/A")
        form_layout.addRow("Loss recovery commenced or completed:", self.loss_recovery_combo)

        # Steps to prevent future occurrence
        self.prevention_steps_edit = QTextEdit()
        self.prevention_steps_edit.setMinimumHeight(80)  # Make it bigger for paragraphs
        form_layout.addRow("Steps taken to prevent future occurrence of F&W expenditure:", self.prevention_steps_edit)

        # Amount
        self.amount_edit = QLineEdit()
        form_layout.addRow("Amount:", self.amount_edit)

        # BAS Payment fields
        self.bas_label = QLabel("BAS Payment No:")
        self.bas_payment_no_edit = QLineEdit()
        form_layout.addRow(self.bas_label, self.bas_payment_no_edit)

        self.bas_date_label = QLabel("BAS Payment Date:")
        self.bas_payment_date_edit = QDateEdit(QDate.currentDate())
        self.bas_payment_date_edit.setCalendarPopup(True)
        form_layout.addRow(self.bas_date_label, self.bas_payment_date_edit)

        # Persal No field
        self.persal_label = QLabel("Persal No:")
        self.persal_no_edit = QLineEdit()
        form_layout.addRow(self.persal_label, self.persal_no_edit)

        # File selection fields (conditional)
        self.source_doc_label = QLabel("Source Document:")
        self.source_doc_edit = QLineEdit()
        self.source_doc_button = QPushButton("Browse")
        self.source_doc_button.clicked.connect(self.browse_source_doc)
        source_doc_layout = QHBoxLayout()
        source_doc_layout.addWidget(self.source_doc_edit)
        source_doc_layout.addWidget(self.source_doc_button)
        form_layout.addRow(self.source_doc_label, source_doc_layout)

        self.minutes_label = QLabel("Loss Control Minutes:")
        self.minutes_edit = QLineEdit()
        self.minutes_button = QPushButton("Browse")
        self.minutes_button.clicked.connect(self.browse_minutes)
        minutes_layout = QHBoxLayout()
        minutes_layout.addWidget(self.minutes_edit)
        minutes_layout.addWidget(self.minutes_button)
        form_layout.addRow(self.minutes_label, minutes_layout)

        self.evidence_label = QLabel("Assessment Evidence:")
        self.evidence_edit = QLineEdit()
        self.evidence_button = QPushButton("Browse")
        self.evidence_button.clicked.connect(self.browse_evidence)
        evidence_layout = QHBoxLayout()
        evidence_layout.addWidget(self.evidence_edit)
        evidence_layout.addWidget(self.evidence_button)
        form_layout.addRow(self.evidence_label, evidence_layout)


        # Other fields - Status moved above

        # Assessment fields (conditional)
        self.assessed_by_label = QLabel("Assessed By:")
        self.assessed_by_edit = QLineEdit()
        form_layout.addRow(self.assessed_by_label, self.assessed_by_edit)

        self.assessment_date_label = QLabel("Assessment Date:")
        self.assessment_date_edit = QDateEdit(QDate.currentDate())
        self.assessment_date_edit.setCalendarPopup(True)
        form_layout.addRow(self.assessment_date_label, self.assessment_date_edit)

        layout.addLayout(form_layout)

        # Initial update of conditional fields
        self.update_conditional_fields()

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save & Continue")
        self.save_button.clicked.connect(self.save_case)
        self.save_close_button = QPushButton("Save & Close")
        self.save_close_button.clicked.connect(self.save_case_and_close)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.save_close_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def select_responsibility(self):
        dialog = ResponsibilitySelectionDialog(self)
        if dialog.exec_():
            selected = dialog.get_selected_responsibility()
            if selected:
                self.responsibility_edit.setText(selected["name"])
                self.selected_responsibility_id = selected["id"]

    def update_conditional_fields(self):
        """Update visibility of conditional fields based on list and status selection"""
        selected_list = self.list_combo.currentText()
        selected_status = self.status_combo.currentText()

        # Show assessment fields only for Lead Schedule + Valid/Confirmed status
        show_assessment_fields = (selected_list == "Lead Schedule" and
                                selected_status in ["Valid", "Confirmed"])

        # Update visibility of assessment-related fields
        self.source_doc_label.setVisible(show_assessment_fields)
        self.source_doc_edit.setVisible(show_assessment_fields)
        self.source_doc_button.setVisible(show_assessment_fields)

        self.minutes_label.setVisible(show_assessment_fields)
        self.minutes_edit.setVisible(show_assessment_fields)
        self.minutes_button.setVisible(show_assessment_fields)

        self.evidence_label.setVisible(show_assessment_fields)
        self.evidence_edit.setVisible(show_assessment_fields)
        self.evidence_button.setVisible(show_assessment_fields)

        self.assessed_by_label.setVisible(show_assessment_fields)
        self.assessed_by_edit.setVisible(show_assessment_fields)

        self.assessment_date_label.setVisible(show_assessment_fields)
        self.assessment_date_edit.setVisible(show_assessment_fields)

        # Update compulsory fields based on category
        selected_category = self.category_combo.currentText()
        if selected_category:
            category = next((c for c in self.categories if c["name"] == selected_category), None)
            if category:
                bas_comp = category.get("bas_payment_compulsory", False)
                persal_comp = category.get("persal_compulsory", False)
            else:
                bas_comp = False
                persal_comp = False
        else:
            bas_comp = False
            persal_comp = False

        # Update BAS fields
        self.bas_label.setText("BAS Payment No:" + (" *" if bas_comp else ""))
        self.bas_label.setVisible(bas_comp)
        self.bas_payment_no_edit.setVisible(bas_comp)
        self.bas_date_label.setVisible(bas_comp)
        self.bas_payment_date_edit.setVisible(bas_comp)

        # Update Persal field
        self.persal_label.setText("Persal No:" + (" *" if persal_comp else ""))
        self.persal_label.setVisible(persal_comp)
        self.persal_no_edit.setVisible(persal_comp)

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
            print("DEBUG: Starting save_case method")
            bas_payment_no = self.bas_payment_no_edit.text().strip()
            persal_no = self.persal_no_edit.text().strip()
            amount_text = self.amount_edit.text().strip()
            print(f"DEBUG: bas_payment_no='{bas_payment_no}', persal_no='{persal_no}', amount_text='{amount_text}'")

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
            missing_fields = []
            if bas_comp and not bas_payment_no:
                missing_fields.append("BAS Payment No")
            if persal_comp and not persal_no:
                missing_fields.append("Persal No")
            if not amount_text:
                missing_fields.append("Amount")

            if missing_fields:
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

            # Generate transaction number only when saving
            self.transaction_no = generate_transaction_no(self.fy)
            self.trans_no_edit.setText(self.transaction_no)
            print(f"DEBUG: Generated transaction_no: {self.transaction_no}")

            # Convert dates to strings explicitly with error checking
            try:
                date_incurred_str = self.date_incurred_edit.date().toString("yyyy-MM-dd")
                date_identified_str = self.date_identified_edit.date().toString("yyyy-MM-dd")
                date_reported_str = self.date_reported_edit.date().toString("yyyy-MM-dd")
                bas_payment_date_str = self.bas_payment_date_edit.date().toString("yyyy-MM-dd")
                assessment_date_str = self.assessment_date_edit.date().toString("yyyy-MM-dd")
                print(f"DEBUG: Date conversions successful")
            except Exception as e:
                print(f"DEBUG: Date conversion error: {e}")
                raise

            # Create case dictionary with error checking
            try:
                category_text = self.category_combo.currentText()
                status_text = self.status_combo.currentText()
                list_text = self.list_combo.currentText()
                criminal_charges_text = self.criminal_charges_combo.currentText()
                disciplinary_text = self.disciplinary_combo.currentText()
                loss_recovery_text = self.loss_recovery_combo.currentText()

                print(f"DEBUG: Combo box values - category: '{category_text}', status: '{status_text}', list: '{list_text}'")
                print(f"DEBUG: Combo box values - criminal: '{criminal_charges_text}', disciplinary: '{disciplinary_text}', loss: '{loss_recovery_text}'")

                case = {
                    "transaction_no": self.transaction_no,
                    "date_incurred": str(date_incurred_str),
                    "date_identified": str(date_identified_str),
                    "date_reported": str(date_reported_str),
                    "description": self.description_edit.toPlainText().strip(),
                    "bas_payment_no": bas_payment_no,
                    "bas_payment_date": str(bas_payment_date_str),
                    "persal_no": persal_no,
                    "category": category_text,
                    "responsibility_id": self.selected_responsibility_id,
                    "amount": amount,
                    "source_document": self.source_doc_edit.text().strip(),
                    "minutes": self.minutes_edit.text().strip(),
                    "evidence_path": self.evidence_edit.text().strip(),
                    "attachments": "[]",
                    "status": status_text,
                    "list": list_text,
                    "assessment_assessed_by": self.assessed_by_edit.text().strip(),
                    "assessment_date": str(assessment_date_str),
                    "assessment_result": "",  # Removed field
                    "criminal_charges": criminal_charges_text,
                    "disciplinary_process": disciplinary_text,
                    "loss_recovery": loss_recovery_text,
                    "prevention_steps": self.prevention_steps_edit.toPlainText().strip(),
                    "fy_id": None,  # Add missing fields
                    "period_id": None,
                    "original_list": list_text
                }
                print(f"DEBUG: Case dictionary created successfully with {len(case)} fields")
                print(f"DEBUG: Case dict keys: {list(case.keys())}")
            except Exception as e:
                print(f"DEBUG: Error creating case dictionary: {e}")
                raise
            # Handle file operations with error checking
            try:
                year_folder = create_year_folder(self.fy)
                print(f"DEBUG: Year folder: {year_folder}")
                for field in ["source_document", "minutes", "evidence_path"]:
                    if case[field]:
                        print(f"DEBUG: Processing file field: {field} = '{case[field]}'")
                        dest_path = os.path.join(year_folder, f"{self.transaction_no}_{field}.pdf")
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        os.replace(case[field], dest_path)
                        case[field] = dest_path
                        print(f"DEBUG: Successfully moved {field} to {dest_path}")
                    else:
                        print(f"DEBUG: No file for {field}")
            except Exception as e:
                print(f"DEBUG: File operation error: {e}")
                raise
            print("DEBUG: About to connect to database")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            print("DEBUG: Database connection established")

            print("DEBUG: About to execute INSERT statement")
            try:
                cursor.execute("""
                    INSERT INTO cases (
                        transaction_no, date_incurred, date_identified, date_reported, description,
                        bas_payment_no, bas_payment_date, persal_no, category, responsibility_id, amount,
                        source_document, minutes, evidence_path, attachments, status, list, assessment_assessed_by,
                        assessment_date, assessment_result, fy_id, period_id, criminal_charges, disciplinary_process,
                        loss_recovery, prevention_steps, original_list
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    case["transaction_no"], case["date_incurred"], case["date_identified"], case["date_reported"],
                    case["description"], case["bas_payment_no"], case["bas_payment_date"], case["persal_no"],
                    case["category"], case["responsibility_id"], case["amount"], case["source_document"],
                    case["minutes"], case["evidence_path"], case["attachments"], case["status"], case["list"],
                    case["assessment_assessed_by"], case["assessment_date"], case["assessment_result"],
                    case["fy_id"], case["period_id"],  # Use values from case dict
                    case["criminal_charges"], case["disciplinary_process"], case["loss_recovery"],
                    case["prevention_steps"], case["original_list"]  # Use value from case dict
                ))
                print("DEBUG: INSERT statement executed successfully")
            except Exception as e:
                print(f"DEBUG: INSERT statement failed: {e}")
                print(f"DEBUG: Exception type: {type(e)}")
                raise
            conn.commit()
            case_id = cursor.lastrowid
            conn.close()
            save_audit_log("add_case", {
                "timestamp": datetime.now().isoformat(),
                "case_id": case_id,
                "transaction_no": self.transaction_no,
                "details": case
            }, self.fy)
            QMessageBox.information(self, "Success", "Case added successfully.")
            self.reset_form_for_next_case()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save case: {str(e)}")
            self.reject()

    def save_case_and_close(self):
        """Save the case and close the dialog"""
        self.save_case()
        self.accept()

    def reset_form_for_next_case(self):
        """Reset the form for entering the next case"""
        # Generate new transaction number
        self.transaction_no = generate_transaction_no(self.fy)
        self.trans_no_edit.setText(self.transaction_no)

        # Clear text fields
        self.description_edit.clear()
        self.bas_payment_no_edit.clear()
        self.persal_no_edit.clear()
        self.amount_edit.clear()
        self.evidence_edit.clear()
        self.source_doc_edit.clear()
        self.minutes_edit.clear()
        self.assessed_by_edit.clear()

        # Reset combo boxes to defaults
        self.status_combo.setCurrentText("Alleged")
        self.criminal_charges_combo.setCurrentText("N/A")
        self.disciplinary_combo.setCurrentText("N/A")
        self.loss_recovery_combo.setCurrentText("N/A")
        self.prevention_steps_edit.clear()

        # Reset dates to current date
        current_date = QDate.currentDate()
        self.date_incurred_edit.setDate(current_date)
        self.date_identified_edit.setDate(current_date)
        self.date_reported_edit.setDate(current_date)
        self.bas_payment_date_edit.setDate(current_date)
        self.assessment_date_edit.setDate(current_date)

        # Clear responsibility selection
        self.responsibility_edit.clear()
        self.selected_responsibility_id = None

        # Clear attachments (keeping empty array for database)
        pass

        # Reset focus to first field
        self.responsibility_edit.setFocus()

    def next_case(self):
        # Generate new transaction number for next case
        self.transaction_no = generate_transaction_no(self.fy)
        self.trans_no_edit.setText(self.transaction_no)
        self.description_edit.clear()
        self.bas_payment_no_edit.clear()
        self.persal_no_edit.clear()
        self.amount_edit.clear()
        self.evidence_edit.clear()
        self.criminal_charges_combo.setCurrentText("N/A")
        self.disciplinary_combo.setCurrentText("N/A")
        self.loss_recovery_combo.setCurrentText("N/A")
        self.prevention_steps_edit.clear()
        # Reset list combo to default
        default_list = next((l for l in self.lists if l.get("is_default", False)), None)
        if default_list:
            self.list_combo.setCurrentText(default_list["name"])
        else:
            self.list_combo.setCurrentIndex(0)

    def send_reminder_email(self):
        resp_id = self.responsibilities[self.responsibility_combo.currentIndex()]["id"]
        contacts = get_effective_contacts(self.responsibilities, resp_id)
        emails = [c["email"] for c in contacts if is_valid_email(c["email"])]
        if not emails:
            QMessageBox.warning(self, "No Contacts", "No valid email contacts found for this responsibility.")
            return

        conn = sqlite3.connect(DB_PATH)
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
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM cases")
            max_id = cursor.fetchone()[0]
            case_id = (max_id or 0) + 1
            cursor.execute("UPDATE cases SET assessment_assessed_by = ?, assessment_date = ?, assessment_result = ?, status = ?, list = ? WHERE transaction_no = ?",
                           (assessment_data["assessed_by"], assessment_data["assessment_date"], assessment_data["result"], assessment_data["result"], "Lead Schedule", self.transaction_no))
            conn.commit()
            conn.close()
            save_audit_log("assess_case", {
                "timestamp": datetime.now().isoformat(),
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
            "Case No", "Date Incurred", "Description", "BAS Payment No",
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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if resp_ids:
            placeholders = ",".join("?" for _ in resp_ids)
            query = f"SELECT transaction_no, date_incurred, description, bas_payment_no, persal_no, category, amount, status FROM cases WHERE responsibility_id IN ({placeholders})"
            cursor.execute(query, resp_ids)
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
        self.current_list = "Checklist"  # Default context
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
            "Case No", "Date Incurred", "Description", "BAS Payment No",
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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Build query based on current list context
        base_query = """
            SELECT id, transaction_no, date_incurred, description, bas_payment_no, persal_no, category, amount, status, list
            FROM cases
            WHERE 1=1
        """
        params = []

        if resp_ids:
            placeholders = ",".join("?" for _ in resp_ids)
            base_query += f" AND responsibility_id IN ({placeholders})"
            params.extend(resp_ids)

        # If we're viewing Checklist, also include Confirmed cases from Lead Schedule
        # This simulates showing cases in multiple lists
        if hasattr(self, 'current_list') and self.current_list == "Checklist":
            base_query += " AND (list = 'Checklist' OR (list = 'Lead Schedule' AND status = 'Confirmed'))"
        else:
            base_query += " AND list = 'Checklist'"  # Default to Checklist if no context

        cursor.execute(base_query, params)

        for row_data in cursor.fetchall():
            row = self.case_table.rowCount()
            self.case_table.insertRow(row)
            # Display data (skip id and list columns for display)
            for col, data in enumerate(row_data[1:-1], start=0):  # Skip id (0) and list (-1)
                self.case_table.setItem(row, col, QTableWidgetItem(str(data)))

            case_id = row_data[0]
            case_list = row_data[-1]
            case_status = row_data[8]

            # Create action buttons
            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda _, r=row, cid=case_id: self.edit_case_by_id(cid))
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, r=row, cid=case_id: self.delete_case_by_id(cid))

            # Disable edit/delete for cases from Lead Schedule when viewed in Checklist
            if case_list == "Lead Schedule" and case_status == "Confirmed":
                edit_button.setEnabled(False)
                edit_button.setToolTip("This case is locked. Edit from Lead Schedule.")
                delete_button.setEnabled(False)
                delete_button.setToolTip("This case is locked. Delete from Lead Schedule.")

            action_layout = QHBoxLayout()
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            action_widget = QWidget()
            action_widget.setLayout(action_layout)
            self.case_table.setCellWidget(row, 8, action_widget)

        conn.close()

    def edit_case_by_id(self, case_id):
        """Edit case by database ID"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
            case = cursor.fetchone()
            conn.close()

            if case:
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
                # Set responsibility
                resp = next((r for r in dialog.responsibilities if r["id"] == case[10]), None)
                if resp:
                    dialog.responsibility_edit.setText(resp["name"])
                    dialog.selected_responsibility_id = resp["id"]
                dialog.amount_edit.setText(str(case[11]))
                dialog.evidence_edit.setText(case[14])
                dialog.list_combo.setCurrentText(case[16])
                dialog.status_combo.setCurrentText(case[17])
                dialog.criminal_charges_combo.setCurrentText(case[22] if len(case) > 22 else "N/A")
                dialog.disciplinary_combo.setCurrentText(case[23] if len(case) > 23 else "N/A")
                dialog.loss_recovery_combo.setCurrentText(case[24] if len(case) > 24 else "N/A")
                dialog.prevention_steps_edit.setText(case[25] if len(case) > 25 else "")
                if dialog.exec_():
                    self.refresh_cases()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to load case: {str(e)}")

    def delete_case_by_id(self, case_id):
        """Delete case by database ID"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT transaction_no, list FROM cases WHERE id = ?", (case_id,))
            case_data = cursor.fetchone()
            conn.close()

            if case_data:
                transaction_no, current_list = case_data
                reply = QMessageBox.question(
                    self, "Confirm Move to Deleted Cases",
                    f"Move case {transaction_no} to Deleted Cases?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE cases SET list = 'Deleted Cases', original_list = ? WHERE id = ?", (current_list, case_id))
                    conn.commit()
                    conn.close()
                    QMessageBox.information(self, "Success", "Case moved to Deleted Cases.")
                    self.refresh_cases()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to delete case: {str(e)}")

    def edit_case(self, row):
        transaction_no = self.case_table.item(row, 0).text()
        conn = sqlite3.connect(DB_PATH)
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
        # Set responsibility
        resp = next((r for r in dialog.responsibilities if r["id"] == case[10]), None)
        if resp:
            dialog.responsibility_edit.setText(resp["name"])
            dialog.selected_responsibility_id = resp["id"]
        dialog.amount_edit.setText(str(case[11]))
        dialog.evidence_edit.setText(case[14])
        dialog.list_combo.setCurrentText(case[16])  # list field
        dialog.status_combo.setCurrentText(case[17])  # status field
        dialog.criminal_charges_combo.setCurrentText(case[22] if len(case) > 22 else "N/A")
        dialog.disciplinary_combo.setCurrentText(case[23] if len(case) > 23 else "N/A")
        dialog.loss_recovery_combo.setCurrentText(case[24] if len(case) > 24 else "N/A")
        dialog.prevention_steps_edit.setText(case[25] if len(case) > 25 else "")
        if dialog.exec_():
            # Check if status changed to Confirmed and move to Lead Schedule
            new_status = dialog.status_combo.currentText()
            if new_status == "Confirmed" and case[16] != "Confirmed":
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    # Store original list and move to Lead Schedule
                    cursor.execute("UPDATE cases SET list = 'Lead Schedule', original_list = ? WHERE transaction_no = ?", (case[15], transaction_no))
                    conn.commit()
                    conn.close()
                    QMessageBox.information(self, "Case Moved", "Case status changed to Confirmed and moved to Lead Schedule for follow-up action.")
                except sqlite3.Error as e:
                    QMessageBox.warning(self, "Warning", f"Case status updated but failed to move to Lead Schedule: {str(e)}")
            self.refresh_cases()

    def delete_case(self, row):
        transaction_no = self.case_table.item(row, 0).text()
        reply = QMessageBox.question(self, "Confirm Move to Deleted Cases", f"Move case {transaction_no} to Deleted Cases?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT id, list FROM cases WHERE transaction_no = ?", (transaction_no,))
                case_data = cursor.fetchone()
                case_id = case_data[0]
                original_list = case_data[1]
                cursor.execute("UPDATE cases SET list = 'Deleted Cases', original_list = ? WHERE transaction_no = ?", (original_list, transaction_no))
                conn.commit()
                conn.close()
                save_audit_log("move_to_deleted_cases", {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": case_id,
                    "transaction_no": transaction_no,
                    "details": {"original_list": original_list}
                }, get_financial_year())
                QMessageBox.information(self, "Success", "Case moved to Deleted Cases.")
                self.refresh_cases()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to move case: {str(e)}")

class ViewDeletedCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Deleted Cases")
        self.setFixedSize(1000, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.case_table = QTableWidget()
        self.case_table.setColumnCount(8)
        self.case_table.setHorizontalHeaderLabels([
            "Case No", "Date Incurred", "Description", "BAS Payment No",
            "Persal No", "Category", "Amount", "Status"
        ])
        self.case_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.case_table)

        # Add restore and permanent delete buttons
        button_layout = QHBoxLayout()
        self.restore_button = QPushButton("Restore Selected Case")
        self.restore_button.clicked.connect(self.restore_case)
        button_layout.addWidget(self.restore_button)

        self.permanent_delete_button = QPushButton("Permanently Delete Selected Case")
        self.permanent_delete_button.clicked.connect(self.permanent_delete_case)
        self.permanent_delete_button.setStyleSheet("QPushButton { color: red; }")
        button_layout.addWidget(self.permanent_delete_button)

        layout.addLayout(button_layout)
        self.refresh_cases()

    def refresh_cases(self):
        self.case_table.setRowCount(0)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT transaction_no, date_incurred, description, bas_payment_no, persal_no, category, amount, status FROM cases WHERE list = 'Deleted Cases'")
        for row_data in cursor.fetchall():
            row = self.case_table.rowCount()
            self.case_table.insertRow(row)
            for col, data in enumerate(row_data):
                self.case_table.setItem(row, col, QTableWidgetItem(str(data)))
        conn.close()

    def restore_case(self):
        selected_row = self.case_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a case to restore.")
            return

        transaction_no = self.case_table.item(selected_row, 0).text()

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT original_list, status FROM cases WHERE transaction_no = ?", (transaction_no,))
            case_data = cursor.fetchone()
            original_list = case_data[0] if case_data else None
            current_status = case_data[1] if case_data else None

            if not original_list:
                original_list = "Checklist"  # Default fallback

            restore_message = f"Restore case {transaction_no} to {original_list}?"
            if original_list == "Lead Schedule" and current_status == "Confirmed":
                restore_message += "\n\nNote: Confirmed cases will be restored to both Checklist and Lead Schedule."

            reply = QMessageBox.question(
                self, "Confirm Restore",
                restore_message,
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                if original_list == "Lead Schedule" and current_status == "Confirmed":
                    # For Confirmed cases from Lead Schedule, restore to both lists
                    cursor.execute("UPDATE cases SET list = 'Checklist', original_list = NULL WHERE transaction_no = ?", (transaction_no,))
                    # Note: In a real implementation, you might want to create a duplicate record for Lead Schedule
                    # For now, we'll restore to Checklist and the case will be visible in both through UI logic
                else:
                    # Restore to original list
                    cursor.execute("UPDATE cases SET list = ?, original_list = NULL WHERE transaction_no = ?", (original_list, transaction_no))

                conn.commit()
                conn.close()
                QMessageBox.information(self, "Success", f"Case restored to {original_list}.")
                self.refresh_cases()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to restore case: {str(e)}")

    def permanent_delete_case(self):
        selected_row = self.case_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a case to permanently delete.")
            return

        transaction_no = self.case_table.item(selected_row, 0).text()
        reply = QMessageBox.question(
            self, "Confirm Permanent Delete",
            f"Permanently delete case {transaction_no}? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cases WHERE transaction_no = ?", (transaction_no,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Success", "Case permanently deleted.")
                self.refresh_cases()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to delete case: {str(e)}")


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
        self.todo_table.setHorizontalHeaderLabels(["Case No", "Description", "Status", "Action", "Due Date"])
        self.todo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.todo_table)
        self.refresh_todo()

    def refresh_todo(self):
        self.todo_table.setRowCount(0)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT transaction_no, description, status FROM cases WHERE status = 'Awaiting Evidence'")
        for row_data in cursor.fetchall():
            row = self.todo_table.rowCount()
            self.todo_table.insertRow(row)
            for col, data in enumerate(row_data):
                self.todo_table.setItem(row, col, QTableWidgetItem(str(data)))
            self.todo_table.setItem(row, 3, QTableWidgetItem("Assessment Required"))
            due_date = QDate.currentDate().addDays(7).toString("yyyy-MM-dd")
            self.todo_table.setItem(row, 4, QTableWidgetItem(due_date))
        conn.close()