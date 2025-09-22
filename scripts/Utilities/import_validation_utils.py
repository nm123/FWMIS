"""
Validation utilities for imported case data.
"""

from datetime import date


def validate_imported_cases(cases: list[dict]) -> list[dict]:
    """Validate and filter imported cases."""
    # Extracted validation code from original import_cases_logic.py
    # Include checks for required fields, duplicates, etc.
    validated_cases = []
    for case in cases:
        # Check required fields
        if (
            not case.get("responsibility")
            or not case.get("description")
            or "amount" not in case
            or "date" not in case
        ):
            continue  # Skip invalid
        # Check amount is number
        if not isinstance(case["amount"], (int, float)):
            continue
        # Check date is date object
        if not isinstance(case["date"], date):
            continue
        validated_cases.append(case)

    # Check for duplicates within the list (simple check: same responsibility, amount, date)
    seen = set()
    unique_cases = []
    for case in validated_cases:
        key = (case["responsibility"], case["amount"], case["date"])
        if key not in seen:
            seen.add(key)
            unique_cases.append(case)
    return unique_cases
