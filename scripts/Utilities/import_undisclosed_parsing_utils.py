"""
Parsing utilities for undisclosed imports.
"""

import sqlite3

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_financial_year


def analyze_database_vs_import_data(transactions, category, date_from, date_to):
    """Comprehensive analysis of database content vs import data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get current financial year
        fy = get_financial_year()
        fy_parts = fy.split("-")
        start_year = int(fy_parts[0])
        end_year = int(fy_parts[1])

        # Get fy_id
        cursor.execute(
            "SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?",
            (start_year, end_year),
        )
        fy_result = cursor.fetchone()
        fy_id = fy_result[0] if fy_result else None

        print("\n" + "=" * 80)
        print("COMPREHENSIVE DATABASE VS IMPORT ANALYSIS")
        print("=" * 80)

        # 1. Database content analysis
        print(f"\n1. DATABASE CONTENT ANALYSIS (FY: {fy}, fy_id: {fy_id})")
        print("-" * 50)

        cursor.execute(
            """
            SELECT COUNT(*) FROM cases
            WHERE fy_id = ? AND list != 'Deleted Cases'
        """,
            (fy_id,),
        )
        total_db_cases = cursor.fetchone()[0]
        print(f"Total cases in database: {total_db_cases}")

        # Get sample of database cases
        cursor.execute(
            """
            SELECT transaction_no, responsibility_id, category, amount, list, status
            FROM cases
            WHERE fy_id = ? AND list != 'Deleted Cases'
            ORDER BY transaction_no
            LIMIT 10
        """,
            (fy_id,),
        )
        db_cases = cursor.fetchall()

        print("\nSample database cases:")
        for case in db_cases:
            print(
                f"  {case[0]} | RespID: {case[1]} | Cat: {case[2]} | Amt: {case[3]:.2f} | List: {case[4]} | Status: {case[5]}"
            )

        # 2. Import data analysis
        print(f"\n2. IMPORT DATA ANALYSIS")
        print("-" * 50)
        print(f"Total transactions to import: {len(transactions)}")

        print("\nSample import transactions:")
        for i, transaction in enumerate(transactions[:10]):
            print(
                f"  {i+1}. Resp: '{transaction['responsibility']}' | Cat: '{category['name']}' | Amt: {abs(transaction['amount']):.2f}"
            )

        # 3. Responsibility mapping analysis
        print(f"\n3. RESPONSIBILITY MAPPING ANALYSIS")
        print("-" * 50)

        # Get all unique responsibilities from import
        import_responsibilities = set(t["responsibility"] for t in transactions)
        print(f"Unique responsibilities in import: {len(import_responsibilities)}")
        for resp in sorted(list(import_responsibilities))[:10]:  # Show first 10
            print(f"  '{resp}'")

        # Check which responsibilities exist in database
        existing_resp_map = {}
        for resp_name in import_responsibilities:
            cursor.execute(
                "SELECT id FROM responsibilities WHERE name = ?", (resp_name,)
            )
            result = cursor.fetchone()
            existing_resp_map[resp_name] = result[0] if result else None

        print(f"\nResponsibility mapping (import -> database ID):")
        for resp_name, db_id in existing_resp_map.items():
            status = "✓" if db_id else "✗"
            print(f"  {status} '{resp_name}' -> ID: {db_id}")

        # 4. Category analysis
        print(f"\n4. CATEGORY ANALYSIS")
        print("-" * 50)
        print(f"Import category: '{category['name']}'")

        # Check if category exists
        cursor.execute("SELECT id FROM categories WHERE name = ?", (category["name"],))
        cat_result = cursor.fetchone()
        print(
            f"Category exists in database: {'✓' if cat_result else '✗'} (ID: {cat_result[0] if cat_result else 'None'})"
        )

        # 5. Amount analysis
        print(f"\n5. AMOUNT ANALYSIS")
        print("-" * 50)

        import_amounts = [abs(t["amount"]) for t in transactions]
        db_amounts = []

        cursor.execute(
            """
            SELECT amount FROM cases
            WHERE fy_id = ? AND list != 'Deleted Cases'
        """,
            (fy_id,),
        )
        db_amount_rows = cursor.fetchall()
        db_amounts = [row[0] for row in db_amount_rows]

        print(
            f"Import amounts range: {min(import_amounts):.2f} - {max(import_amounts):.2f}"
        )
        print(
            f"Database amounts range: {min(db_amounts):.2f} - {max(db_amounts):.2f}"
            if db_amounts
            else "No amounts in database"
        )

        # 6. Potential matches analysis
        print(f"\n6. POTENTIAL MATCHES ANALYSIS")
        print("-" * 50)

        matches_found = 0
        for transaction in transactions[:5]:  # Check first 5 transactions
            resp_id = existing_resp_map.get(transaction["responsibility"])
            if resp_id:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM cases
                    WHERE responsibility_id = ?
                      AND fy_id = ?
                      AND list != 'Deleted Cases'
                """,
                    (resp_id, fy_id),
                )
                count = cursor.fetchone()[0]
                if count > 0:
                    matches_found += 1
                    print(
                        f"  ✓ Transaction '{transaction['responsibility']}' has {count} potential matches by responsibility"
                    )

        print(f"\nSUMMARY:")
        print(f"- Database cases: {total_db_cases}")
        print(f"- Import transactions: {len(transactions)}")
        print(
            f"- Responsibilities with DB matches: {sum(1 for v in existing_resp_map.values() if v is not None)}/{len(existing_resp_map)}"
        )
        print(f"- Transactions with potential matches: {matches_found}/5 (sampled)")

        if matches_found == 0:
            print("\n⚠️  POTENTIAL ISSUES IDENTIFIED:")
            if sum(1 for v in existing_resp_map.values() if v is not None) == 0:
                print("  - No responsibilities from import file exist in database")
            if total_db_cases == 0:
                print("  - No cases exist in database for current financial year")
            print("  - Category mismatch possible")
            print("  - Amount precision/formatting differences")

        print("\n" + "=" * 80)

        conn.close()

    except Exception as e:
        print(f"Error in analysis: {e}")
        import traceback

        print(f"Traceback: {traceback.format_exc()}")
