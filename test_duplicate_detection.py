import sys
import os

# Add the scripts directory to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

from scripts.Utilities.import_duplicate_utils import find_duplicates
from scripts.Utilities.financial_utils import get_financial_year

# Test transaction matching the inserted case
transaction = {
    "responsibility": "Test",
    "amount": 1000.0,
    "type": "AP",  # Assuming type for completeness
    "description": "Test description",
    "user_id": "test_user",
    "number": "123"
}
category_name = "Duplicate Supplier Payments"

print("Testing duplicate detection for test case in FY 149...")
duplicates = find_duplicates(transaction, category_name)
print(f"Found {len(duplicates)} duplicates")
if duplicates:
    for dup in duplicates:
        print(f"Duplicate found: Transaction_no: {dup['transaction_no']}, Amount: {dup['amount']}, FY_id: {dup['fy_id']}, Category: {dup['category']}")
else:
    print("No duplicates found. This indicates the duplicate detection is still not finding the case in FY 149.")
print("\nTest completed.")