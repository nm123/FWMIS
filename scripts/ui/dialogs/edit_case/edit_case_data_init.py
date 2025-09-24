"""
Data initialization utilities for EditCaseDialog.
Handles loading responsibilities, categories, lists, financial year, and extracting case fields.
"""

from scripts.case_management_modules.case_business_logic import \
    CaseBusinessLogic
from scripts.Utilities.category_utils import load_categories
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.list_utils import load_lists
from scripts.Utilities.responsibility_utils import (
    load_posting_responsibilities, load_responsibilities)
from scripts.Utilities.workflow_utils import get_case_workflow_status


def initialize_case_data(dialog_instance, case_data, selected_list):
    """
    Initialize case data for the EditCaseDialog.

    Args:
        dialog_instance: The EditCaseDialog instance.
        case_data: The case data (dict or tuple).
        selected_list: The selected list name.
    """
    dialog_instance.responsibilities = load_posting_responsibilities()
    dialog_instance.categories = load_categories()
    dialog_instance.lists = load_lists()
    dialog_instance.fy = get_financial_year()
    dialog_instance.case_data = case_data
    dialog_instance.selected_list = selected_list or "Checklist"
    dialog_instance._original_selected_list = dialog_instance.selected_list
    dialog_instance.supporting_evidence_compulsory = False
    dialog_instance.business_logic = CaseBusinessLogic(dialog_instance.fy)

    # Initialize selected_responsibility_id
    dialog_instance.selected_responsibility_id = None
    if isinstance(case_data, dict):
        dialog_instance.selected_responsibility_id = case_data.get("responsibility_id")
    elif len(case_data) > 10:
        dialog_instance.selected_responsibility_id = case_data[10]

    # Extract key fields
    dialog_instance.case_id = case_data[0]
    if isinstance(case_data, dict):
        # Extract base transaction number properly
        base_transaction_no = case_data.get("base_transaction_no")
        if not base_transaction_no:
            transaction_no = str(case_data.get("transaction_no", ""))
            # For FW-202600001-LS-WOR, we want FW-202600001, not just FW
            if transaction_no.startswith("FW-"):
                # Find the first occurrence of a suffix pattern (-LS, -WOR, -REC, -WO)
                import re
                match = re.match(r'(FW-\d{9})', transaction_no)
                if match:
                    base_transaction_no = match.group(1)
                else:
                    # Fallback to original logic if pattern doesn't match
                    base_transaction_no = transaction_no.split("-")[0]
            else:
                base_transaction_no = transaction_no.split("-")[0]
        dialog_instance.base_transaction_no = base_transaction_no
        dialog_instance.transaction_no = case_data.get("transaction_no", "")
        dialog_instance.assessment_status = case_data.get(
            "assessment_status", "Alleged"
        )
        dialog_instance.lc_status = case_data.get("lc_status")
        dialog_instance.suffixes = case_data.get("suffixes", "")
        dialog_instance.is_finalized = case_data.get("is_finalized", False)
    else:
        dialog_instance.transaction_no = case_data[1] if len(case_data) > 1 else ""
        # Extract base transaction number properly for tuple case
        base_transaction_no = (
            case_data[45] if len(case_data) > 45 and case_data[45] else None
        )
        if not base_transaction_no:
            transaction_no = str(case_data[1])
            # For FW-202600001-LS-WOR, we want FW-202600001, not just FW
            if transaction_no.startswith("FW-"):
                # Find the first occurrence of a suffix pattern (-LS, -WOR, -REC, -WO)
                import re
                match = re.match(r'(FW-\d{9})', transaction_no)
                if match:
                    base_transaction_no = match.group(1)
                else:
                    # Fallback to original logic if pattern doesn't match
                    base_transaction_no = transaction_no.split("-")[0]
            else:
                base_transaction_no = transaction_no.split("-")[0]
        dialog_instance.base_transaction_no = base_transaction_no
        dialog_instance.assessment_status = (
            case_data[42] if len(case_data) > 42 and case_data[42] else "Alleged"
        )
        dialog_instance.lc_status = (
            case_data[43] if len(case_data) > 43 and case_data[43] else None
        )
        dialog_instance.suffixes = (
            case_data[44] if len(case_data) > 44 and case_data[44] else ""
        )
        dialog_instance.is_finalized = (
            case_data[26] if len(case_data) > 26 and case_data[26] else False
        )

    # Cache workflow status
    try:
        dialog_instance.workflow_status_cache = get_case_workflow_status(
            dialog_instance.case_id
        )
    except Exception as e:
        print(f"DEBUG: Failed to load workflow status cache: {e}")
        dialog_instance.workflow_status_cache = None

    # Validate loaded data
    if not dialog_instance.responsibilities:
        raise ValueError("No posting responsibilities found in database")
    if not dialog_instance.categories:
        raise ValueError("No categories found in database")
    if not dialog_instance.lists:
        raise ValueError("No lists found in database")
