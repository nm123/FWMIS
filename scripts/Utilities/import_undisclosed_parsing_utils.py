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
        print("\n1. DATABASE CONTENT ANALYSIS (FY: {}, fy_id: {})".format(fy, fy_id))
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
                "  {} | RespID: {} | Cat: {} | Amt: {:.2f} | List: {} | Status: {}".format(
                    case[0],
                    case[1],
                    case[2],
                    case[3],
                    case[4],
                    case[5],
                )
            )

        # 2. Import data analysis
        print("\n2. IMPORT DATA ANALYSIS")
        print("-" * 50)
        print("Total transactions to import: {}".format(len(transactions)))

        print("\nSample import transactions:")
        for i, transaction in enumerate(transactions[:10]):
            print(
                "  {}. Resp: '{}' | Cat: '{}' | Amt: {:.2f}".format(
                    i + 1,
                    transaction["responsibility"],
                    category["name"],
                    abs(transaction["amount"]),
                )
            )

        # 3. Responsibility mapping analysis
        print("\n3. RESPONSIBILITY MAPPING ANALYSIS")
        print("-" * 50)

        # Get all unique responsibilities from import
        import_responsibilities = set(t["responsibility"] for t in transactions)
        print(f"Unique responsibilities in import: {len(import_responsibilities)}")
        for resp in sorted(list(import_responsibilities))[:10]:  # Show first 10
            print("  '{}'".format(resp))

        # Check which responsibilities exist in database
        existing_resp_map = {}
        for resp_name in import_responsibilities:
            cursor.execute(
                "SELECT id FROM responsibilities WHERE name = ?", (resp_name,)
            )
            result = cursor.fetchone()
            existing_resp_map[resp_name] = result[0] if result else None

        print("\nResponsibility mapping (import -> database ID):")
        for resp_name, db_id in existing_resp_map.items():
            status = "✓" if db_id else "✗"
            print("  {} '{}' -> ID: {}".format(status, resp_name, db_id))

        # 4. Category analysis
        print("\n4. CATEGORY ANALYSIS")
        print("-" * 50)
        print("Import category: '{}'".format(category["name"]))

        # Check if category exists
        cursor.execute("SELECT id FROM categories WHERE name = ?", (category["name"],))
        cat_result = cursor.fetchone()
        cat_exists_msg = "Category exists in database: {} (ID: {})".format(
            "✓" if cat_result else "✗",
            cat_result[0] if cat_result else "None",
        )
        print(cat_exists_msg)

        # 5. Amount analysis
        print("\n5. AMOUNT ANALYSIS")
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
            "Import amounts range: {:.2f} - {:.2f}".format(
                min(import_amounts),
                max(import_amounts),
            )
        )
        if db_amounts:
            print(
                "Database amounts range: {:.2f} - {:.2f}".format(
                    min(db_amounts),
                    max(db_amounts),
                )
            )
        else:
            print("No amounts in database")

        # 6. Potential matches analysis
        print("\n6. POTENTIAL MATCHES ANALYSIS")
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
                        "  ✓ Transaction '{}' has {} potential matches by responsibility".format(
                            transaction["responsibility"],
                            count,
                        )
                    )

        print("\nSUMMARY:")
        print("- Database cases: {}".format(total_db_cases))
        print("- Import transactions: {}".format(len(transactions)))
        resp_matches = sum(1 for v in existing_resp_map.values() if v is not None)
        print(
            "- Responsibilities with DB matches: {}/{}".format(
                resp_matches,
                len(existing_resp_map),
            )
        )
        print(
            "- Transactions with potential matches: {}/5 (sampled)".format(
                matches_found
            )
        )

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
