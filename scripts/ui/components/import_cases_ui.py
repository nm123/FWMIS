import os
import sqlite3

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from scripts.category_management import ManageCategoriesDialog
from scripts.core.import_worker import ImportWorker
from scripts.models.bas_parser import BASParser
from scripts.responsibility_management_actions import edit_responsibility_by_name
from scripts.responsibility_management_ui import ResponsibilityManagementDialog
from scripts.ui.dialogs.transaction_details_dialog import TransactionDetailsDialog
from scripts.Utilities.category_utils import load_categories
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.import_cases_utils import validate_responsibility
from scripts.Utilities.responsibility_utils import load_posting_responsibilities
from scripts.Utilities.ui_theme import (
    apply_theme,
    create_professional_button,
    create_professional_groupbox,
    create_status_label,
    setup_professional_table,
)
from scripts.Utilities.utils import format_currency_amount


def setup_import_ui(dialog):
    layout = QVBoxLayout(dialog)
    layout.setSpacing(15)
    layout.setContentsMargins(20, 20, 20, 20)

    # Header section
    header_layout = QHBoxLayout()
    header_label = QLabel("Import Undisclosed Cases")
    header_label.setStyleSheet(
        """
        QLabel {
            font-size: 18px;
            font-weight: bold;
            color: #343a40;
            margin-bottom: 5px;
        }
    """
    )
    header_layout.addWidget(header_label)
    header_layout.addStretch()
    layout.addLayout(header_layout)

    # File selection section
    file_group = create_professional_groupbox("BAS Report File Selection", "blue")
    file_layout = QHBoxLayout()
    file_layout.setSpacing(10)

    dialog.file_path_edit = QLineEdit()
    dialog.file_path_edit.setPlaceholderText(
        "Click Browse to select BAS report file (.txt)..."
    )
    dialog.file_path_edit.setReadOnly(True)
    dialog.file_path_edit.setMinimumHeight(35)

    dialog.browse_button = create_professional_button("Browse", "success")
    dialog.browse_button.clicked.connect(lambda: browse_file(dialog))

    file_layout.addWidget(dialog.file_path_edit)
    file_layout.addWidget(dialog.browse_button)
    file_group.setLayout(file_layout)
    layout.addWidget(file_group)

    # Import settings section
    settings_group = create_professional_groupbox("Import Configuration")
    settings_layout = QGridLayout()
    settings_layout.setSpacing(15)

    # Category selection
    category_label = QLabel("Category:")
    category_label.setStyleSheet("font-weight: bold;")
    dialog.category_button = create_professional_button("Select Category")
    dialog.category_button.clicked.connect(lambda: select_category(dialog))
    dialog.category_button.setMinimumHeight(35)
    dialog.category_label = QLabel("No category selected")
    dialog.category_label.setStyleSheet(
        """
        QLabel {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 8px;
            color: #856404;
            font-style: italic;
        }
    """
    )

    # Date range selection
    date_label = QLabel("📅 Date Range:")
    date_label.setStyleSheet("font-weight: bold;")

    date_range_layout = QHBoxLayout()
    date_range_layout.setSpacing(10)

    from_label = QLabel("From:")
    from_label.setMinimumWidth(40)
    dialog.date_from_edit = QDateEdit()
    dialog.date_from_edit.setDate(QDate.currentDate().addMonths(-1))
    dialog.date_from_edit.setCalendarPopup(True)
    dialog.date_from_edit.setMinimumHeight(35)

    to_label = QLabel("To:")
    to_label.setMinimumWidth(25)
    dialog.date_to_edit = QDateEdit()
    dialog.date_to_edit.setDate(QDate.currentDate())
    dialog.date_to_edit.setCalendarPopup(True)
    dialog.date_to_edit.setMinimumHeight(35)

    date_range_layout.addWidget(from_label)
    date_range_layout.addWidget(dialog.date_from_edit)
    date_range_layout.addWidget(to_label)
    date_range_layout.addWidget(dialog.date_to_edit)
    date_range_layout.addStretch()

    # Parse button
    dialog.parse_button = create_professional_button("Parse File", "info")
    dialog.parse_button.clicked.connect(lambda: dialog.logic.parse_file())
    dialog.parse_button.setEnabled(False)
    dialog.parse_button.setMinimumHeight(40)

    # Layout arrangement
    settings_layout.addWidget(category_label, 0, 0)
    settings_layout.addWidget(dialog.category_button, 0, 1)
    settings_layout.addWidget(dialog.category_label, 0, 2, 1, 2)

    settings_layout.addWidget(date_label, 1, 0)
    settings_layout.addLayout(date_range_layout, 1, 1, 1, 3)

    settings_layout.addWidget(dialog.parse_button, 2, 1, 1, 2, Qt.AlignCenter)

    settings_group.setLayout(settings_layout)
    layout.addWidget(settings_group)

    # Results section
    results_group = create_professional_groupbox(
        "Transaction Analysis & Processing", "purple"
    )
    results_layout = QVBoxLayout()
    results_layout.setSpacing(10)

    # Status display
    status_layout = QHBoxLayout()
    dialog.results_label = create_status_label("⏳ Ready to parse BAS file...", "info")
    dialog.results_label.setMinimumHeight(40)
    status_layout.addWidget(dialog.results_label)
    results_layout.addLayout(status_layout)

    # Progress bar
    dialog.progress_bar = QProgressBar()
    dialog.progress_bar.setVisible(False)
    dialog.progress_bar.setMinimumHeight(25)
    results_layout.addWidget(dialog.progress_bar)

    # Transactions table
    table_container = QWidget()
    table_layout = QVBoxLayout()
    table_layout.setContentsMargins(0, 0, 0, 0)

    table_header = QLabel("Parsed Transactions:")
    table_header.setStyleSheet(
        """
        QLabel {
            font-size: 14px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }
    """
    )
    table_layout.addWidget(table_header)

    dialog.transactions_table = QTableWidget()
    dialog.transactions_table.setColumnCount(9)
    dialog.transactions_table.setHorizontalHeaderLabels(
        [
            "Responsibility",
            "Type",
            "Amount",
            "Date",
            "Description",
            "Resp Status",
            "Dup Status",
            "Case Number",
            "Actions",
        ]
    )

    setup_professional_table(dialog.transactions_table)

    header = dialog.transactions_table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Interactive)
    header.setStretchLastSection(True)
    dialog.transactions_table.setColumnWidth(0, 200)  # Responsibility
    dialog.transactions_table.setColumnWidth(1, 70)  # Type
    dialog.transactions_table.setColumnWidth(2, 110)  # Amount
    dialog.transactions_table.setColumnWidth(3, 110)  # Date
    dialog.transactions_table.setColumnWidth(4, 220)  # Description
    dialog.transactions_table.setColumnWidth(5, 110)  # Resp Status
    dialog.transactions_table.setColumnWidth(6, 110)  # Dup Status
    dialog.transactions_table.setColumnWidth(7, 130)  # Case Number

    # Connect double-click signal for editing responsibilities
    dialog.transactions_table.itemDoubleClicked.connect(
        lambda item: on_table_double_click(dialog, item)
    )

    # Set minimum row height to accommodate buttons
    dialog.transactions_table.verticalHeader().setDefaultSectionSize(60)

    table_layout.addWidget(dialog.transactions_table)
    table_container.setLayout(table_layout)
    results_layout.addWidget(table_container)

    results_group.setLayout(results_layout)
    layout.addWidget(results_group)

    # Action buttons section
    actions_group = create_professional_groupbox("Import Actions", "red")
    actions_layout = QVBoxLayout()
    actions_layout.setSpacing(15)

    # Workflow buttons
    workflow_layout = QHBoxLayout()
    workflow_layout.setSpacing(12)

    dialog.manage_resp_button = create_professional_button(
        "👥 Manage Responsibilities", "purple"
    )
    dialog.manage_resp_button.clicked.connect(
        lambda: dialog.logic.manage_responsibilities()
    )
    dialog.manage_resp_button.setEnabled(False)
    dialog.manage_resp_button.setMinimumHeight(40)

    dialog.check_duplicates_button = create_professional_button(
        "Check Duplicates", "warning"
    )
    dialog.check_duplicates_button.clicked.connect(
        lambda: dialog.logic.check_duplicates()
    )
    dialog.check_duplicates_button.setEnabled(False)
    dialog.check_duplicates_button.setMinimumHeight(40)

    dialog.assign_case_numbers_button = create_professional_button(
        "🎫 Assign Case Numbers", "info"
    )
    dialog.assign_case_numbers_button.clicked.connect(
        lambda: dialog.logic.assign_case_numbers()
    )
    dialog.assign_case_numbers_button.setEnabled(False)
    dialog.assign_case_numbers_button.setMinimumHeight(45)

    workflow_layout.addWidget(dialog.manage_resp_button)
    workflow_layout.addWidget(dialog.check_duplicates_button)
    workflow_layout.addWidget(dialog.assign_case_numbers_button)
    workflow_layout.addStretch()

    actions_layout.addLayout(workflow_layout)

    # Final action buttons
    final_actions_layout = QHBoxLayout()
    final_actions_layout.addStretch()

    dialog.import_button = create_professional_button("Import Cases", "success")
    dialog.import_button.clicked.connect(lambda: dialog.logic.import_cases())
    dialog.import_button.setEnabled(False)
    dialog.import_button.setMinimumHeight(50)

    dialog.cancel_button = create_professional_button("Cancel", "secondary")

    def _cancel_import():
        # If a worker is running, request cancellation; otherwise close dialog
        if hasattr(dialog, "worker") and dialog.worker is not None:
            try:
                dialog.worker.cancel()
            except Exception:
                pass
        dialog.reject()

    dialog.cancel_button.clicked.connect(_cancel_import)
    dialog.cancel_button.setMinimumHeight(45)

    final_actions_layout.addWidget(dialog.import_button)
    final_actions_layout.addWidget(dialog.cancel_button)

    actions_layout.addLayout(final_actions_layout)
    actions_group.setLayout(actions_layout)
    layout.addWidget(actions_group)


