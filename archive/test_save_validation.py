#!/usr/bin/env python3

# Test the save validation logic
def test_installment_validation():
    # Simulate the validation logic
    unsaved_installment_amount = "500"  # Simulate user entering 500
    unsaved_installment_date = ""  # No date entered

    print(f"unsaved_installment_amount = '{unsaved_installment_amount}' (len={len(unsaved_installment_amount)})")
    print(f"unsaved_installment_date = '{unsaved_installment_date}' (len={len(unsaved_installment_date)})")

    print(f"Checking condition - unsaved_installment_amount='{unsaved_installment_amount}' evaluates to {bool(unsaved_installment_amount)}")

    if unsaved_installment_amount:
        print("Condition met - would show warning dialog")
        return True
    else:
        print("Condition NOT met - would allow saving")
        return False

if __name__ == "__main__":
    test_installment_validation()
