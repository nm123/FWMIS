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

# Re-export all functions and variables for backward compatibility
__all__ = [
    'BASE_DIR', 'DATA_DIR', 'DB_PATH', 'logging',
    'get_financial_year', 'generate_transaction_no', 'create_year_folder',
    'save_audit_log', 'get_effective_contacts', 'is_valid_email',
    'get_subtree_resp_ids', 'load_categories', 'save_categories',
    'load_email_templates', 'save_email_templates',
    'load_responsibilities', 'load_posting_responsibilities',
    'load_lists', 'save_lists', 'load_cases'
]