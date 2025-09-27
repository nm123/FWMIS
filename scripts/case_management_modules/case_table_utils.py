"""
Shared utilities for case table display in View Cases and Edit Cases dialogs.
Ensures consistent list and status display.
"""

import sqlite3
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QPushButton, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget, QHBoxLayout, QLabel)
from scripts.Utilities.config import DB_PATH
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

        # Get is_finalized status for To-Do logic
        is_finalized = False
        try:
            conn_temp = sqlite3.connect(DB_PATH)
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute("SELECT is_finalized FROM cases WHERE transaction_no = ?", (transaction_no,))
            result = cursor_temp.fetchone()
            if result:
                is_finalized = bool(result[0])
            conn_temp.close()
        except Exception as e:
            print(f"Error getting finalized status for {transaction_no}: {e}")
            is_finalized = False

        # Case No (with suffix stripping for display)
        display_value = transaction_no
        if display_value and list_name != "All Cases":
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

        # Amount - calculate based on list type
        display_amount = calculate_display_amount(amount, suffixes, list_name, transaction_no)
        amount_item = format_currency_amount(display_amount, right_align=True)
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
            if "-RIP" in suffixes:
                status_value = "Recovery in Progress"
            else:
                status_value = lc_status or "Awaiting LC determination"
        elif list_name == "Recovery in Progress":
            status_value = "In progress"
        elif list_name == "Recovered":
            if "-REC" in suffixes:
                status_value = "Recovered"
            else:
                status_value = "In progress"  # Partially recovered cases
        elif list_name == "Write-Off Recommended":
            status_value = "Write-Off Recommended"
        elif list_name == "Written Off":
            status_value = "Written Off"
        else:
            status_value = assessment_status
        table.setItem(row, 5, QTableWidgetItem(status_value))

        # To-Do (view-specific logic)
        if list_name == "Checklist":
            if is_finalized:
                todo_value = "No - Case is finalised"
            elif assessment_status in ["Alleged", "Under Assessment"]:
                todo_value = "Yes - Assessment Outstanding"
            elif assessment_status == "Valid":
                todo_value = "No - Case is finalised"
            elif assessment_status == "Confirmed":
                todo_value = "Yes - Refer Lead Schedule"
            else:
                todo_value = "No"  # Fallback for any other status
        elif list_name == "Lead Schedule":
            if "-RIP" in suffixes:
                todo_value = "Yes - refer Recovery in progress"
            elif lc_status == "Awaiting LC determination":
                todo_value = "Yes - LC Minutes Outstanding"
            elif lc_status == "Recovered":
                todo_value = "No - Case is finalised"
            elif lc_status == "Write-Off Recommended":
                todo_value = "Yes - Refer Write-Off Recommended list"
            else:
                todo_value = "No"  # Fallback for any other status
        elif list_name == "Recovery in Progress":
            todo_value = "Yes - update latest installment"
        elif list_name == "Recovered":
            todo_value = "No"  # Recovery in Progress list already tells user what to do
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


def calculate_display_amount(original_amount, suffixes, list_name, transaction_no):
    """
    Calculate the display amount based on list type and recovery status.
    
    Args:
        original_amount (float): Original case amount
        suffixes (str): Case suffixes (e.g., "-LS,-RIP")
        list_name (str): Name of the list view
        transaction_no (str): Transaction number for database lookup
        
    Returns:
        float: Amount to display in the list view
    """
    try:
        # For Checklist, always show original amount
        if list_name == "Checklist":
            return original_amount
        
        # For Recovery in Progress list, show remaining balance
        if list_name == "Recovery in Progress":
            amount_paid = get_total_installments_paid(transaction_no)
            remaining = original_amount - amount_paid
            return max(0.0, remaining)  # Don't show negative amounts
        
        # For Recovered list, show amount recovered so far (or original amount if no installments)
        if list_name == "Recovered":
            amount_paid = get_total_installments_paid(transaction_no)
            # If no installments, show original amount (fully recovered without installments)
            return amount_paid if amount_paid > 0 else original_amount
        
        # For Lead Schedule, show remaining balance if in recovery
        if list_name == "Lead Schedule" and "-RIP" in suffixes:
            amount_paid = get_total_installments_paid(transaction_no)
            remaining = original_amount - amount_paid
            return max(0.0, remaining)
        
        # For all other lists, show original amount
        return original_amount
        
    except Exception as e:
        print(f"Error calculating display amount: {e}")
        return original_amount


