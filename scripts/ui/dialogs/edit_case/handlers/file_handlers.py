"""
File handling handlers for the Edit Case dialog.

This module contains all event handlers related to file browsing and viewing
operations in the Edit Case dialog.
"""

import os
from typing import Any

from scripts.Utilities.file_dialog_utils import select_pdf_file


def browse_source_doc(dialog: Any) -> None:
    """Handle browsing for source document."""
    file_path = select_pdf_file(dialog, "Select Source Document")
    if file_path:
        dialog.source_doc_edit.setText(file_path)


def browse_minutes(dialog: Any) -> None:
    """Handle browsing for minutes."""
    file_path = select_pdf_file(dialog, "Select Minutes")
    if file_path:
        dialog.minutes_edit.setText(file_path)


def browse_evidence(dialog: Any) -> None:
    """Handle browsing for evidence."""
    file_path = select_pdf_file(dialog, "Select Evidence")
    if file_path:
        print(f"Setting evidence_edit to: {file_path}")
        dialog.evidence_edit.setText(file_path)
        print(f"evidence_edit text: {dialog.evidence_edit.text()}")


def browse_assessment_evidence(dialog: Any) -> None:
    """Handle browsing for assessment evidence."""
    file_path = select_pdf_file(dialog, "Select Assessment Evidence")
    if file_path:
        print(f"Setting assessment_evidence_edit to: {file_path}")
        dialog.assessment_evidence_edit.setText(file_path)
        print(
            f"assessment_evidence_edit text: {dialog.assessment_evidence_edit.text()}"
        )


def browse_recovery_evidence(dialog: Any) -> None:
    """Handle browsing for recovery evidence."""
    file_path = select_pdf_file(dialog, "Select Recovery Evidence")
    if file_path:
        dialog.recovery_evidence_edit.setText(file_path)


def browse_supporting_evidence(dialog: Any) -> None:
    """Handle browsing for supporting evidence."""
    file_path = select_pdf_file(dialog, "Select Supporting Evidence")
    if file_path:
        dialog.supporting_evidence_edit.setText(file_path)


def browse_recovery_evidence_rip(dialog: Any) -> None:
    """Handle browsing for recovery evidence in Recovery in Progress group."""
    file_path = select_pdf_file(dialog, "Select Recovery Evidence")
    if file_path:
        dialog.recovery_evidence_rip_edit.setText(file_path)


def view_assessment_evidence(dialog: Any) -> None:
    """View assessment evidence file."""
    if (
        hasattr(dialog, "assessment_evidence_edit")
        and dialog.assessment_evidence_edit.text()
    ):
        os.startfile(dialog.assessment_evidence_edit.text())


def view_recovery_evidence(dialog: Any) -> None:
    """View recovery evidence file."""
    if (
        hasattr(dialog, "recovery_evidence_edit")
        and dialog.recovery_evidence_edit.text()
    ):
        os.startfile(dialog.recovery_evidence_edit.text())


def view_recovery_evidence_rip(dialog: Any) -> None:
    """View recovery evidence file in Recovery in Progress group."""
    if (
        hasattr(dialog, "recovery_evidence_rip_edit")
        and dialog.recovery_evidence_rip_edit.text()
    ):
        os.startfile(dialog.recovery_evidence_rip_edit.text())


def view_minutes(dialog: Any) -> None:
    """View minutes file."""
    if hasattr(dialog, "minutes_edit") and dialog.minutes_edit.text():
        os.startfile(dialog.minutes_edit.text())


def view_supporting_evidence(dialog: Any) -> None:
    """View supporting evidence file."""
    if (
        hasattr(dialog, "supporting_evidence_edit")
        and dialog.supporting_evidence_edit.text()
    ):
        os.startfile(dialog.supporting_evidence_edit.text())


def view_source_doc(dialog: Any) -> None:
    """View source document file."""
    if hasattr(dialog, "source_doc_edit") and dialog.source_doc_edit.text():
        os.startfile(dialog.source_doc_edit.text())
