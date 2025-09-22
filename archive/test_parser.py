#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from datetime import date

from scripts.models.bas_parser import BASParser


def test_parser():
    # Test with a small sample from the file
    test_content = """         R 007   GAMALAKHE CHC
         I 005                   INT PAID:LOC GOV ON WATER & ELEC                                     0.00                    0.00
         CL 0000036711 G03570360277849BWATER ACC        00088774 GOVENDERYS   20/05/2025            229.89                    0.00
  TOTAL  I 005                   INT PAID:LOC GOV ON WATER & ELEC                                   229.89                    0.00"""

    # Write test content to a temporary file
    with open("test_bas.txt", "w") as f:
        f.write(test_content)

    try:
        # Create parser and manually test the parsing logic
        parser = BASParser()
        transactions = []
        current_responsibility = None
        current_item = None

        lines = test_content.split("\n")
        print(f"Processing {len(lines)} lines:")

        for i, line in enumerate(lines):
            line = line.rstrip()
            print(f"Line {i+1}: '{line}'")

            # Check for responsibility line
            import re

            resp_match = re.match(r"\s*R\s+(\d+)\s+(.+)", line)
            if resp_match:
                current_responsibility = resp_match.group(2).strip()
                print(f"  -> Found responsibility: {current_responsibility}")
                continue

            # Check for item line - exclude amounts at the end
            item_match = re.match(
                r"\s*I\s+(\d+)\s+(.+?)\s+\d+\.\d{2}\s+\d+\.\d{2}\s*$", line
            )
            if item_match:
                current_item = item_match.group(2).strip()
                print(f"  -> Found item: {current_item}")
                continue

            # Check for transaction lines
            trans_match = re.match(
                r"\s*(AP|GJ|CL)\s+(\d+)\s+(.+?)\s+(\d+)\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})",
                line,
            )
            print(f"  -> Transaction regex match: {trans_match is not None}")
            print(
                f"  -> Current context: resp='{current_responsibility}', item='{current_item}'"
            )

            if trans_match and current_responsibility and current_item:
                print(f"  -> Found transaction: {trans_match.group(1)}")
                trans_type = trans_match.group(1)
                trans_number = trans_match.group(2)
                description = trans_match.group(3).strip()
                user_id = trans_match.group(4)
                user_name = trans_match.group(5).strip()
                user_date = trans_match.group(6)
                debit = trans_match.group(7).replace(",", "")
                credit = trans_match.group(8).replace(",", "")

                print(f"     Type: {trans_type}, Number: {trans_number}")
                print(f"     Description: '{description}'")
                print(f"     Date: {user_date}, User ID: {user_id}")
                print(f"     Debit: {debit}, Credit: {credit}")

                # Parse date
                from datetime import datetime

                try:
                    date_obj = datetime.strptime(user_date, "%d/%m/%Y").date()
                    print(f"     Date parsed: {date_obj}")
                except ValueError as e:
                    print(f"     Date parse error: {e}")
                    continue

                # Validate date range
                date_from = date(2025, 1, 1)
                date_to = date(2025, 12, 31)
                if not (date_from <= date_obj <= date_to):
                    print(f"     Date {date_obj} not in range {date_from} to {date_to}")
                    continue

                # Determine amount
                try:
                    amount = float(debit) if float(debit) > 0 else -float(credit)
                    print(f"     Amount: {amount}")
                except ValueError as e:
                    print(f"     Amount parse error: {e}")
                    continue

                # Create transaction record
                transaction = {
                    "responsibility": current_responsibility,
                    "item": current_item,
                    "type": trans_type,
                    "number": trans_number,
                    "description": description,
                    "date": date_obj,
                    "user_id": user_id,
                    "amount": amount,
                    "is_credit": amount < 0,
                }

                transactions.append(transaction)
                print(f"  -> Transaction added!")
            elif trans_match:
                print(
                    f"  -> Transaction found but missing context: resp={current_responsibility}, item={current_item}"
                )

        print(f"\nFinal result: Found {len(transactions)} transactions")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    # Clean up
    if os.path.exists("test_bas.txt"):
        os.remove("test_bas.txt")


if __name__ == "__main__":
    test_parser()
