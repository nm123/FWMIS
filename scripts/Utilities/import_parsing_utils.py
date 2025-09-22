"""
Parsing utilities for BAS file imports.
"""

import re
from datetime import date, datetime


def parse_bas_file(file_path: str) -> tuple[list[dict], date | None, date | None]:
    """Parse BAS file lines into case dictionaries."""
    # Extracted parsing code from BASParser
    transactions = []
    extracted_date_from = None
    extracted_date_to = None

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Extract dates from header first
        # Look for various date range patterns in header lines (first 30 lines)
        patterns = [
            re.compile(
                r"(\d{2}/\d{2}/\d{4})\s+TO\s+(\d{2}/\d{2}/\d{4})"
            ),  # 01/05/2025 TO 31/05/2025
            re.compile(
                r"(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})"
            ),  # 01/05/2025 - 31/05/2025
            re.compile(
                r"FROM\s+(\d{2}/\d{2}/\d{4})\s+TO\s+(\d{2}/\d{2}/\d{4})"
            ),  # FROM 01/05/2025 TO 31/05/2025
            re.compile(
                r"(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})"
            ),  # 01/05/2025 31/05/2025
        ]

        for i, line in enumerate(lines[:100]):  # Check first 100 lines
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    try:
                        date_from_str = match.group(1)
                        date_to_str = match.group(2)

                        # Parse dates (DD/MM/YYYY format)
                        extracted_date_from = datetime.strptime(
                            date_from_str, "%d/%m/%Y"
                        ).date()
                        extracted_date_to = datetime.strptime(
                            date_to_str, "%d/%m/%Y"
                        ).date()
                        break
                    except ValueError:
                        continue
            if extracted_date_from:
                break

        # If no standard patterns found, try to find any date ranges in the file
        if not extracted_date_from:
            date_only_pattern = re.compile(r"(\d{2}/\d{2}/\d{4})")
            found_dates = []

            for line in lines[:100]:
                matches = date_only_pattern.findall(line)
                if matches:
                    found_dates.extend(matches)

            if len(found_dates) >= 2:
                try:
                    # Take first two dates as from/to range
                    extracted_date_from = datetime.strptime(
                        found_dates[0], "%d/%m/%Y"
                    ).date()
                    extracted_date_to = datetime.strptime(
                        found_dates[1], "%d/%m/%Y"
                    ).date()
                except ValueError:
                    pass

        current_responsibility = None
        current_item = None

        for line in lines:
            line = line.rstrip()

            # Check for responsibility line (R 007)
            resp_match = re.match(r"\s*R\s+(\d+)\s+(.+)", line)
            if resp_match:
                current_responsibility = resp_match.group(2).strip()
                continue

            # Check for item line (I 005) - exclude amounts at the end
            item_match = re.match(
                r"\s*I\s+(\d+)\s+(.+?)\s+\d+\.\d{2}\s+\d+\.\d{2}\s*$", line
            )
            if item_match:
                current_item = item_match.group(2).strip()
                continue

            # Check for transaction lines (AP, GJ, CL)
            # Updated regex to handle system-generated numbers before actual user names
            trans_match = re.match(
                r"\s*(AP|GJ|CL)\s+(\d+)\s+(.+?)\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})",
                line,
            )
            if trans_match and current_responsibility and current_item:
                trans_type = trans_match.group(1)
                trans_number = trans_match.group(2)
                description = trans_match.group(3).strip()
                # Extract the last word as the actual user name (handles system-generated numbers)
                user_field = trans_match.group(4).strip()
                user_name = (
                    user_field.split()[-1] if user_field else ""
                )  # Get the last word (actual user name)
                user_date = trans_match.group(5)
                debit = trans_match.group(6).replace(",", "")
                credit = trans_match.group(7).replace(",", "")

                # Parse date (DD/MM/YYYY format)
                try:
                    date_obj = datetime.strptime(user_date, "%d/%m/%Y").date()
                except ValueError:
                    continue  # Skip invalid dates

                # Validate date range if extracted
                if extracted_date_from is not None and extracted_date_to is not None:
                    if not (extracted_date_from <= date_obj <= extracted_date_to):
                        continue

                # Determine amount (debit or credit)
                try:
                    amount = float(debit) if float(debit) > 0 else -float(credit)
                except ValueError:
                    continue

                # Create transaction record
                transaction = {
                    "responsibility": current_responsibility,
                    "item": current_item,
                    "type": trans_type,
                    "number": trans_number,
                    "description": description,
                    "date": date_obj,
                    "user_id": user_name,  # Use the actual user name instead of system-generated number
                    "amount": amount,
                    "is_credit": amount < 0,
                }

                transactions.append(transaction)

    except Exception as e:
        raise Exception(f"Error parsing BAS file: {str(e)}")

    return transactions, extracted_date_from, extracted_date_to
