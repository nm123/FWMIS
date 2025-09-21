# Import everything from the new modular utilities for backward compatibility
from .config import BASE_DIR, DATA_DIR, DB_PATH, logging
from .financial_utils import get_financial_year, generate_transaction_no, create_year_folder
from .audit_utils import save_audit_log
from .contact_utils import get_effective_contacts
from .validation_utils import is_valid_email
from .tree_utils import get_subtree_resp_ids
from .category_utils import load_categories, save_categories
from .email_utils import load_email_templates, save_email_templates
from .responsibility_utils import load_responsibilities, load_posting_responsibilities
from .list_utils import load_lists, save_lists
from .case_utils import load_cases

def format_currency_amount(amount, include_currency=False, right_align=False):
    """
    Format a currency amount consistently throughout the application.

    Args:
        amount: Numeric amount to format
        include_currency: Whether to include 'R' prefix (default: False)
        right_align: Whether this is for a table item that should be right-aligned

    Returns:
        If right_align=True: QTableWidgetItem with right alignment
        If right_align=False: Formatted string
    """
    if amount is None or amount == 0 or amount == "0" or amount == "":
        formatted = "0.00"
    else:
        try:
            numeric_amount = float(amount) if isinstance(amount, str) else amount
            abs_amount = abs(numeric_amount)
            if include_currency:
                formatted = f"R {abs_amount:,.2f}"
            else:
                formatted = f"{abs_amount:,.2f}"
        except (ValueError, TypeError):
            formatted = "0.00"

    if right_align:
        from PyQt5.QtWidgets import QTableWidgetItem
        from PyQt5.QtCore import Qt
        item = QTableWidgetItem(formatted)
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return item
    else:
        return formatted

# Re-export all functions and variables for backward compatibility
__all__ = [
    'BASE_DIR', 'DATA_DIR', 'DB_PATH', 'logging',
    'get_financial_year', 'generate_transaction_no', 'create_year_folder',
    'save_audit_log', 'get_effective_contacts', 'is_valid_email',
    'get_subtree_resp_ids', 'load_categories', 'save_categories',
    'load_email_templates', 'save_email_templates',
    'load_responsibilities', 'load_posting_responsibilities',
    'load_lists', 'save_lists', 'load_cases', 'format_currency_amount'
]