def get_total_installments_paid(transaction_no):
    """
    Get total amount paid from installments table.
    
    Args:
        transaction_no (str): Transaction number
        
    Returns:
        float: Total amount paid in installments
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get case ID from transaction number
        cursor.execute("SELECT id FROM cases WHERE transaction_no = ?", (transaction_no,))
        case_result = cursor.fetchone()
        
        if not case_result:
            conn.close()
            return 0.0
        
        case_id = case_result[0]
        
        # Get total from installments
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM installments WHERE case_id = ?",
            (case_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        return float(result[0]) if result else 0.0
        
    except Exception as e:
        print(f"Error getting installments total: {e}")
        return 0.0


def calculate_list_totals(list_name, fy_id=None):
    """
    Calculate totals for a specific list view.
    
    Args:
        list_name (str): Name of the list view
        fy_id (int): Financial year ID (optional)
        
    Returns:
        tuple: (total_count, total_amount, explanation)
    """
    # Default values
    total_count = 0
    total_amount = 0.0
    explanation = "Total for all cases"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Base query with financial year filter if provided
        base_where = "WHERE fy_id = ?" if fy_id else ""
        params = [fy_id] if fy_id else []
        
        if list_name == "Checklist":
            # Total (Confirmed) - new cases for the reporting period
            query = f"""
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM cases 
                {base_where}
                AND assessment_status = 'Confirmed'
            """
            explanation = "Total (Confirmed) - Reconciliation: New cases for the reporting period"
            
        elif list_name == "Lead Schedule":
            # Lead Schedule shows active cases (already accounts for recovered/written off)
            query = f"""
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM cases 
                {base_where}
                AND suffixes LIKE '%-LS%' 
                AND suffixes NOT LIKE '%-REC%' 
                AND suffixes NOT LIKE '%-WO'
            """
            explanation = "Total (Checklist - Recovered - Written Off) - Reconciliation: Movement for the reporting period"
            
        elif list_name == "Recovery in Progress":
            # Show remaining balances for cases in recovery
            query = f"""
                SELECT COUNT(*), COALESCE(SUM(
                    CASE 
                        WHEN EXISTS (SELECT 1 FROM installments WHERE installments.case_id = cases.id) 
                        THEN amount - COALESCE((SELECT SUM(amount) FROM installments WHERE installments.case_id = cases.id), 0)
                        ELSE amount 
                    END
                ), 0)
                FROM cases 
                {base_where}
                AND suffixes LIKE '%-RIP%'
            """
            explanation = "Total remaining balances for cases in recovery"
            
        elif list_name == "Recovered":
            # Show total amounts recovered
            query = f"""
                SELECT COUNT(*), COALESCE(SUM(
                    CASE 
                        WHEN EXISTS (SELECT 1 FROM installments WHERE installments.case_id = cases.id) 
                        THEN COALESCE((SELECT SUM(amount) FROM installments WHERE installments.case_id = cases.id), 0)
                        ELSE amount 
                    END
                ), 0)
                FROM cases 
                {base_where}
                AND (suffixes LIKE '%-REC%' OR EXISTS (SELECT 1 FROM installments WHERE installments.case_id = cases.id))
            """
            explanation = "Total amounts recovered to date - Reconciliation: Cases recovered during the reporting period"
            
        elif list_name == "Write-Off Recommended":
            query = f"""
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM cases 
                {base_where}
                AND suffixes LIKE '%-WOR%'
            """
            explanation = "Total amounts recommended for write-off"
            
        elif list_name == "Written Off":
            query = f"""
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM cases 
                {base_where}
                AND suffixes LIKE '%-WO'
            """
            explanation = "Total amounts written off - Reconciliation: Cases written off during the reporting period"
            
        else:
            # Default: show all cases
            query = f"""
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM cases 
                {base_where}
            """
            explanation = "Total for all cases"
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        
        if result:
            total_count = result[0] if result[0] is not None else 0
            total_amount = float(result[1]) if result[1] is not None else 0.0
        
    except Exception as e:
        print(f"Error calculating list totals: {e}")
        # Return safe defaults instead of error message
    
    return total_count, total_amount, explanation


def create_totals_widget(list_name, fy_id=None):
    """
    Create a totals widget for a list view.
    
    Args:
        list_name (str): Name of the list view
        fy_id (int): Financial year ID (optional)
        
    Returns:
        QWidget: Widget containing totals display
    """
    # Get totals with fallback to safe defaults
    total_count, total_amount, explanation = calculate_list_totals(list_name, fy_id)
    
    # Create totals widget
    totals_widget = QWidget()
    totals_layout = QHBoxLayout(totals_widget)
    totals_layout.setContentsMargins(10, 5, 10, 5)
    
    # Total count
    count_label = QLabel(f"Total No: {total_count}")
    count_label.setStyleSheet("""
        QLabel {
            font-weight: bold;
            color: #2c5aa0;
            padding: 5px;
            background-color: #f0f8ff;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
    """)
    
    # Total amount - safe formatting
    try:
        formatted_amount = format_currency_amount(total_amount)
    except:
        formatted_amount = f"R {total_amount:,.2f}"
    
    amount_label = QLabel(f"Total Amt: {formatted_amount}")
    amount_label.setStyleSheet("""
        QLabel {
            font-weight: bold;
            color: #2d7d32;
            padding: 5px;
            background-color: #f1f8e9;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
    """)
    
    # Explanation
    explanation_label = QLabel(explanation)
    explanation_label.setStyleSheet("""
        QLabel {
            color: #666;
            font-style: italic;
            padding: 5px;
        }
    """)
    
    totals_layout.addWidget(count_label)
    totals_layout.addWidget(amount_label)
    totals_layout.addWidget(explanation_label)
    totals_layout.addStretch()
    
    return totals_widget
