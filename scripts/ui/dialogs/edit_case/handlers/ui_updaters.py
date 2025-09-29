"""
UI update handlers for the Edit Case dialog.

This module contains functions for updating UI element visibility and state
based on status changes and other conditions.
"""

from typing import Any


def update_list_status_grid(dialog: Any, list_name: str, status: str) -> None:
    """
    Update list status grid display.

    Args:
        dialog: The EditCaseDialog instance
        list_name: Name of the list being updated
        status: Status to display
    """
    if list_name == "Checklist" and status == "Confirmed":
        # Set LC status in table to "Awaiting LC determination"
        from PyQt5.QtWidgets import QTableWidgetItem

        dialog.list_status_table.setItem(
            1, 1, QTableWidgetItem("Awaiting LC determination")
        )  # Assuming row 1 is LC status
    print(f"Updating grid for {list_name} with status {status}")


def update_lc_fields_visibility(dialog: Any, lc_status: str) -> None:
    """
    Update visibility of LC-specific fields based on LC status.

    Args:
        dialog: The EditCaseDialog instance
        lc_status: The current LC status
    """
    print(f"LC fields updated for status: {lc_status}")

    # Update LC Committee Date visibility - show when LC status is set
    if hasattr(dialog, "lc_committee_date_label") and hasattr(
        dialog, "lc_committee_date_edit"
    ):
        lc_date_visible = bool(lc_status and lc_status.strip())
        dialog.lc_committee_date_label.setVisible(lc_date_visible)
        dialog.lc_committee_date_edit.setVisible(lc_date_visible)

    # Update recovery group visibility based on LC status
    if hasattr(dialog, "recovery_group"):
        if lc_status == "Recovery in Progress":
            dialog.recovery_group.setVisible(True)
            # Initialize recovery progress when group becomes visible
            from .recovery_handlers import update_recovery_progress

            update_recovery_progress(dialog)
        else:
            dialog.recovery_group.setVisible(False)

    # Update recovery fields visibility based on LC status
    if lc_status == "Recovery in Progress":
        # Show recovery fields for installment tracking
        if hasattr(dialog, "debtor_name_edit"):
            dialog.debtor_name_edit.setVisible(True)
        if hasattr(dialog, "debtor_number_edit"):
            dialog.debtor_number_edit.setVisible(True)
        if hasattr(dialog, "debt_number_edit"):
            dialog.debt_number_edit.setVisible(True)

        # Hide Loss Control Committee recovery evidence, show Recovery in Progress recovery evidence
        if hasattr(dialog, "recovery_evidence_label"):
            dialog.recovery_evidence_label.setVisible(False)
        if hasattr(dialog, "recovery_evidence_edit"):
            dialog.recovery_evidence_edit.setVisible(False)
        if hasattr(dialog, "recovery_evidence_button"):
            dialog.recovery_evidence_button.setVisible(False)
        if hasattr(dialog, "recovery_evidence_view_button"):
            dialog.recovery_evidence_view_button.setVisible(False)

        # Show Recovery in Progress recovery evidence
        if hasattr(dialog, "recovery_evidence_rip_label"):
            dialog.recovery_evidence_rip_label.setVisible(True)
        if hasattr(dialog, "recovery_evidence_rip_edit"):
            dialog.recovery_evidence_rip_edit.setVisible(True)
            dialog.recovery_evidence_rip_edit.setPlaceholderText(
                "Upload latest Debt Inquiry report"
            )
        if hasattr(dialog, "recovery_evidence_rip_button"):
            dialog.recovery_evidence_rip_button.setVisible(True)
        if hasattr(dialog, "recovery_evidence_rip_view_button"):
            dialog.recovery_evidence_rip_view_button.setVisible(True)

        if hasattr(dialog, "minutes_edit"):
            dialog.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")

    elif lc_status == "Recovered":
        # Hide installment fields, show only total recovered
        if hasattr(dialog, "debtor_name_edit"):
            dialog.debtor_name_edit.setVisible(False)
        if hasattr(dialog, "debtor_number_edit"):
            dialog.debtor_number_edit.setVisible(False)
        if hasattr(dialog, "debt_number_edit"):
            dialog.debt_number_edit.setVisible(False)

        # Show Loss Control Committee recovery evidence, hide Recovery in Progress recovery evidence
        if hasattr(dialog, "recovery_evidence_label"):
            dialog.recovery_evidence_label.setVisible(True)
        if hasattr(dialog, "recovery_evidence_edit"):
            dialog.recovery_evidence_edit.setVisible(True)
            dialog.recovery_evidence_edit.setPlaceholderText(
                "Recovery Evidence is REQUIRED"
            )
        if hasattr(dialog, "recovery_evidence_button"):
            dialog.recovery_evidence_button.setVisible(True)
        if hasattr(dialog, "recovery_evidence_view_button"):
            dialog.recovery_evidence_view_button.setVisible(True)

        # Hide Recovery in Progress recovery evidence
        if hasattr(dialog, "recovery_evidence_rip_label"):
            dialog.recovery_evidence_rip_label.setVisible(False)
        if hasattr(dialog, "recovery_evidence_rip_edit"):
            dialog.recovery_evidence_rip_edit.setVisible(False)
        if hasattr(dialog, "recovery_evidence_rip_button"):
            dialog.recovery_evidence_rip_button.setVisible(False)
        if hasattr(dialog, "recovery_evidence_rip_view_button"):
            dialog.recovery_evidence_rip_view_button.setVisible(False)
        if hasattr(dialog, "minutes_edit"):
            dialog.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")

    elif lc_status == "Write Off Recommended":
        # Hide all recovery fields
        if hasattr(dialog, "debtor_name_edit"):
            dialog.debtor_name_edit.setVisible(False)
        if hasattr(dialog, "debtor_number_edit"):
            dialog.debtor_number_edit.setVisible(False)
        if hasattr(dialog, "debt_number_edit"):
            dialog.debt_number_edit.setVisible(False)

        if hasattr(dialog, "recovery_evidence_label"):
            dialog.recovery_evidence_label.setVisible(False)
        if hasattr(dialog, "recovery_evidence_edit"):
            dialog.recovery_evidence_edit.setVisible(False)
        if hasattr(dialog, "recovery_evidence_button"):
            dialog.recovery_evidence_button.setVisible(False)
        if hasattr(dialog, "recovery_evidence_view_button"):
            dialog.recovery_evidence_view_button.setVisible(False)
        if hasattr(dialog, "recovery_evidence_edit"):
            dialog.recovery_evidence_edit.clear()
            dialog.recovery_evidence_edit.setPlaceholderText("")
        if hasattr(dialog, "minutes_edit"):
            dialog.minutes_edit.setPlaceholderText("Loss Control Minutes are REQUIRED")

    else:
        # Hide all recovery fields for other statuses
        if hasattr(dialog, "debtor_name_edit"):
            dialog.debtor_name_edit.setVisible(False)
        if hasattr(dialog, "debtor_number_edit"):
            dialog.debtor_number_edit.setVisible(False)
        if hasattr(dialog, "debt_number_edit"):
            dialog.debt_number_edit.setVisible(False)

        if hasattr(dialog, "recovery_evidence_label"):
            dialog.recovery_evidence_label.setVisible(False)
        if hasattr(dialog, "recovery_evidence_edit"):
            dialog.recovery_evidence_edit.setVisible(False)
        if hasattr(dialog, "recovery_evidence_button"):
            dialog.recovery_evidence_button.setVisible(False)
        if hasattr(dialog, "recovery_evidence_view_button"):
            dialog.recovery_evidence_view_button.setVisible(False)
        if hasattr(dialog, "recovery_evidence_edit"):
            dialog.recovery_evidence_edit.clear()
            dialog.recovery_evidence_edit.setPlaceholderText("")
        if hasattr(dialog, "minutes_edit"):
            dialog.minutes_edit.setPlaceholderText("")
