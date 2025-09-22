import json
import sqlite3

from scripts.Utilities.config import DB_PATH


def verify_database():
    print("=== Database Verification ===")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Fix base_transaction_no if missing
        print("Fixing missing base_transaction_no...")
        cursor.execute(
            "UPDATE cases SET base_transaction_no = transaction_no WHERE base_transaction_no IS NULL"
        )
        fixed_count = cursor.rowcount
        print(f"Updated {fixed_count} cases with base_transaction_no")
        conn.commit()

        # Query 1: Check case 202600001
        print(
            "\nQuery 1: SELECT base_transaction_no, assessment_status, lc_status, evidence_paths FROM cases WHERE base_transaction_no='202600001'"
        )
        cursor.execute(
            "SELECT base_transaction_no, assessment_status, lc_status, evidence_paths FROM cases WHERE base_transaction_no='202600001'"
        )
        result = cursor.fetchone()

        if result:
            base_no, assessment_status, lc_status, evidence_paths_json = result
            print(f"Found case: {base_no}")
            print(f"Assessment Status: {assessment_status}")
            print(f"LC Status: {lc_status}")

            if evidence_paths_json:
                try:
                    evidence_paths = json.loads(evidence_paths_json)
                    print(f"Evidence Paths: {evidence_paths}")
                    if "assessment" in evidence_paths:
                        print(f"Assessment Evidence: {evidence_paths['assessment']}")
                    else:
                        print("No assessment evidence found")
                except json.JSONDecodeError:
                    print("Failed to parse evidence_paths")
            else:
                print("No evidence_paths")

            # Check expected values
            if assessment_status == "Confirmed":
                print("[PASS] Assessment status is Confirmed")
            else:
                print(
                    f"[FAIL] Assessment status is {assessment_status}, expected Confirmed"
                )

            if lc_status == "Awaiting LC determination":
                print("[PASS] LC status is Awaiting LC determination")
            else:
                print(
                    f"[FAIL] LC status is {lc_status}, expected Awaiting LC determination"
                )

        else:
            print("[FAIL] No case found with base_transaction_no='202600001'")

        # Query 2: Check for duplicates
        print(
            "\nQuery 2: SELECT base_transaction_no, COUNT(*) FROM cases GROUP BY base_transaction_no HAVING COUNT(*) > 1"
        )
        cursor.execute(
            "SELECT base_transaction_no, COUNT(*) FROM cases GROUP BY base_transaction_no HAVING COUNT(*) > 1"
        )
        duplicates = cursor.fetchall()

        if duplicates:
            print(f"[FAIL] Found duplicate cases: {duplicates}")
        else:
            print("[PASS] No duplicate cases found")

        # Check schema
        print("\nSchema check:")
        cursor.execute("PRAGMA table_info(cases)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} (index {col[0]})")

        # Check a sample case
        print("\nSample case data:")
        cursor.execute("SELECT * FROM cases LIMIT 1")
        sample = cursor.fetchone()
        if sample:
            print(f"Total columns: {len(sample)}")
            for i, val in enumerate(sample):
                print(f"  Column {i}: {val}")

        # Additional check: Total cases
        cursor.execute("SELECT COUNT(*) FROM cases")
        total_cases = cursor.fetchone()[0]
        print(f"\nTotal cases in database: {total_cases}")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    verify_database()
