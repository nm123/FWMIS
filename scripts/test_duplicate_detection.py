import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Utilities.import_duplicate_utils import find_duplicates
from Utilities.financial_utils import get_financial_year

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

print("Testing duplicate detection...")
duplicates = find_duplicates(transaction, category_name)
print(f"Found {len(duplicates)} duplicates")
if duplicates:
    for dup in duplicates:
        print(f"Duplicate: {dup['transaction_no']} - Amount: {dup['amount']}, FY: {dup['fy_id']}")
else:
    print("No duplicates found - this indicates the fix is not detecting the orphaned FY case.")