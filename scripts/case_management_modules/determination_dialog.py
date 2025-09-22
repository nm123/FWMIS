import json
import sqlite3
from datetime import datetime

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDateEdit, QDialog,
                             QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QMessageBox, QPushButton, QTextEdit, QVBoxLayout)
from scripts.Utilities.audit_utils import save_audit_log
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.utils import format_currency_amount


class DeterminationDialog(QDialog):
    def __init__(self, case_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loss Control Committee Determination")
        self.setFixedSize(800, 700)
        self.case_data = case_data
        self.transaction_no = case_data[1]
        self.fy = get_financial_year()
        self.committee_members = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Case Information Section
        case_group = QGroupBox("Case Information")
        case_layout = QFormLayout(case_group)

        case_layout.addRow("Case No:", QLabel(self.transaction_no))
        case_layout.addRow(
            "Category:", QLabel(self.case_data[9] if self.case_data[9] else "N/A")
        )
        case_layout.addRow(
            "Amount:",
            QLabel(
                format_currency_amount(self.case_data[11])
                if self.case_data[11]
                else "N/A"
            ),
        )
        case_layout.addRow(
            "Status:", QLabel(self.case_data[17] if self.case_data[17] else "N/A")
        )

        layout.addWidget(case_group)

        # Determination Section
        determination_group = QGroupBox("Determination Details")
        determination_layout = QFormLayout(determination_group)

        # Exact Amount Determined
        self.determined_amount_edit = QLineEdit()
        self.determined_amount_edit.setPlaceholderText(
            "Enter exact F&W amount determined"
        )
        if self.case_data[11]:  # Pre-populate with current amount
            self.determined_amount_edit.setText(str(self.case_data[11]))
        determination_layout.addRow(
            "Exact Amount Determined (R):", self.determined_amount_edit
        )

        # Determination Date
        self.determination_date_edit = QDateEdit(QDate.currentDate())
        self.determination_date_edit.setCalendarPopup(True)
        determination_layout.addRow("Determination Date:", self.determination_date_edit)

        layout.addWidget(determination_group)

        # Committee Recommendations Section
        recommendations_group = QGroupBox("Committee Recommendations")
        recommendations_layout = QVBoxLayout(recommendations_group)

        # Recommendation checkboxes
        self.criminal_charges_cb = QCheckBox(
            "Criminal Charges must be laid against the person responsible"
        )
        self.disciplinary_cb = QCheckBox(
            "Disciplinary action needs to be taken against the culprit"
        )
        self.loss_recovery_cb = QCheckBox(
            "The loss must be recovered from the person responsible"
        )
        self.write_off_cb = QCheckBox("The case should be recommended for write-off")

        recommendations_layout.addWidget(self.criminal_charges_cb)
        recommendations_layout.addWidget(self.disciplinary_cb)
        recommendations_layout.addWidget(self.loss_recovery_cb)
        recommendations_layout.addWidget(self.write_off_cb)

        layout.addWidget(recommendations_group)

        # Committee Members Section
        members_group = QGroupBox("Committee Members")
        members_layout = QVBoxLayout(members_group)

        # Add member input
        member_input_layout = QHBoxLayout()
        self.member_name_edit = QLineEdit()
        self.member_name_edit.setPlaceholderText("Enter committee member name")
        add_member_btn = QPushButton("Add Member")
        add_member_btn.clicked.connect(self.add_committee_member)

        member_input_layout.addWidget(self.member_name_edit)
        member_input_layout.addWidget(add_member_btn)
        members_layout.addLayout(member_input_layout)

        # Members list
        self.members_list = QListWidget()
        self.members_list.setMaximumHeight(100)
        members_layout.addWidget(self.members_list)

        # Remove member button
        remove_member_btn = QPushButton("Remove Selected Member")
        remove_member_btn.clicked.connect(self.remove_committee_member)
        members_layout.addWidget(remove_member_btn)

        layout.addWidget(members_group)

        # Notes Section
        notes_group = QGroupBox("Additional Notes")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(
            "Enter any additional notes from the determination meeting..."
        )
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)

        layout.addWidget(notes_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Determination")
        save_btn.clicked.connect(self.save_determination)
        save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
        )

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def add_committee_member(self):
        member_name = self.member_name_edit.text().strip()
        if member_name:
            if member_name not in self.committee_members:
                self.committee_members.append(member_name)
                self.members_list.addItem(member_name)
                self.member_name_edit.clear()
            else:
                QMessageBox.warning(
                    self, "Duplicate Member", "This member is already in the list."
                )
        else:
            QMessageBox.warning(self, "Invalid Input", "Please enter a member name.")

    def remove_committee_member(self):
        current_item = self.members_list.currentItem()
        if current_item:
            member_name = current_item.text()
            self.committee_members.remove(member_name)
            self.members_list.takeItem(self.members_list.row(current_item))
        else:
            QMessageBox.warning(
                self, "No Selection", "Please select a member to remove."
            )

    def save_determination(self):
        try:
            # Validate required fields
            determined_amount_text = self.determined_amount_edit.text().strip()
            if not determined_amount_text:
                QMessageBox.warning(
                    self, "Invalid Input", "Please enter the determined amount."
                )
                return

            try:
                determined_amount = float(determined_amount_text)
                if determined_amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Determined amount must be a positive number.",
                )
                return

            # Check if at least one recommendation is made
            recommendations = {
                "criminal_charges": self.criminal_charges_cb.isChecked(),
                "disciplinary": self.disciplinary_cb.isChecked(),
                "loss_recovery": self.loss_recovery_cb.isChecked(),
                "write_off": self.write_off_cb.isChecked(),
            }

            if not any(recommendations.values()):
                QMessageBox.warning(
                    self, "Invalid Input", "Please select at least one recommendation."
                )
                return

            if not self.committee_members:
                QMessageBox.warning(
                    self, "Invalid Input", "Please add at least one committee member."
                )
                return

            # Convert date
            determination_date = self.determination_date_edit.date().toString(
                "yyyy-MM-dd"
            )

            # Prepare data for database
            determination_data = {
                "case_id": self.case_data[0],
                "transaction_no": self.transaction_no,
                "determination_date": determination_date,
                "determined_amount": determined_amount,
                "criminal_charges_recommended": recommendations["criminal_charges"],
                "disciplinary_recommended": recommendations["disciplinary"],
                "loss_recovery_recommended": recommendations["loss_recovery"],
                "write_off_recommended": recommendations["write_off"],
                "committee_members": json.dumps(self.committee_members),
                "notes": self.notes_edit.toPlainText().strip(),
            }

            # Save to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Insert into determination_history table
            cursor.execute(
                """
                INSERT INTO determination_history (
                    case_id, determination_date, determined_amount,
                    criminal_charges_recommended, disciplinary_recommended,
                    loss_recovery_recommended, write_off_recommended,
                    committee_members, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    determination_data["case_id"],
                    determination_data["determination_date"],
                    determination_data["determined_amount"],
                    determination_data["criminal_charges_recommended"],
                    determination_data["disciplinary_recommended"],
                    determination_data["loss_recovery_recommended"],
                    determination_data["write_off_recommended"],
                    determination_data["committee_members"],
                    determination_data["notes"],
                ),
            )

            # Update cases table with determination results
            cursor.execute(
                """
                UPDATE cases SET
                    determination_amount = ?,
                    determination_date = ?,
                    committee_recommendations = ?
                WHERE transaction_no = ?
            """,
                (
                    determined_amount,
                    determination_date,
                    json.dumps(recommendations),
                    self.transaction_no,
                ),
            )

            # Handle automatic status changes based on recommendations
            new_status = None
            new_list = None

            if recommendations["write_off"]:
                new_status = "Write Off Recommended"
                new_list = "Write-Off Recommended"
            elif recommendations["loss_recovery"]:
                # Could move to a recovery tracking status if needed
                pass

            if new_status and new_list:
                cursor.execute(
                    """
                    UPDATE cases SET
                        status = ?,
                        list = ?
                    WHERE transaction_no = ?
                """,
                    (new_status, new_list, self.transaction_no),
                )

            conn.commit()
            conn.close()

            # Log audit trail
            save_audit_log(
                "determination_made",
                {
                    "timestamp": datetime.now().isoformat(),
                    "case_id": self.case_data[0],
                    "transaction_no": self.transaction_no,
                    "details": determination_data,
                },
                self.fy,
            )

            QMessageBox.information(
                self, "Success", "Determination saved successfully!"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save determination: {str(e)}"
            )