def browse_file(dialog):
    file_path, _ = QFileDialog.getOpenFileName(
        dialog, "Select BAS Report File", "", "Text Files (*.txt);;All Files (*)"
    )
    if file_path:
        dialog.file_path_edit.setText(file_path)
        dialog.bas_file_path = file_path
        dialog.parse_button.setEnabled(bool(dialog.category))


def select_category(dialog):
    dialog_cat = ManageCategoriesDialog(dialog)
    if dialog_cat.exec_():
        selected = dialog_cat.get_selected_category()
        if selected:
            dialog.category = selected
            dialog.category_label.setText(f"Selected: {selected['name']}")
            dialog.category_label.setStyleSheet(
                """
                QLabel {
                    background-color: #d4edda;
                    border: 2px solid #28a745;
                    border-radius: 6px;
                    padding: 8px;
                    color: #155724;
                    font-weight: bold;
                    font-size: 13px;
                }
            """
            )
            dialog.parse_button.setEnabled(bool(dialog.bas_file_path))


def populate_transactions_table(dialog):
    # Save current scroll position
    vertical_scroll_pos = dialog.transactions_table.verticalScrollBar().value()
    horizontal_scroll_pos = dialog.transactions_table.horizontalScrollBar().value()

    dialog.transactions_table.setRowCount(0)

    for i, transaction in enumerate(dialog.transactions):
        row = dialog.transactions_table.rowCount()
        dialog.transactions_table.insertRow(row)

        # Check if transaction is marked for removal
        is_marked_for_removal = transaction.get("marked_for_removal", False)

        # Responsibility - make it visually distinct as clickable
        resp_item = QTableWidgetItem(transaction["responsibility"])
        resp_item.setToolTip("Double-click to edit this responsibility")
        resp_item.setForeground(Qt.blue)  # Make it blue to indicate it's clickable
        font = resp_item.font()
        font.setUnderline(True)  # Underline to show it's a link
        resp_item.setFont(font)

        # Apply removal styling if marked for removal
        if is_marked_for_removal:
            resp_item.setBackground(Qt.red)
            resp_item.setForeground(Qt.white)
            resp_item.setToolTip("This transaction is marked for removal")

        dialog.transactions_table.setItem(row, 0, resp_item)

        # Type
        dialog.transactions_table.setItem(row, 1, QTableWidgetItem(transaction["type"]))

        # Amount - right aligned with comma formatting
        amount_str = f"R{abs(transaction['amount']):,.2f}"
        if transaction["is_credit"]:
            amount_str = f"({amount_str})"  # Show credits in parentheses
        amount_item = QTableWidgetItem(amount_str)
        amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dialog.transactions_table.setItem(row, 2, amount_item)

        # Date
        dialog.transactions_table.setItem(
            row, 3, QTableWidgetItem(transaction["date"].strftime("%Y-%m-%d"))
        )

        # Description
        dialog.transactions_table.setItem(
            row, 4, QTableWidgetItem(transaction["description"])
        )

        # Responsibility Status
        resp_status = validate_responsibility(dialog, transaction["responsibility"])
        status_item = QTableWidgetItem(resp_status["status"])
        if resp_status["status"] == "Not Found":
            status_item.setBackground(Qt.red)
        elif resp_status["status"] == "Non-Posting":
            status_item.setBackground(Qt.yellow)
        else:
            status_item.setBackground(Qt.green)
        dialog.transactions_table.setItem(row, 5, status_item)

        # Duplicate Status
        dup_status = "Not Checked"
        has_duplicates = False
        if hasattr(dialog, "duplicate_check_results") and i < len(
            dialog.duplicate_check_results
        ):
            result = dialog.duplicate_check_results[i]
            if result["duplicates"]:
                dup_status = f"Duplicates: {len(result['duplicates'])}"
                has_duplicates = True
            else:
                dup_status = "No Duplicates"

        # Override status if marked for removal
        if is_marked_for_removal:
            dup_status = "Marked for Removal"

        dup_item = QTableWidgetItem(dup_status)
        if has_duplicates:
            dup_item.setBackground(Qt.yellow)  # Highlight duplicates in yellow
            dup_item.setForeground(Qt.black)
        elif is_marked_for_removal:
            dup_item.setBackground(Qt.red)
            dup_item.setForeground(Qt.white)
        dialog.transactions_table.setItem(row, 6, dup_item)

        # Also highlight the entire row if it has duplicates
        if has_duplicates:
            for col in range(dialog.transactions_table.columnCount()):
                item = dialog.transactions_table.item(row, col)
                if item:
                    item.setBackground(Qt.yellow)
                    item.setForeground(Qt.black)

        # Apply removal styling to entire row if marked for removal
        if is_marked_for_removal:
            for col in range(dialog.transactions_table.columnCount()):
                item = dialog.transactions_table.item(row, col)
                if item:
                    item.setBackground(Qt.red)
                    item.setForeground(Qt.white)

        # Case Number
        case_number = "Not Assigned"
        if "case_number" in transaction and transaction["case_number"]:
            case_number = transaction["case_number"]
        dialog.transactions_table.setItem(row, 7, QTableWidgetItem(case_number))

        # Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(2, 2, 2, 2)

        # View Details button
        view_btn = QPushButton("Details")
        view_btn.setMinimumHeight(35)
        view_btn.setMinimumWidth(70)
        view_btn.clicked.connect(
            lambda checked, trans=transaction: view_transaction_details(dialog, trans)
        )
        actions_layout.addWidget(view_btn)

        # Compare Duplicates button (only if duplicates exist)
        if has_duplicates:
            compare_btn = QPushButton("Compare")
            compare_btn.setMinimumHeight(35)
            compare_btn.setMinimumWidth(70)
            compare_btn.clicked.connect(
                lambda checked, trans=transaction, dups=result[
                    "duplicates"
                ]: compare_duplicates(dialog, trans, dups)
            )
            compare_btn.setStyleSheet(
                "QPushButton { background-color: #FF9800; color: white; }"
            )
            actions_layout.addWidget(compare_btn)

        dialog.transactions_table.setCellWidget(row, 8, actions_widget)

    # Restore scroll position
    dialog.transactions_table.verticalScrollBar().setValue(vertical_scroll_pos)
    dialog.transactions_table.horizontalScrollBar().setValue(horizontal_scroll_pos)


