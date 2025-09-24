"""
Shared utilities for case table display in View Cases and Edit Cases dialogs.
Ensures consistent list and status display.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QPushButton, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget)
from scripts.Utilities.utils import format_currency_amount
from scripts.Utilities.db_utils import get_db_connection


def create_table_button(text):
    """Create a simple, visible button for table cells"""
    button = QPushButton(text)
    button.setFixedSize(50, 20)  # Slightly larger for visibility
    button.setStyleSheet(
        """
        QPushButton {
            background-color: #007bff;
            color: white;
            border: 1px solid #007bff;
            border-radius: 3px;
            font-size: 11px;
            padding: 2px;
            margin-top: 4px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:pressed {
            background-color: #004085;
        }
    """
    )
    return button


def setup_case_table_columns(table, include_edit=False):
    """
    Set up table columns for case display.

    Args:
        table (QTableWidget): The table to configure.
        include_edit (bool): Whether to include Edit Case column.
    """
    headers = [
        "Case No",
        "Date Reported",
        "Category",
        "Amount",
        "List",
        "Status",
        "To-Do",
    ]
    if include_edit:
        headers.append("Edit Case")
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    # Set column widths (match existing)
    table.setColumnWidth(0, 120)  # Case No
    table.setColumnWidth(1, 140)  # Date Reported
    table.setColumnWidth(2, 150)  # Category
    table.setColumnWidth(3, 120)  # Amount
    table.setColumnWidth(4, 120)  # List
    table.setColumnWidth(5, 120)  # Status
    table.setColumnWidth(6, 200)  # To-Do (increased for longer text)
    if include_edit:
        table.setColumnWidth(7, 90)  # Edit Case
    table.verticalHeader().setDefaultSectionSize(80)  # Further increased for wrapped text visibility
    
    # Enable text wrapping for To-Do column (column 6)
    table.setWordWrap(True)


def populate_case_table(
    table, cases, list_name, include_edit=False, edit_callback=None
):
    """
    Populate the table with case data, using consistent display logic.

    Args:
        table (QTableWidget): The table to populate.
        cases (list): List of case data tuples.
        list_name (str): Name of the list view (e.g., "Checklist").
        include_edit (bool): Whether to add Edit buttons.
    """
    table.setRowCount(0)
    for case_data in cases:
        row = table.rowCount()
        table.insertRow(row)

        # Extract fields (adjust indices based on query: transaction_no, date_reported, category, amount, assessment_status, lc_status, suffixes, bas_payment_no, bas_journal_no)
        transaction_no = case_data[0]
        date_reported = case_data[1]
        category = case_data[2]
        amount = case_data[3]
        assessment_status = case_data[4]
        lc_status = case_data[5] if len(case_data) > 5 else None
        suffixes = case_data[6] if len(case_data) > 6 else ""
        bas_payment_no = case_data[7] if len(case_data) > 7 else None
        bas_journal_no = case_data[8] if len(case_data) > 8 else None

        # Case No (with suffix stripping for display)
        display_value = transaction_no
        if list_name != "All Cases":
            while any(
                display_value.endswith(s) for s in ["-LS", "-WOR", "-REC", "-WO"]
            ):
                display_value = display_value.rsplit("-", 1)[0]
        case_item = QTableWidgetItem(str(display_value) if display_value else "")
        case_item.setData(Qt.UserRole, transaction_no)
        table.setItem(row, 0, case_item)

        # Date Reported
        table.setItem(
            row, 1, QTableWidgetItem(str(date_reported) if date_reported else "")
        )

        # Category
        table.setItem(row, 2, QTableWidgetItem(str(category) if category else ""))

        # Amount
        amount_item = format_currency_amount(amount, right_align=True)
        table.setItem(row, 3, amount_item)

        # List (view-specific)
        if list_name == "All Cases":
            if "-WO" in suffixes:
                list_value = "Written Off"
            elif "-REC" in suffixes:
                list_value = "Recovered"
            elif "-WOR" in suffixes:
                list_value = "Write-Off Recommended"
            elif "-LS" in suffixes:
                list_value = "Lead Schedule"
            else:
                list_value = "Checklist"
        else:
            list_value = list_name
        table.setItem(row, 4, QTableWidgetItem(list_value))

        # Status (view-specific)
        if list_name == "Checklist":
            status_value = assessment_status
        elif list_name == "Lead Schedule":
            status_value = lc_status or "Awaiting LC determination"
        elif list_name == "Recovered":
            status_value = "Recovered"
        elif list_name == "Write-Off Recommended":
            status_value = "Write-Off Recommended"
        elif list_name == "Written Off":
            status_value = "Written Off"
        else:
            status_value = assessment_status
        table.setItem(row, 5, QTableWidgetItem(status_value))

        # To-Do (view-specific logic)
        if list_name == "Checklist":
            if assessment_status in ["Alleged", "Under Assessment"]:
                todo_value = "Yes - Assessment Outstanding"
            elif assessment_status == "Valid":
                todo_value = "No - Case is finalised"
            elif assessment_status == "Confirmed":
                todo_value = "Yes - Refer Lead Schedule"
            else:
                todo_value = "No"  # Fallback for any other status
        elif list_name == "Lead Schedule":
            if lc_status == "Awaiting LC determination":
                todo_value = "Yes - LC Minutes Outstanding"
            elif lc_status == "Recovered":
                todo_value = "No - Case is finalised"
            elif lc_status == "Write-Off Recommended":
                todo_value = "Yes - Refer Write-Off Recommended list"
            else:
                todo_value = "No"  # Fallback for any other status
        elif list_name == "Write-Off Recommended":
            # Check if case is in an annexure
            annexure_info = get_case_annexure_info(transaction_no)
            if annexure_info:
                todo_value = f"In annexure {annexure_info['annexure_no']}"
            else:
                todo_value = "Awaiting annexure preparation"
        else:
            # For other views, use the original logic
            todo_value = "Yes" if bas_payment_no or bas_journal_no else "No"
        # Create To-Do item with text wrapping
        todo_item = QTableWidgetItem(todo_value)
        todo_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, 6, todo_item)

        # Edit Case (if enabled)
        if include_edit:
            edit_button = create_table_button("Edit")
            if edit_callback:
                edit_button.clicked.connect(lambda checked, r=row: edit_callback(r))
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(edit_button, alignment=Qt.AlignCenter)
            table.setCellWidget(row, 7, container)


def get_case_annexure_info(transaction_no):
    """Get annexure information for a case."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.annexure_no, a.role
                FROM annexures a
                JOIN annexure_cases ac ON a.id = ac.annexure_id
                JOIN cases c ON ac.case_id = c.id
                WHERE c.transaction_no = ?
            """, (transaction_no,))
            
            row = cursor.fetchone()
            if row:
                return {'annexure_no': row[0], 'role': row[1]}
            return None
    except Exception as e:
        print(f"Error getting annexure info: {e}")
        return None
