import sys
import os
import csv
from datetime import datetime
import sqlite3

# Add root directory to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
sys.path.append('scripts')
sys.path.append('scripts/Utilities')

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.shared_case_filter_utils import build_case_query, execute_case_query
from scripts.Utilities.financial_utils import get_all_financial_years

print("=== START TEST DATA IMPORT FOR FY7 ===")

# File path
file_path = 'data/test_data/test_bas_6_cases.TXT'

# FY ID for import
fy_id = 7  # FY7
responsibility_id = 1  # Assume valid responsibility_id
list_name = 'Checklist'
status = 'Alleged'

# Check if FY7 exists
financial_years = get_all_financial_years()
fy7_exists = any(fy[0] == fy_id for fy in financial_years)
if not fy7_exists:
    print(f"Error: FY7 (ID {fy_id}) does not exist in database")
    sys.exit(1)

cases_imported = 0

try:
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='|')
        for row_num, row in enumerate(reader, 1):
            try:
                # Parse row
                transaction_no = row['Transaction_No'].strip()
                amount = float(row['Amount'].strip())
                vendor_name = row['Vendor_Name'].strip()
                date_str = row['Date'].strip()
                category = row['Category'].strip()
                description = row['Description'].strip()

                date_incurred = datetime.strptime(date_str, '%Y-%m-%d').date()

                # Minimal case data with basic required columns
                case_data = (
                    transaction_no,
                    date_incurred,
                    datetime.now().date(),  # date_identified
                    datetime.now().date(),  # date_reported
                    description,
                    category,
                    responsibility_id,
                    amount,
                    fy_id,
                    list_name,
                    status,
                )

                # Minimal insert query with core columns only
                insert_sql = """
                INSERT INTO cases (
                    transaction_no, date_incurred, date_identified, date_reported,
                    description, category, responsibility_id, amount,
                    fy_id, list, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute(insert_sql, case_data)
                case_id = cur.lastrowid
                conn.commit()
                conn.close()

                cases_imported += 1
                print(f"Imported case {transaction_no} (ID {case_id}) - Amount: R{amount}, Category: {category}")

            except ValueError as ve:
                print(f"Row {row_num}: Value error - {ve}")
                continue
            except sqlite3.Error as se:
                print(f"Row {row_num}: Database error for {row.get('Transaction_No', 'unknown')} - {se}")
                continue
            except Exception as e:
                print(f"Row {row_num}: Unexpected error - {e}")
                continue

    print(f"=== IMPORT COMPLETED: {cases_imported} cases imported successfully ===")

except FileNotFoundError:
    print(f"Error: File {file_path} not found")
except Exception as e:
    print(f"Error during import: {e}")

# Verify import count
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM cases WHERE fy_id = ? AND list = ? AND status = ?", (fy_id, list_name, status))
imported_count = cur.fetchone()[0]
print(f"Verification - Total imported: {imported_count} (expected 6)")

# Simulate visibility query using shared_case_filter_utils
print("\n=== SIMULATING VIEW/EDIT QUERY FOR FY7 CHECKLIST ===")

class MockCombo:
    def currentData(self):
        return fy_id  # FY7 ID
    def currentText(self):
        return list_name  # 'Checklist'

fy_combo = MockCombo()
list_combo = MockCombo()

try:
    query, params = build_case_query(fy_combo, list_combo)
    print(f"Generated Query: {query}")
    print(f"Params: {params}")

    rows = execute_case_query(query, params)
    visible_count = len(rows)
    print(f"Visibility query returned {visible_count} rows")

    if rows:
        print("Sample row keys:", list(rows[0].keys()) if isinstance(rows[0], dict) else "Raw row data")
    else:
        print("No rows visible - checking base conditions:")
        # Manual check
        cur.execute('SELECT COUNT(*) FROM cases WHERE fy_id=? AND list=? AND responsibility_id IS NOT NULL AND fy_id IN (SELECT id FROM financial_years)', (fy_id, list_name))
        base_count = cur.fetchone()[0]
        print(f"Base matching cases: {base_count}")
        
        cur.execute('SELECT COUNT(*) FROM cases WHERE fy_id=? AND list=? AND (responsibility_id IS NULL OR responsibility_id = 0)', (fy_id, list_name))
        invalid_resp = cur.fetchone()[0]
        print(f"Cases with invalid responsibility_id: {invalid_resp}")

except Exception as e:
    print(f"Error in visibility query: {e}")
    # Fallback manual verification
    cur.execute("SELECT COUNT(*) FROM cases WHERE fy_id = ? AND list = ?", (fy_id, list_name))
    manual_count = cur.fetchone()[0]
    print(f"Manual count: {manual_count} cases in FY7 Checklist")

conn.close()

if imported_count == 6:
    print("SUCCESS: 6 cases imported to FY7 Checklist")
else:
    print(f"ISSUE: Expected 6, imported {imported_count}")