def on_table_double_click(dialog, item):
    """Handle double-click on table items"""
    row = item.row()
    column = item.column()

    # Check if double-click was on the Responsibility column (column 0)
    if column == 0:
        responsibility_name = item.text().strip()
        if responsibility_name and responsibility_name != "Responsibility":
            # Open the edit responsibility dialog for this responsibility
            edit_responsibility_by_name(dialog, responsibility_name)


def view_transaction_details(dialog, transaction):
    """Show detailed view of transaction"""
    details_dialog = TransactionDetailsDialog(transaction, dialog)
    details_dialog.exec_()


def compare_duplicates(dialog, transaction, duplicates):
    """Open duplicate comparison dialog"""
    # Create a copy of the transaction with category name for display
    transaction_copy = transaction.copy()
    transaction_copy["category_name"] = (
        dialog.category["name"] if dialog.category else "N/A"
    )

    # Import the duplicate comparison dialog
    from scripts.case_management_modules.duplicate_comparison_dialog import (
        DuplicateComparisonDialog,
    )

    comp_dialog = DuplicateComparisonDialog(transaction_copy, duplicates, dialog)
    if comp_dialog.exec_():
        resolution = comp_dialog.get_resolution()
        if resolution == "remove":
            # Mark transaction for removal
            transaction["marked_for_removal"] = True
            # Update table display
            populate_transactions_table(dialog)
            QMessageBox.information(
                dialog,
                "Transaction Removed",
                "The transaction has been marked for removal from the import list.",
            )


def manage_responsibilities(dialog):
    resp_dialog = ResponsibilityManagementDialog(dialog)
    resp_dialog.exec_()
    # Refresh validation status after potential changes


def update_progress(dialog, percentage, message):
    dialog.progress_bar.setValue(percentage)
    dialog.results_label.setText(message)


def import_finished(dialog, imported_cases):
    dialog.progress_bar.setVisible(False)
    if not imported_cases:
        QMessageBox.warning(
            dialog,
            "No Cases Imported",
            "No cases were imported. Please review the transactions and try again.",
        )
        dialog.import_button.setEnabled(True)
        return
    QMessageBox.information(
        dialog,
        "Import Complete",
        f"Successfully imported {len(imported_cases)} cases:\n\n"
        + "\n".join(imported_cases[:10])  # Show first 10
        + (
            f"\n... and {len(imported_cases) - 10} more"
            if len(imported_cases) > 10
            else ""
        ),
    )
    dialog.accept()


def import_error(dialog, error_msg):
    dialog.progress_bar.setVisible(False)
    dialog.import_button.setEnabled(True)
    QMessageBox.critical(
        dialog, "Import Error", f"Failed to import cases:\n{error_msg}"
    )


# All functions are now properly implemented or delegated to logic/utils
