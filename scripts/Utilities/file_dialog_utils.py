"""
File Dialog Utilities for FWMIS

This module provides centralized file dialog functions for consistent file operations
across the entire application.
"""

from typing import Optional

from PyQt5.QtWidgets import QFileDialog, QWidget


def select_file_to_open(
    parent: QWidget,
    title: str = "Select File",
    file_filter: str = "All Files (*.*)",
    initial_dir: Optional[str] = None,
) -> Optional[str]:
    """
    Show a file selection dialog for opening files.

    Args:
        parent: Parent widget
        title: Dialog title
        file_filter: File type filter (e.g., "PDF Files (*.pdf)")
        initial_dir: Initial directory to show

    Returns:
        Optional[str]: Selected file path or None if cancelled
    """
    file_path, _ = QFileDialog.getOpenFileName(
        parent, title, initial_dir or "", file_filter
    )
    return file_path if file_path else None


def select_file_to_save(
    parent: QWidget,
    title: str = "Save File",
    file_filter: str = "All Files (*.*)",
    initial_dir: Optional[str] = None,
    default_filename: Optional[str] = None,
) -> Optional[str]:
    """
    Show a file save dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        file_filter: File type filter
        initial_dir: Initial directory to show
        default_filename: Default filename to suggest

    Returns:
        Optional[str]: Selected file path or None if cancelled
    """
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        title,
        (
            initial_dir or ""
            if not default_filename
            else f"{initial_dir or ''}/{default_filename}"
        ),
        file_filter,
    )
    return file_path if file_path else None


def select_directory(
    parent: QWidget, title: str = "Select Directory", initial_dir: Optional[str] = None
) -> Optional[str]:
    """
    Show a directory selection dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        initial_dir: Initial directory to show

    Returns:
        Optional[str]: Selected directory path or None if cancelled
    """
    directory = QFileDialog.getExistingDirectory(parent, title, initial_dir or "")
    return directory if directory else None


def select_pdf_file(parent: QWidget, title: str = "Select PDF File") -> Optional[str]:
    """
    Show a PDF file selection dialog.

    Args:
        parent: Parent widget
        title: Dialog title

    Returns:
        Optional[str]: Selected PDF file path or None if cancelled
    """
    return select_file_to_open(parent, title, "PDF Files (*.pdf)")


def select_excel_file(
    parent: QWidget, title: str = "Select Excel File"
) -> Optional[str]:
    """
    Show an Excel file selection dialog.

    Args:
        parent: Parent widget
        title: Dialog title

    Returns:
        Optional[str]: Selected Excel file path or None if cancelled
    """
    return select_file_to_open(parent, title, "Excel Files (*.xlsx *.xls)")


def select_csv_file(parent: QWidget, title: str = "Select CSV File") -> Optional[str]:
    """
    Show a CSV file selection dialog.

    Args:
        parent: Parent widget
        title: Dialog title

    Returns:
        Optional[str]: Selected CSV file path or None if cancelled
    """
    return select_file_to_open(parent, title, "CSV Files (*.csv)")


def select_save_pdf_file(
    parent: QWidget,
    title: str = "Save PDF File",
    default_filename: Optional[str] = None,
) -> Optional[str]:
    """
    Show a PDF save dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        default_filename: Default filename (without extension)

    Returns:
        Optional[str]: Selected file path or None if cancelled
    """
    filename = f"{default_filename}.pdf" if default_filename else None
    return select_file_to_save(
        parent, title, "PDF Files (*.pdf)", default_filename=filename
    )


def select_save_excel_file(
    parent: QWidget,
    title: str = "Save Excel File",
    default_filename: Optional[str] = None,
) -> Optional[str]:
    """
    Show an Excel save dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        default_filename: Default filename (without extension)

    Returns:
        Optional[str]: Selected file path or None if cancelled
    """
    filename = f"{default_filename}.xlsx" if default_filename else None
    return select_file_to_save(
        parent, title, "Excel Files (*.xlsx)", default_filename=filename
    )
