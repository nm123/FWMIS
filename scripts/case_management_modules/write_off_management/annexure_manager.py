"""
Annexure Manager Module for Write-Off Management

Contains functionality for managing write-off annexures.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .dialog import WriteOffManagementDialog


class AnnexureManager:
    """
    Manages write-off annexure operations.
    """

    def __init__(self, dialog: "WriteOffManagementDialog"):
        """
        Initialize the annexure manager.

        Args:
            dialog: The parent WriteOffManagementDialog instance
        """
        self.dialog = dialog

    def load_annexures(self) -> None:
        """
        Load annexures data and populate the annexures table.
        """
        try:
            from scripts.Repositories import get_annexure_repository

            repo = get_annexure_repository()

            # Get selected FY filter
            selected_fy = self.dialog.fy_filter_combo.currentData()

            # Get annexures based on filter
            if selected_fy:
                # TODO: Add FY filtering to repository method
                annexures = repo.get_all_annexures_with_details()
                annexures = [
                    a for a in annexures if a.get("financial_year_id") == selected_fy
                ]
            else:
                annexures = repo.get_all_annexures_with_details()  # All years

            # Clear existing rows
            self.dialog.annexures_table.setRowCount(0)

            # Populate table
            for annexure in annexures:
                row_count = self.dialog.annexures_table.rowCount()
                self.dialog.annexures_table.insertRow(row_count)

                # Annexure data
                annexure_id = annexure.get("id")
                annexure_no = annexure.get("annexure_no")
                created_date = annexure.get("created_date", "")
                status = annexure.get("status", "Unknown")
                cases_count = annexure.get("cases_count", 0)
                total_amount = annexure.get("total_amount", 0)

                # Format date
                if created_date:
                    try:
                        from datetime import datetime

                        created_date = datetime.fromisoformat(created_date).strftime(
                            "%Y-%m-%d"
                        )
                    except (ValueError, TypeError) as e:
                        # Log the error but keep original format
                        import logging

                        logging.warning(f"Failed to parse date '{created_date}': {e}")
                        pass  # Keep original format if parsing fails

                # Set table data
                self.dialog.annexures_table.setItem(
                    row_count, 0, self._create_table_item(annexure_no)
                )
                self.dialog.annexures_table.setItem(
                    row_count, 1, self._create_table_item(created_date)
                )
                self.dialog.annexures_table.setItem(
                    row_count, 2, self._create_table_item(status)
                )
                self.dialog.annexures_table.setItem(
                    row_count, 3, self._create_table_item(str(cases_count))
                )
                self.dialog.annexures_table.setItem(
                    row_count, 4, self._create_table_item(f"R{total_amount:.2f}")
                )

                # Actions widget
                actions_widget = self.create_annexure_actions_widget(
                    annexure_id, annexure_no
                )
                self.dialog.annexures_table.setCellWidget(row_count, 5, actions_widget)

                # Details button
                details_btn = self._create_action_button("View Details")
                details_btn.clicked.connect(
                    lambda checked, aid=annexure_id: self.view_annexure_details(aid)
                )
                self.dialog.annexures_table.setCellWidget(row_count, 6, details_btn)

                # Export buttons widget
                export_widget = self._create_export_widget(annexure_id, annexure_no)
                self.dialog.annexures_table.setCellWidget(row_count, 7, export_widget)

        except Exception as e:
            from scripts.Utilities.message_box_utils import show_warning_message

            show_warning_message(
                self.dialog, "Error", f"Failed to load annexures: {str(e)}"
            )

    def create_annexure_actions_widget(self, annexure_id: int, annexure_no: str):
        """
        Create action buttons widget for an annexure.

        Args:
            annexure_id: The annexure ID
            annexure_no: The annexure number

        Returns:
            QWidget: Widget containing action buttons
        """
        from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget

        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)

        # Get annexure status
        status = self._get_annexure_status(annexure_id)

        if status == "Draft":
            approve_btn = QPushButton("Approve")
            approve_btn.clicked.connect(
                lambda: self.approve_annexure(annexure_id, annexure_no)
            )
            actions_layout.addWidget(approve_btn)

            decline_btn = QPushButton("Decline")
            decline_btn.clicked.connect(
                lambda: self.decline_annexure(annexure_id, annexure_no)
            )
            actions_layout.addWidget(decline_btn)

        elif status == "Approved":
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(
                lambda: self.delete_annexure(annexure_id, annexure_no)
            )
            actions_layout.addWidget(delete_btn)

        actions_layout.addStretch()
        return actions_widget

    def approve_annexure(self, annexure_id: int, annexure_no: str) -> None:
        """
        Approve a write-off annexure.

        Args:
            annexure_id: The annexure ID
            annexure_no: The annexure number
        """
        try:
            from scripts.Utilities.message_box_utils import show_confirmation_dialog

            if not show_confirmation_dialog(
                self.dialog,
                "Confirm Approval",
                f"Are you sure you want to approve write-off annexure '{annexure_no}'?\n\n"
                "This will finalize the write-off process for all associated cases.\n\n"
                "This action cannot be undone.",
            ):
                return

                # Update annexure status to "Approved"
                success, message = self._update_annexure_status(annexure_id, "Approved")

                if success:
                    # Update associated cases to "Write Off Recommended" status
                    self._update_associated_cases_status(annexure_id)

                    # Log the action
                    from scripts.Utilities.audit_utils import save_audit_log

                    save_audit_log(
                        "ANNEXURE_APPROVED",
                        f"Write-off annexure {annexure_no} approved",
                        annexure_id,
                    )

                    QMessageBox.information(
                        self.dialog,
                        "Success",
                        f"Write-off annexure '{annexure_no}' has been approved and all associated cases have been marked for write-off.",
                    )
                    self.load_annexures()
                else:
                    QMessageBox.warning(
                        self.dialog,
                        "Error",
                        f"Failed to approve write-off annexure: {message}",
                    )

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                self.dialog, "Error", f"Failed to approve write-off annexure: {str(e)}"
            )

    def decline_annexure(self, annexure_id: int, annexure_no: str) -> None:
        """
        Decline a write-off annexure.

        Args:
            annexure_id: The annexure ID
            annexure_no: The annexure number
        """
        try:
            from PyQt5.QtWidgets import QInputDialog, QMessageBox

            # Get decline reason
            reason, ok = QInputDialog.getText(
                self.dialog,
                "Decline Reason",
                "Please provide a reason for declining this write-off annexure:",
            )

            if ok and reason.strip():
                # Update annexure status to "Declined" with reason
                success, message = self._update_annexure_status(
                    annexure_id, "Declined", reason.strip()
                )

                if success:
                    # Log the action
                    from scripts.Utilities.audit_utils import save_audit_log

                    save_audit_log(
                        "ANNEXURE_DECLINED",
                        f"Write-off annexure {annexure_no} declined: {reason}",
                        annexure_id,
                    )

                    QMessageBox.information(
                        self.dialog,
                        "Success",
                        f"Write-off annexure '{annexure_no}' has been declined.",
                    )
                    self.load_annexures()
                else:
                    QMessageBox.warning(
                        self.dialog,
                        "Error",
                        f"Failed to decline write-off annexure: {message}",
                    )
            elif ok:
                QMessageBox.warning(
                    self.dialog,
                    "Invalid Input",
                    "Please provide a reason for declining the annexure.",
                )

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                self.dialog, "Error", f"Failed to decline write-off annexure: {str(e)}"
            )

    def view_annexure_details(self, annexure_id: int) -> None:
        """
        View detailed information about an annexure.

        Args:
            annexure_id: The annexure ID
        """
        try:
            from scripts.Utilities.annexure_utils import get_annexure_details

            # Get annexure details
            details = get_annexure_details(annexure_id)

            if not details:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self.dialog, "Error", "Failed to load annexure details."
                )
                return

            # Create details dialog
            from PyQt5.QtWidgets import (
                QDialog,
                QDialogButtonBox,
                QTextEdit,
                QVBoxLayout,
            )

            details_dialog = QDialog(self.dialog)
            details_dialog.setWindowTitle(
                f"Annexure Details - {details.get('annexure_no', 'Unknown')}"
            )
            details_dialog.resize(800, 600)

            layout = QVBoxLayout(details_dialog)

            # Details text area
            details_text = QTextEdit()
            details_text.setReadOnly(True)

            # Format details
            details_content = self._format_annexure_details(details)
            details_text.setPlainText(details_content)
            layout.addWidget(details_text)

            # Buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(details_dialog.accept)
            layout.addWidget(button_box)

            details_dialog.exec_()

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                self.dialog, "Error", f"Failed to view annexure details: {str(e)}"
            )

    def delete_annexure(self, annexure_id: int, annexure_no: str) -> None:
        """
        Delete a write-off annexure.

        Args:
            annexure_id: The annexure ID
            annexure_no: The annexure number
        """
        try:
            from PyQt5.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self.dialog,
                "Confirm Deletion",
                f"Are you sure you want to delete write-off annexure '{annexure_no}'?\n\n"
                "This will permanently remove the annexure and cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                # Delete annexure
                success, message = self._delete_annexure_from_db(annexure_id)

                if success:
                    # Log the action
                    from scripts.Utilities.audit_utils import save_audit_log

                    save_audit_log(
                        "ANNEXURE_DELETED",
                        f"Write-off annexure {annexure_no} deleted",
                        annexure_id,
                    )

                    QMessageBox.information(
                        self.dialog,
                        "Success",
                        f"Write-off annexure '{annexure_no}' has been deleted.",
                    )
                    self.load_annexures()
                else:
                    QMessageBox.warning(
                        self.dialog,
                        "Error",
                        f"Failed to delete write-off annexure: {message}",
                    )

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                self.dialog, "Error", f"Failed to delete write-off annexure: {str(e)}"
            )

    def _create_table_item(self, text: str):
        """Create a table widget item."""
        from PyQt5.QtWidgets import QTableWidgetItem

        return QTableWidgetItem(text)

    def _create_action_button(self, text: str):
        """Create an action button."""
        from PyQt5.QtWidgets import QPushButton

        return QPushButton(text)

    def _create_export_widget(self, annexure_id: int, annexure_no: str):
        """Create export buttons widget."""
        from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget

        export_widget = QWidget()
        export_layout = QHBoxLayout(export_widget)
        export_layout.setContentsMargins(0, 0, 0, 0)

        excel_btn = QPushButton("Excel")
        excel_btn.clicked.connect(
            lambda: self._export_annexure_excel(annexure_id, annexure_no)
        )
        export_layout.addWidget(excel_btn)

        pdf_btn = QPushButton("PDF")
        pdf_btn.clicked.connect(
            lambda: self._export_annexure_pdf(annexure_id, annexure_no)
        )
        export_layout.addWidget(pdf_btn)

        return export_widget

    def _export_annexure_excel(self, annexure_id: int, annexure_no: str) -> None:
        """Export annexure to Excel."""
        try:
            from scripts.Utilities.excel_exporter import export_annexure_to_excel

            success, message = export_annexure_to_excel(annexure_id)

            if success:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.information(
                    self.dialog,
                    "Success",
                    f"Annexure '{annexure_no}' exported to Excel successfully.\n\n{message}",
                )
            else:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self.dialog,
                    "Export Failed",
                    f"Failed to export annexure to Excel: {message}",
                )

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                self.dialog, "Error", f"Failed to export annexure to Excel: {str(e)}"
            )

    def _export_annexure_pdf(self, annexure_id: int, annexure_no: str) -> None:
        """Export annexure to PDF."""
        try:
            from scripts.Utilities.pdf_exporter import export_annexure_to_pdf

            success, message = export_annexure_to_pdf(annexure_id)

            if success:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.information(
                    self.dialog,
                    "Success",
                    f"Annexure '{annexure_no}' exported to PDF successfully.\n\n{message}",
                )
            else:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self.dialog,
                    "Export Failed",
                    f"Failed to export annexure to PDF: {message}",
                )

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                self.dialog, "Error", f"Failed to export annexure to PDF: {str(e)}"
            )

    def _get_annexure_status(self, annexure_id: int) -> str:
        """Get the status of an annexure."""
        try:
            from scripts.Utilities.annexure_utils import get_annexure_details

            details = get_annexure_details(annexure_id)
            return details.get("status", "Unknown")
        except Exception as e:
            import logging

            logging.error(f"Failed to get annexure status for ID {annexure_id}: {e}")
            return "Unknown"

    def _update_annexure_status(
        self, annexure_id: int, new_status: str, reason: str = ""
    ):
        """Update annexure status in database."""
        try:
            from scripts.Repositories import get_annexure_repository

            repo = get_annexure_repository()
            success = repo.update_annexure_status(
                annexure_id, new_status, reason if reason else None
            )

            return success, (
                "Status updated successfully" if success else "Failed to update status"
            )

        except Exception as e:
            import logging

            logging.error(f"Failed to update annexure status for ID {annexure_id}: {e}")
            return False, str(e)

    def _update_associated_cases_status(self, annexure_id: int) -> None:
        """Update status of cases associated with the annexure."""
        try:
            from scripts.Repositories import get_annexure_repository

            repo = get_annexure_repository()

            # Update case statuses to "Write Off Recommended"
            repo.update_associated_case_statuses(
                annexure_id, "Write Off Recommended", "Write Off Recommended"
            )

        except Exception as e:
            import logging

            logging.error(
                f"Failed to update associated cases for annexure {annexure_id}: {e}"
            )

    def _delete_annexure_from_db(self, annexure_id: int):
        """Delete annexure from database."""
        try:
            from scripts.Repositories import get_annexure_repository

            repo = get_annexure_repository()
            success = repo.delete_annexure(annexure_id)

            return success, (
                "Annexure deleted successfully"
                if success
                else "Failed to delete annexure"
            )

        except Exception as e:
            return False, str(e)

    def _format_annexure_details(self, details: dict) -> str:
        """Format annexure details for display."""
        annexure_no = details.get("annexure_no", "N/A")
        status = details.get("status", "N/A")
        created_date = details.get("created_date", "N/A")
        total_amount = details.get("total_amount", 0)
        cases = details.get("cases", [])

        content = f"""
Annexure Number: {annexure_no}
Status: {status}
Created Date: {created_date}
Total Amount: R{total_amount:.2f}

Cases Included:
"""

        if cases:
            for case in cases:
                content += f"- Transaction: {case.get('transaction_no', 'N/A')}\n"
                content += f"  Amount: R{case.get('amount', 0):.2f}\n"
                content += f"  Description: {case.get('description', 'N/A')}\n\n"
        else:
            content += "No cases found in this annexure."

        return content.strip()
