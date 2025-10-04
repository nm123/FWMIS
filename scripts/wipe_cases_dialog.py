import sqlite3
from datetime import datetime

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QFont, QIcon, QWheelEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import (
    get_all_financial_years,
    get_current_open_financial_year,
)


class NoWheelComboBox(QComboBox):
    """Custom QComboBox that ignores mouse wheel events unless focused"""

    def wheelEvent(self, event: QWheelEvent):
        """Override wheel event to only accept when widget has focus"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # Ignore wheel event when not focused
            event.ignore()


class WipeCasesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ Wipe Cases - DANGER ZONE")
        self.setFixedSize(600, 450)
        self.setModal(True)
        self.setup_ui()
        self.load_financial_years()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Warning header
        warning_group = QGroupBox("🚨 CRITICAL WARNING")
        warning_layout = QVBoxLayout()

        warning_text = QLabel(
            "This action will PERMANENTLY DELETE all case data for the selected financial year.\n\n"
            "This cannot be undone and will affect:"
        )
        warning_text.setWordWrap(True)
        warning_text.setStyleSheet(
            """
            QLabel {
                color: #dc3545;
                font-weight: bold;
                font-size: 12px;
            }
        """
        )
        warning_layout.addWidget(warning_text)

        # Affected items list
        affected_items = QLabel(
            "• All case records and transactions\n"
            "• Case attachments and documents\n"
            "• Case assignments and workflows\n"
            "• Case numbering counter (will reset to 00001)\n"
            "• Orphaned cases with invalid financial year data\n\n"
            "Audit logs and other system data will be preserved for compliance."
        )
        affected_items.setWordWrap(True)
        affected_items.setStyleSheet(
            """
            QLabel {
                color: #6c757d;
                font-size: 11px;
                padding-left: 20px;
            }
        """
        )
        warning_layout.addWidget(affected_items)

        warning_group.setLayout(warning_layout)
        layout.addWidget(warning_group)

        # Financial year selection
        fy_group = QGroupBox("Select Financial Year")
        fy_layout = QFormLayout()

        self.fy_combo = NoWheelComboBox()
        self.fy_combo.setMinimumWidth(250)
        fy_layout.addRow("Financial Year:", self.fy_combo)

        fy_group.setLayout(fy_layout)
        layout.addWidget(fy_group)

        # Case count display
        self.case_count_label = QLabel("Select a financial year to see case count...")
        self.case_count_label.setStyleSheet(
            """
            QLabel {
                color: #495057;
                font-style: italic;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 3px;
            }
        """
        )
        layout.addWidget(self.case_count_label)

        # Orphaned cases warning
        self.orphaned_label = QLabel("")
        self.orphaned_label.setStyleSheet(
            """
            QLabel {
                color: #dc3545;
                font-weight: bold;
                padding: 5px;
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 3px;
            }
        """
        )
        layout.addWidget(self.orphaned_label)

        # Connect fy combo change to update case count
        self.fy_combo.currentIndexChanged.connect(self.update_case_count)

        # Buttons
        button_layout = QHBoxLayout()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)

        # Spacer
        button_layout.addStretch()

        # Wipe button (styled as danger)
        self.wipe_btn = QPushButton("🗑️ WIPE ALL CASES")
        self.wipe_btn.clicked.connect(self.confirm_wipe)
        self.wipe_btn.setMinimumWidth(150)
        self.wipe_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """
        )
        button_layout.addWidget(self.wipe_btn)

        layout.addLayout(button_layout)

        # Add stretch to push everything to top
        layout.addStretch()

    def load_financial_years(self):
        """Load all financial years into the combo box"""
        try:
            financial_years = get_all_financial_years()

            if not financial_years:
                QMessageBox.warning(
                    self,
                    "No Financial Years",
                    "No financial years found in the database.",
                )
                self.reject()
                return

            self.fy_combo.clear()

            # Add "All Valid FYs" option first (special value None)
            self.fy_combo.addItem("All Valid FYs (Default)", None)

            # Find current open year for default selection after all
            current_open = get_current_open_financial_year()
            default_index = 0  # Default to "All"

            for i, (fy_id, fy_string, is_open) in enumerate(financial_years):
                display_text = f"{fy_string}"
                if is_open:
                    display_text += " (Current Open)"
                else:
                    display_text += " (Closed)"

                self.fy_combo.addItem(display_text, fy_id)

                # Set default to current open year if not "All"
                if current_open and fy_id == current_open[0]:
                    default_index = i + 1  # +1 because "All" is first

            # Set default selection to "All Valid FYs"
            self.fy_combo.setCurrentIndex(0)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load financial years: {e}")
            self.reject()

    def update_case_count(self):
        """Update the case count display for selected financial year"""
        try:
            fy_id = self.fy_combo.currentData()
            selected_text = self.fy_combo.currentText()

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            if fy_id is None:  # "All Valid FYs"
                # Count cases for all valid FYs
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM cases c
                    JOIN financial_years fy ON c.fy_id = fy.id
                    """
                )
                valid_case_count = cursor.fetchone()[0]

                # Count orphaned cases separately
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM cases
                    WHERE fy_id NOT IN (SELECT id FROM financial_years) OR fy_id IS NULL
                """
                )
                orphaned_count = cursor.fetchone()[0]

                conn.close()

                if valid_case_count == 0 and orphaned_count == 0:
                    self.case_count_label.setText("No cases found in valid financial years.")
                elif valid_case_count > 0 and orphaned_count == 0:
                    self.case_count_label.setText(
                        f"⚠️ {valid_case_count} case(s) in valid FYs will be permanently deleted!"
                    )
                elif valid_case_count == 0 and orphaned_count > 0:
                    self.case_count_label.setText(
                        f"⚠️ {orphaned_count} orphaned case(s) will be cleaned up!"
                    )
                else:
                    self.case_count_label.setText(
                        f"⚠️ {valid_case_count} case(s) in valid FYs + {orphaned_count} orphaned case(s) will be cleaned up!"
                    )

                if orphaned_count > 0:
                    self.orphaned_label.setText(
                        f"⚠️ Warning: {orphaned_count} orphaned cases (invalid FY IDs) will be deleted separately."
                    )
                else:
                    self.orphaned_label.setText("")

                return

            # Count cases for specific FY
            cursor.execute("SELECT COUNT(*) FROM cases WHERE fy_id = ?", (fy_id,))
            fy_case_count = cursor.fetchone()[0]

            # Count orphaned cases separately
            cursor.execute(
                """
                SELECT COUNT(*) FROM cases
                WHERE fy_id NOT IN (SELECT id FROM financial_years) OR fy_id IS NULL
            """
            )
            orphaned_count = cursor.fetchone()[0]

            conn.close()

            if fy_case_count == 0 and orphaned_count == 0:
                self.case_count_label.setText(f"No cases found for {selected_text}.")
            elif fy_case_count > 0 and orphaned_count == 0:
                self.case_count_label.setText(
                    f"⚠️ {fy_case_count} case(s) in {selected_text} will be permanently deleted!"
                )
            elif fy_case_count == 0 and orphaned_count > 0:
                self.case_count_label.setText(
                    f"⚠️ {orphaned_count} orphaned case(s) will be cleaned up!"
                )
            else:
                self.case_count_label.setText(
                    f"⚠️ {fy_case_count} case(s) in {selected_text} + {orphaned_count} orphaned case(s) will be cleaned up!"
                )

            if orphaned_count > 0:
                self.orphaned_label.setText(
                    f"⚠️ Warning: {orphaned_count} orphaned cases (invalid FY IDs) will be deleted separately."
                )
            else:
                self.orphaned_label.setText("")

        except sqlite3.Error as e:
            self.case_count_label.setText(f"Error counting cases: {e}")
            self.orphaned_label.setText("")

    def confirm_wipe(self):
        """Show confirmation dialog before wiping"""
        fy_id = self.fy_combo.currentData()
        fy_text = self.fy_combo.currentText()

        if fy_id is None and fy_text == "All Valid FYs (Default)":
            fy_id = None  # All valid

        if fy_id is None:
            # For all valid, confirm
            reply = QMessageBox.question(
                self,
                "Confirm Wipe All Valid FYs",
                "Are you sure you want to wipe ALL cases from valid financial years?\n\n"
                "Orphaned cases will be cleaned up separately.\n\n"
                "This action CANNOT be undone!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                if self.case_count_label.text().startswith("⚠️"):
                    # Extract counts from label or requery
                    self.perform_wipe(fy_id, fy_text, 0, 0)  # Counts handled inside
                else:
                    QMessageBox.information(self, "No Action", "No cases to wipe.")
            return

        # Get case counts for confirmation
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            if fy_id is None:  # All valid
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM cases c
                    JOIN financial_years fy ON c.fy_id = fy.id
                """
                )
                valid_case_count = cursor.fetchone()[0]
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM cases
                    WHERE fy_id NOT IN (SELECT id FROM financial_years) OR fy_id IS NULL
                """
                )
                orphaned_count = cursor.fetchone()[0]
                fy_case_count = valid_case_count
            else:
                # Specific FY
                cursor.execute("SELECT COUNT(*) FROM cases WHERE fy_id = ?", (fy_id,))
                fy_case_count = cursor.fetchone()[0]
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM cases
                    WHERE fy_id NOT IN (SELECT id FROM financial_years) OR fy_id IS NULL
                """
                )
                orphaned_count = cursor.fetchone()[0]

            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to count cases: {e}")
            return

        total_cases = fy_case_count + orphaned_count

        if total_cases == 0:
            QMessageBox.information(
                self,
                "No Cases",
                "No cases found for the selected financial year(s) or orphaned cases to clean up.",
            )
            return

        # Final confirmation
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("FINAL CONFIRMATION - DATA LOSS")

        if fy_id is None:
            if fy_case_count > 0 and orphaned_count > 0:
                msg.setText(
                    f"You are about to DELETE {fy_case_count} case(s) from ALL valid FYs and {orphaned_count} orphaned case(s)"
                )
            elif fy_case_count > 0:
                msg.setText(
                    f"You are about to DELETE {fy_case_count} case(s) from ALL valid FYs"
                )
            else:
                msg.setText(f"You are about to DELETE {orphaned_count} orphaned case(s)")
        else:
            if fy_case_count > 0 and orphaned_count > 0:
                msg.setText(
                    f"You are about to DELETE {fy_case_count} case(s) from {fy_text} and {orphaned_count} orphaned case(s)"
                )
            elif fy_case_count > 0:
                msg.setText(
                    f"You are about to DELETE {fy_case_count} case(s) from {fy_text}"
                )
            else:
                msg.setText(f"You are about to DELETE {orphaned_count} orphaned case(s)")

        msg.setInformativeText(
            "This action CANNOT be undone!\n\n"
            f"Total cases to be removed: {total_cases}\n\n"
            "Are you absolutely sure you want to proceed?\n\n"
            "Type 'WIPE' in the box below to confirm:"
        )

        # Add a text input for confirmation
        from PyQt5.QtWidgets import QLineEdit

        confirm_input = QLineEdit()
        confirm_input.setPlaceholderText("Type WIPE to confirm")
        msg.layout().addWidget(confirm_input, 2, 1)

        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        # Show dialog and check confirmation
        result = msg.exec_()

        if result == QMessageBox.Yes:
            if confirm_input.text().upper() == "WIPE":
                self.perform_wipe(fy_id, fy_text, fy_case_count, orphaned_count)
            else:
                QMessageBox.warning(
                    self,
                    "Confirmation Failed",
                    "You must type 'WIPE' to confirm the deletion.",
                )
        else:
            # User cancelled
            pass

    def perform_wipe(self, fy_id, fy_text, fy_case_count, orphaned_count):
        """Perform the actual wipe operation"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Initialize variables
            cleaned_count = 0
            cleaned_periods_count = 0

            print(f"DEBUG: ===== WIPE OPERATION START =====")
            print(f"DEBUG: Wiping FY {fy_text} (ID: {fy_id})")

            # Log to file for debugging
            with open("wipe_debug.log", "a") as f:
                f.write(f"\\n=== WIPE OPERATION START {datetime.now()} ===\\n")
                f.write(f"Wiping FY {fy_text} (ID: {fy_id})\\n")

            # Verify what financial year this ID corresponds to
            cursor.execute(
                "SELECT start_year, end_year, status FROM financial_years WHERE id = ?",
                (fy_id,),
            )
            fy_details = cursor.fetchone()
            if fy_details:
                start_year, end_year, status = fy_details
                print(f"DEBUG: FY details: {start_year}-{end_year}, Status: {status}")
            else:
                print(
                    f"DEBUG: ERROR: FY ID {fy_id} not found in financial_years table!"
                )

            # Check what cases exist BEFORE deletion
            cursor.execute(
                """
                SELECT COUNT(*), GROUP_CONCAT(transaction_no, ', ') FROM cases
                WHERE fy_id = ?
            """,
                (fy_id,),
            )
            before_result = cursor.fetchone()
            print(f"DEBUG: Cases BEFORE wipe: {before_result[0]} cases")
            if before_result[1]:
                print(f"DEBUG: Case numbers: {before_result[1][:200]}...")

            # Check what cases exist in OTHER financial years
            cursor.execute(
                """
                SELECT fy_id, COUNT(*), MAX(transaction_no) FROM cases
                WHERE fy_id != ?
                GROUP BY fy_id
                ORDER BY fy_id
            """,
                (fy_id,),
            )
            other_fy_cases = cursor.fetchall()
            print(f"DEBUG: Cases in OTHER FYs: {other_fy_cases}")

            # Clean up any orphaned cases FIRST (cases with invalid fy_id or NULL fy_id) to prevent numbering issues
            cursor.execute(
                """
                SELECT COUNT(*) FROM cases
                WHERE fy_id NOT IN (SELECT id FROM financial_years) OR fy_id IS NULL
            """
            )
            orphaned_count = cursor.fetchone()[0]

            if orphaned_count > 0:
                print(
                    f"DEBUG: Found {orphaned_count} orphaned cases with invalid/NULL fy_id - cleaning up"
                )
                cursor.execute(
                    """
                    DELETE FROM cases
                    WHERE fy_id NOT IN (SELECT id FROM financial_years) OR fy_id IS NULL
                """
                )
                cleaned_count = cursor.rowcount
                print(f"DEBUG: Cleaned up {cleaned_count} orphaned cases")
            else:
                print(f"DEBUG: No orphaned cases found")
                cleaned_count = 0

            # Check installments before deletion
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='installments'")
            installments_table_exists = cursor.fetchone() is not None
            if installments_table_exists:
                cursor.execute("SELECT COUNT(*) FROM installments")
                total_installments_before = cursor.fetchone()[0]
                print(
                    f"DEBUG: Total installments before cleanup: {total_installments_before}"
                )
            else:
                total_installments_before = 0
                print("DEBUG: Installments table does not exist; total before: 0")

            with open("wipe_debug.log", "a") as f:
                f.write(
                    f"Total installments before cleanup: {total_installments_before}\\n"
                )

            # Also delete related data that depends on cases BEFORE deleting cases
            # Delete installments for cases in this financial year
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='installments'")
            if cursor.fetchone():
                cursor.execute(
                    """
                    DELETE FROM installments
                    WHERE case_id IN (SELECT id FROM cases WHERE fy_id = ?)
                """,
                    (fy_id,),
                )
                installments_deleted = cursor.rowcount
                print(f"DEBUG: Deleted {installments_deleted} installments for FY {fy_id}")
            else:
                installments_deleted = 0
                print("DEBUG: Installments table does not exist; skipping deletion")

            with open("wipe_debug.log", "a") as f:
                f.write(
                    f"Deleted {installments_deleted} installments for FY {fy_id}\\n"
                )

            # Also clean up any orphaned installments (installments for non-existent cases)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='installments'")
            if cursor.fetchone():
                cursor.execute(
                    """
                    DELETE FROM installments
                    WHERE case_id NOT IN (SELECT id FROM cases)
                """
                )
                orphaned_installments_deleted = cursor.rowcount
                print(
                    f"DEBUG: Deleted {orphaned_installments_deleted} orphaned installments"
                )
            else:
                orphaned_installments_deleted = 0
                print("DEBUG: Installments table does not exist; skipping orphaned cleanup")

            with open("wipe_debug.log", "a") as f:
                f.write(
                    f"Deleted {orphaned_installments_deleted} orphaned installments\\n"
                )

            # Check installments after deletion
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='installments'")
            installments_table_exists = cursor.fetchone() is not None
            if installments_table_exists:
                cursor.execute("SELECT COUNT(*) FROM installments")
                total_installments_after = cursor.fetchone()[0]
                print(
                    f"DEBUG: Total installments after cleanup: {total_installments_after}"
                )
            else:
                total_installments_after = 0
                print("DEBUG: Installments table does not exist; total after: 0")

            with open("wipe_debug.log", "a") as f:
                f.write(
                    f"Total installments after cleanup: {total_installments_after}\\n"
                )

            # Delete all cases for this financial year
            cursor.execute("DELETE FROM cases WHERE fy_id = ?", (fy_id,))
            cases_deleted = cursor.rowcount
            print(f"DEBUG: Deleted {cases_deleted} cases from FY {fy_id}")

            # Verify deletion
            cursor.execute("SELECT COUNT(*) FROM cases WHERE fy_id = ?", (fy_id,))
            after_count = cursor.fetchone()[0]
            print(f"DEBUG: Cases remaining in FY {fy_id}: {after_count}")

            # Delete case attachments/documents
            cursor.execute(
                """
                DELETE FROM shared_documents
                WHERE id IN (SELECT shared_document_id FROM cases WHERE fy_id = ? AND shared_document_id IS NOT NULL)
            """,
                (fy_id,),
            )
            docs_deleted = cursor.rowcount
            print(f"DEBUG: Deleted {docs_deleted} shared documents")

            # Also clean up orphaned periods that belong to non-existent financial years
            cursor.execute(
                """
                SELECT COUNT(*) FROM periods
                WHERE fy_id NOT IN (SELECT id FROM financial_years) AND fy_id IS NOT NULL
            """
            )
            orphaned_periods_count = cursor.fetchone()[0]

            if orphaned_periods_count > 0:
                print(
                    f"DEBUG: Found {orphaned_periods_count} orphaned periods with invalid fy_id - cleaning up"
                )
                cursor.execute(
                    """
                    DELETE FROM periods
                    WHERE fy_id NOT IN (SELECT id FROM financial_years) AND fy_id IS NOT NULL
                """
                )
                cleaned_periods_count = cursor.rowcount
                print(f"DEBUG: Cleaned up {cleaned_periods_count} orphaned periods")
            else:
                print(f"DEBUG: No orphaned periods found")
                cleaned_periods_count = 0

            # Check current counter before reset
            cursor.execute(
                "SELECT counter FROM fy_case_counters WHERE fy_id = ?", (fy_id,)
            )
            old_counter = cursor.fetchone()
            print(f"DEBUG: Counter before reset: {old_counter}")

            # Reset the case counter for this financial year so numbering starts fresh
            cursor.execute(
                """
                UPDATE fy_case_counters SET counter = 0 WHERE fy_id = ?
            """,
                (fy_id,),
            )
            counter_updated = cursor.rowcount
            print(f"DEBUG: Updated {counter_updated} counter rows")

            # If no counter exists for this FY, create one with counter = 0
            cursor.execute(
                """
                INSERT OR IGNORE INTO fy_case_counters (fy_id, counter) VALUES (?, 0)
            """,
                (fy_id,),
            )
            counter_inserted = cursor.rowcount
            print(f"DEBUG: Inserted {counter_inserted} counter rows")

            # Verify counter after reset
            cursor.execute(
                "SELECT counter FROM fy_case_counters WHERE fy_id = ?", (fy_id,)
            )
            new_counter = cursor.fetchone()
            print(f"DEBUG: Counter after reset: {new_counter}")

            # Check ALL counters in the database
            cursor.execute("SELECT fy_id, counter FROM fy_case_counters ORDER BY fy_id")
            all_counters = cursor.fetchall()
            print(f"DEBUG: All counters in database: {all_counters}")

            # Note: Audit logs are preserved for compliance reasons
            # They contain historical records that may be needed for auditing purposes
            # Only case data is deleted, not the audit trail

            conn.commit()
            conn.close()

            print(f"DEBUG: ===== WIPE OPERATION COMPLETED =====")

            total_cleaned = cases_deleted + cleaned_count
            total_installments = installments_deleted + orphaned_installments_deleted
            QMessageBox.information(
                self,
                "Success",
                f"Successfully cleaned up the database!\n\n"
                f"• Deleted {cases_deleted} case(s) from {fy_text}\n"
                f"• Cleaned up {cleaned_count} orphaned case(s)\n"
                f"• Deleted {total_installments} installment(s)\n"
                f"• Cleaned up {cleaned_periods_count} orphaned period(s)\n\n"
                f"Total: {total_cleaned} case(s) removed\n\n"
                "Case numbering will restart from 00001.",
            )

            self.accept()

        except sqlite3.Error as e:
            print(f"DEBUG: Database error during wipe: {e}")
            import traceback

            print(f"DEBUG: Wipe traceback: {traceback.format_exc()}")
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to wipe cases: {e}\n\n"
                "Some data may have been partially deleted. Please check the database.",
            )
