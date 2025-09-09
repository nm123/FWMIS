import re
from datetime import datetime


class BASParser:
    """Parser for BAS report files"""

    def __init__(self):
        self.transactions = []
        self.extracted_date_from = None
        self.extracted_date_to = None

    def extract_dates_from_header(self, lines):
        """Extract date range from BAS report header"""
        self.extracted_date_from = None
        self.extracted_date_to = None

        # Look for various date range patterns in header lines (first 30 lines)
        patterns = [
            re.compile(r'(\d{2}/\d{2}/\d{4})\s+TO\s+(\d{2}/\d{2}/\d{4})'),  # 01/05/2025 TO 31/05/2025
            re.compile(r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'),   # 01/05/2025 - 31/05/2025
            re.compile(r'FROM\s+(\d{2}/\d{2}/\d{4})\s+TO\s+(\d{2}/\d{2}/\d{4})'),  # FROM 01/05/2025 TO 31/05/2025
            re.compile(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})'),     # 01/05/2025 31/05/2025
        ]

        for i, line in enumerate(lines[:100]):  # Check first 100 lines
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    try:
                        date_from_str = match.group(1)
                        date_to_str = match.group(2)

                        # Parse dates (DD/MM/YYYY format)
                        self.extracted_date_from = datetime.strptime(date_from_str, '%d/%m/%Y').date()
                        self.extracted_date_to = datetime.strptime(date_to_str, '%d/%m/%Y').date()
                        return  # Exit early once we find dates
                    except ValueError:
                        continue

        # If no standard patterns found, try to find any date ranges in the file
        date_only_pattern = re.compile(r'(\d{2}/\d{2}/\d{4})')
        found_dates = []

        for line in lines[:100]:
            matches = date_only_pattern.findall(line)
            if matches:
                found_dates.extend(matches)

        if len(found_dates) >= 2:
            try:
                # Take first two dates as from/to range
                self.extracted_date_from = datetime.strptime(found_dates[0], '%d/%m/%Y').date()
                self.extracted_date_to = datetime.strptime(found_dates[1], '%d/%m/%Y').date()
                return
            except ValueError:
                pass

    def parse_file(self, file_path, date_from, date_to):
        """Parse BAS report file and extract transactions"""
        self.transactions = []

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            # Extract dates from header first
            self.extract_dates_from_header(lines)

            current_responsibility = None
            current_item = None

            for line in lines:
                line = line.rstrip()

                # Check for responsibility line (R 007)
                resp_match = re.match(r'\s*R\s+(\d+)\s+(.+)', line)
                if resp_match:
                    current_responsibility = resp_match.group(2).strip()
                    continue

                # Check for item line (I 005) - exclude amounts at the end
                item_match = re.match(r'\s*I\s+(\d+)\s+(.+?)\s+\d+\.\d{2}\s+\d+\.\d{2}\s*$', line)
                if item_match:
                    current_item = item_match.group(2).strip()
                    continue

                # Check for transaction lines (AP, GJ, CL)
                # Updated regex to handle system-generated numbers before actual user names
                trans_match = re.match(r'\s*(AP|GJ|CL)\s+(\d+)\s+(.+?)\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})', line)
                if trans_match and current_responsibility and current_item:
                    trans_type = trans_match.group(1)
                    trans_number = trans_match.group(2)
                    description = trans_match.group(3).strip()
                    # Extract the last word as the actual user name (handles system-generated numbers)
                    user_field = trans_match.group(4).strip()
                    user_name = user_field.split()[-1] if user_field else ""  # Get the last word (actual user name)
                    user_date = trans_match.group(5)
                    debit = trans_match.group(6).replace(',', '')
                    credit = trans_match.group(7).replace(',', '')

                    # Parse date (DD/MM/YYYY format)
                    try:
                        date_obj = datetime.strptime(user_date, '%d/%m/%Y').date()
                    except ValueError:
                        continue  # Skip invalid dates

                    # Validate date range (skip if dates are None - used for header extraction)
                    if date_from is not None and date_to is not None:
                        if not (date_from <= date_obj <= date_to):
                            continue

                    # Determine amount (debit or credit)
                    try:
                        amount = float(debit) if float(debit) > 0 else -float(credit)
                    except ValueError:
                        continue

                    # Create transaction record
                    transaction = {
                        'responsibility': current_responsibility,
                        'item': current_item,
                        'type': trans_type,
                        'number': trans_number,
                        'description': description,
                        'date': date_obj,
                        'user_id': user_name,  # Use the actual user name instead of system-generated number
                        'amount': amount,
                        'is_credit': amount < 0
                    }

                    self.transactions.append(transaction)

        except Exception as e:
            raise Exception(f"Error parsing BAS file: {str(e)}")

        return self.transactions

    def get_extracted_dates(self):
        """Get the extracted date range from the report header"""
        return {
            'date_from': self.extracted_date_from,
            'date_to': self.extracted_date_to
        }

    def get_transaction_summary(self):
        """Get summary of parsed transactions"""
        if not self.transactions:
            return "No transactions found"

        total_count = len(self.transactions)
        debit_count = len([t for t in self.transactions if not t['is_credit']])
        credit_count = len([t for t in self.transactions if t['is_credit']])
        total_amount = sum(abs(t['amount']) for t in self.transactions)

        from scripts.Utilities.utils import format_currency_amount
        return f"Found {total_count} transactions ({debit_count} debits, {credit_count} credits) totaling {format_currency_amount(total_amount)}"