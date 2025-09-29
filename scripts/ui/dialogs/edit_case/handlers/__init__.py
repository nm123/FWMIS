"""
Edit Case Dialog Handlers Package

This package contains modularized event handlers for the Edit Case dialog,
organized by functionality for better maintainability and readability.
"""

from .status_handlers import (
    select_responsibility,
    on_status_changed,
    on_assessment_status_changed,
    on_lc_status_changed,
    update_conditional_fields,
)

from .file_handlers import (
    browse_source_doc,
    browse_minutes,
    browse_evidence,
    browse_assessment_evidence,
    browse_recovery_evidence,
    browse_supporting_evidence,
    browse_recovery_evidence_rip,
    view_assessment_evidence,
    view_recovery_evidence,
    view_recovery_evidence_rip,
    view_minutes,
    view_supporting_evidence,
    view_source_doc,
)

from .ui_updaters import (
    update_list_status_grid,
    update_lc_fields_visibility,
)

from .date_handlers import (
    select_bas_payment_date,
    select_bas_journal_date,
    select_latest_installment_date,
    select_new_installment_date,
)

from .recovery_handlers import (
    add_new_installment,
    view_installment_history,
    update_recovery_progress,
    get_original_amount,
    get_current_amount_paid,
    save_installment_to_database,
    finalize_recovery,
    on_save_clicked,
    on_cancel_clicked,
)

__all__ = [
    # Status handlers
    "select_responsibility",
    "on_status_changed",
    "on_assessment_status_changed",
    "on_lc_status_changed",
    "update_conditional_fields",
    # File handlers
    "browse_source_doc",
    "browse_minutes",
    "browse_evidence",
    "browse_assessment_evidence",
    "browse_recovery_evidence",
    "browse_supporting_evidence",
    "browse_recovery_evidence_rip",
    "view_assessment_evidence",
    "view_recovery_evidence",
    "view_recovery_evidence_rip",
    "view_minutes",
    "view_supporting_evidence",
    "view_source_doc",
    # UI updaters
    "update_list_status_grid",
    "update_lc_fields_visibility",
    # Date handlers
    "select_bas_payment_date",
    "select_bas_journal_date",
    "select_latest_installment_date",
    "select_new_installment_date",
    # Recovery handlers
    "add_new_installment",
    "view_installment_history",
    "update_recovery_progress",
    "get_original_amount",
    "get_current_amount_paid",
    "save_installment_to_database",
    "finalize_recovery",
    "on_save_clicked",
    "on_cancel_clicked",
]
