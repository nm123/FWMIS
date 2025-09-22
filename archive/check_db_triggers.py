import os
import sqlite3

# Database path
DB_PATH = os.path.join("data", "fruitless.db")


def check_triggers():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check for triggers
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
        triggers = cursor.fetchall()

        print("=== DATABASE TRIGGERS ===")
        if triggers:
            for name, sql in triggers:
                print(f"Trigger: {name}")
                print(f"SQL: {sql}")
                print("-" * 50)
        else:
            print("No triggers found")

        # Check for orphaned data
        print("\n=== ORPHANED DATA CHECK ===")

        # Cases with invalid fy_id
        cursor.execute(
            """
            SELECT COUNT(*) FROM cases c
            LEFT JOIN financial_years fy ON c.fy_id = fy.id
            WHERE fy.id IS NULL AND c.fy_id IS NOT NULL
        """
        )
        orphaned_cases = cursor.fetchone()[0]
        print(f"Cases with invalid fy_id: {orphaned_cases}")

        # Periods with invalid fy_id
        cursor.execute(
            """
            SELECT COUNT(*) FROM periods p
            LEFT JOIN financial_years fy ON p.fy_id = fy.id
            WHERE fy.id IS NULL AND p.fy_id IS NOT NULL
        """
        )
        orphaned_periods = cursor.fetchone()[0]
        print(f"Periods with invalid fy_id: {orphaned_periods}")

        # Show details of orphaned periods
        if orphaned_periods > 0:
            cursor.execute(
                """
                SELECT p.id, p.fy_id, p.period_number, p.status
                FROM periods p
                LEFT JOIN financial_years fy ON p.fy_id = fy.id
                WHERE fy.id IS NULL AND p.fy_id IS NOT NULL
                LIMIT 5
            """
            )
            orphaned_period_details = cursor.fetchall()
            print("Orphaned periods details:")
            for period in orphaned_period_details:
                print(
                    f"  Period ID: {period[0]}, FY_ID: {period[1]}, Period: {period[2]}, Status: {period[3]}"
                )

        # Check for periods that belong to FY 149 specifically
        cursor.execute(
            """
            SELECT COUNT(*) FROM periods WHERE fy_id = 149
        """
        )
        fy149_periods = cursor.fetchone()[0]
        print(f"Periods belonging to FY 149: {fy149_periods}")

        if fy149_periods > 0:
            cursor.execute(
                """
                SELECT id, period_number, status FROM periods WHERE fy_id = 149
            """
            )
            fy149_period_details = cursor.fetchall()
            print("FY 149 period details:")
            for period in fy149_period_details:
                print(
                    f"  Period ID: {period[0]}, Period: {period[1]}, Status: {period[2]}"
                )

        # Check if FY 149 exists
        cursor.execute("SELECT COUNT(*) FROM financial_years WHERE id = 149")
        fy149_exists = cursor.fetchone()[0]
        print(f"Financial Year 149 exists: {fy149_exists}")

        # Check all financial years
        cursor.execute(
            "SELECT id, start_year, end_year FROM financial_years ORDER BY id"
        )
        all_fys = cursor.fetchall()
        print("All financial years:")
        for fy in all_fys:
            print(f"  FY ID: {fy[0]}, Years: {fy[1]}-{fy[2]}")

        # Check the specific case 202600023 that the user mentioned
        cursor.execute(
            """
            SELECT fy_id, list, status, responsibility_id, category, amount
            FROM cases
            WHERE transaction_no = '202600023'
        """
        )
        case_202600023 = cursor.fetchone()
        if case_202600023:
            fy_id, list_name, status, resp_id, category, amount = case_202600023
            print(f"\nCase 202600023 details:")
            print(f"  FY ID: {fy_id}")
            print(f"  List: {list_name}")
            print(f"  Status: {status}")
            print(f"  Category: {category}")
            print(f"  Amount: {amount}")

            # Check what financial year this fy_id corresponds to
            cursor.execute(
                "SELECT start_year, end_year FROM financial_years WHERE id = ?",
                (fy_id,),
            )
            fy_info = cursor.fetchone()
            if fy_info:
                print(f"  Financial Year: {fy_info[0]}-{fy_info[1]}")
            else:
                print(f"  Financial Year: INVALID (fy_id {fy_id} not found)")
        else:
            print("\nCase 202600023 not found in database")

        # Check all cases with transaction numbers starting with 2026
        cursor.execute(
            """
            SELECT transaction_no, fy_id, list, status
            FROM cases
            WHERE transaction_no LIKE '2026%'
            ORDER BY transaction_no
        """
        )
        fy2026_cases = cursor.fetchall()
        print(f"\nAll cases with transaction numbers starting with 2026:")
        for case_info in fy2026_cases:
            trans_no, fy_id, list_name, status = case_info
            print(f"  {trans_no}: FY_ID={fy_id}, List={list_name}, Status={status}")

        conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    check_triggers()
