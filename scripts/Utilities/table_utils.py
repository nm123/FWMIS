"""
Table Utilities for FWMIS

This module provides utilities for common table operations and data population.
"""

from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem


def populate_table_from_data(
    table: QTableWidget, data: List[List[Any]], headers: Optional[List[str]] = None
) -> None:
    """
    Populate a table widget with data.

    Args:
        table: The QTableWidget to populate
        data: List of rows, each row is a list of cell values
        headers: Optional column headers
    """
    if not data:
        table.setRowCount(0)
        return

    table.setRowCount(len(data))
    table.setColumnCount(len(data[0]))

    if headers:
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

    for row_idx, row_data in enumerate(data):
        for col_idx, cell_value in enumerate(row_data):
            item = QTableWidgetItem(str(cell_value) if cell_value is not None else "")
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            table.setItem(row_idx, col_idx, item)


def clear_table(table: QTableWidget) -> None:
    """
    Clear all data from a table widget.

    Args:
        table: The QTableWidget to clear
    """
    table.clearContents()
    table.setRowCount(0)


def get_selected_table_row(table: QTableWidget) -> Optional[int]:
    """
    Get the currently selected row index.

    Args:
        table: The QTableWidget to check

    Returns:
        Optional[int]: Selected row index or None if no selection
    """
    selected_items = table.selectedItems()
    if not selected_items:
        return None
    return selected_items[0].row()


def get_table_row_data(table: QTableWidget, row: int) -> List[str]:
    """
    Get all cell data from a specific table row.

    Args:
        table: The QTableWidget
        row: Row index

    Returns:
        List[str]: List of cell values as strings
    """
    row_data = []
    for col in range(table.columnCount()):
        item = table.item(row, col)
        row_data.append(item.text() if item else "")
    return row_data


def set_table_cell_value(
    table: QTableWidget, row: int, col: int, value: Any, editable: bool = False
) -> None:
    """
    Set a specific cell value in the table.

    Args:
        table: The QTableWidget
        row: Row index
        col: Column index
        value: Value to set
        editable: Whether the cell should be editable
    """
    item = QTableWidgetItem(str(value) if value is not None else "")
    if not editable:
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    table.setItem(row, col, item)


def resize_table_columns_to_contents(table: QTableWidget) -> None:
    """
    Resize table columns to fit their contents.

    Args:
        table: The QTableWidget to resize
    """
    table.resizeColumnsToContents()
    table.resizeRowsToContents()


def setup_table_with_headers(
    table: QTableWidget,
    headers: List[str],
    column_widths: Optional[Dict[int, int]] = None,
) -> None:
    """
    Setup table with headers and optional column widths.

    Args:
        table: The QTableWidget to setup
        headers: List of header labels
        column_widths: Optional dict mapping column index to width
    """
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)

    if column_widths:
        for col_idx, width in column_widths.items():
            if col_idx < len(headers):
                table.setColumnWidth(col_idx, width)


def add_table_row(table: QTableWidget, row_data: List[Any]) -> int:
    """
    Add a new row to the table.

    Args:
        table: The QTableWidget
        row_data: List of cell values for the new row

    Returns:
        int: The row index of the newly added row
    """
    row_idx = table.rowCount()
    table.insertRow(row_idx)

    for col_idx, cell_value in enumerate(row_data):
        if col_idx < table.columnCount():
            set_table_cell_value(table, row_idx, col_idx, cell_value)

    return row_idx


def remove_table_row(table: QTableWidget, row: int) -> None:
    """
    Remove a row from the table.

    Args:
        table: The QTableWidget
        row: Row index to remove
    """
    if 0 <= row < table.rowCount():
        table.removeRow(row)
