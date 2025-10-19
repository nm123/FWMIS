"""Smoke tests for case validation helpers."""

from scripts.core.case_service import CaseService


def test_validate_case_data_missing_fields():
    errors = CaseService.validate_case_data({})

    assert "Description is required" in errors
    assert "Category is required" in errors
    assert "Responsibility is required" in errors
    assert "Valid amount is required" in errors
    assert "Date Incurred is required" in errors
    assert "Date Identified is required" in errors
    assert "Date Reported is required" in errors
