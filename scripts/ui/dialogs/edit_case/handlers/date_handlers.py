"""
Date selection handlers for the Edit Case dialog.

This module contains functions for handling date selection dialogs
and calendar popup interactions.
"""

from typing import Any

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QCalendarWidget, QDialog, QVBoxLayout


def select_bas_payment_date(dialog: Any) -> None:
    """Select BAS payment date using calendar dialog."""
    print("BAS payment date selection")


def select_bas_journal_date(dialog: Any) -> None:
    """Select BAS journal date using calendar dialog."""
    print("BAS journal date selection")


def select_latest_installment_date(dialog: Any) -> None:
    """
    Select latest installment date using date picker.

    Args:
        dialog: The EditCaseDialog instance
    """
    calendar_dialog = QDialog(dialog)
    calendar_dialog.setWindowTitle("Select Latest Installment Date")
    calendar_dialog.setFixedSize(300, 250)

    layout = QVBoxLayout(calendar_dialog)
    calendar = QCalendarWidget()
    layout.addWidget(calendar)

    def on_date_selected():
        selected_date = calendar.selectedDate()
        dialog.latest_installment_date_edit.setText(
            selected_date.toString("yyyy-MM-dd")
        )
        calendar_dialog.accept()

    calendar.clicked.connect(on_date_selected)
    calendar_dialog.exec_()
    print("Latest installment date selection")


def select_new_installment_date(dialog: Any) -> None:
    """
    Handle new installment date selection with calendar popup.

    Args:
        dialog: The EditCaseDialog instance
    """
    calendar_dialog = QDialog(dialog)
    calendar_dialog.setWindowTitle("Select Installment Date")
    calendar_dialog.setFixedSize(300, 300)

    layout = QVBoxLayout(calendar_dialog)
    calendar = QCalendarWidget()
    layout.addWidget(calendar)

    def on_date_selected():
        selected_date = calendar.selectedDate()
        dialog.new_installment_date_edit.setText(selected_date.toString("yyyy-MM-dd"))
        calendar_dialog.accept()

    calendar.clicked.connect(on_date_selected)
    calendar_dialog.exec_()
