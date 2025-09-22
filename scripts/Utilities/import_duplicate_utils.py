import sqlite3

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import (get_current_open_financial_year,
                                               get_financial_year)


def find_duplicates(transaction, category_name):
    """Find potential duplicate cases for a transaction"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get financial year for the transaction date
        fy = get_financial_year()
        fy_parts = fy.split("-")
        start_year = int(fy_parts[0])
        end_year = int(fy_parts[1])

        # Get fy_id for the current financial year
        cursor.execute(
            "SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?",
            (start_year, end_year),
        )
        fy_result = cursor.fetchone()
        fy_id = fy_result[0] if fy_result else None

        # If fy_id is None, try to get the current open financial year
        if fy_id is None:
            current_fy = get_current_open_financial_year()
            if current_fy:
                fy_id = current_fy[0]
                print(f"DEBUG: Switched to current open FY ID: {fy_id}")
            else:
                print(f"DEBUG: No open financial year found for duplicate checking")

        print(
            f"DEBUG: Duplicate checking - Current FY: {fy}, start_year: {start_year}, end_year: {end_year}, fy_id: {fy_id}"
        )

        # Check what FY 149 actually represents
        cursor.execute(
            """
            SELECT start_year, end_year FROM financial_years WHERE id = 149
        """
        )
        fy_149_info = cursor.fetchone()
        print(f"DEBUG: FY 149 represents: {fy_149_info}")

        # If FY 149 doesn't exist, this is the root cause!
        if fy_149_info is None:
            print(f"DEBUG: *** DATABASE INTEGRITY ISSUE DETECTED ***")
            print(
                f"DEBUG: Cases exist with fy_id=149 but no financial year record exists!"
            )
            print(f"DEBUG: This explains why duplicate checking can't find the cases.")
            print(f"DEBUG: The cases are 'orphaned' in a non-existent financial year.")

            # Check what the orphaned cases look like
            cursor.execute(
                """
                SELECT transaction_no, responsibility_id, category, amount, list
                FROM cases WHERE fy_id = 149 AND list != 'Deleted Cases' LIMIT 3
            """
            )
            orphaned_cases = cursor.fetchall()
            print(f"DEBUG: Sample orphaned cases: {orphaned_cases}")

        # Also check what FY the existing cases are actually in
        cursor.execute(
            """
            SELECT DISTINCT fy_id, COUNT(*) FROM cases
            WHERE list != 'Deleted Cases'
            GROUP BY fy_id
            ORDER BY fy_id
        """
        )
        all_fy_cases = cursor.fetchall()
        print(f"DEBUG: All cases by FY ID: {all_fy_cases}")

        # Show details of all FYs with cases
        for fy_id_check, count in all_fy_cases:
            cursor.execute(
                """
                SELECT start_year, end_year FROM financial_years WHERE id = ?
            """,
                (fy_id_check,),
            )
            fy_details = cursor.fetchone()
            print(f"DEBUG: FY ID {fy_id_check}: {fy_details} has {count} cases")

        # Check for orphaned cases in non-existent financial years
        orphaned_fy_ids = []
        for fy_id_check, count in all_fy_cases:
            cursor.execute(
                """
                SELECT start_year, end_year FROM financial_years WHERE id = ?
            """,
                (fy_id_check,),
            )
            fy_details = cursor.fetchone()
            if fy_details is None and count > 0:
                orphaned_fy_ids.append(fy_id_check)
                print(f"DEBUG: Found orphaned FY ID {fy_id_check} with {count} cases")

        # If no cases in current FY, try to find cases in other FYs that match the transaction dates
        if fy_id and not any(row[0] == fy_id for row in all_fy_cases):
            print(
                f"DEBUG: No cases found in current FY {fy} (ID: {fy_id}), checking other FYs..."
            )
            # Look for cases that might match the transaction date range
            # Note: transactions not available here, so skip this part or adjust
            # For now, assume fy_id is correct

        print(f"DEBUG: Current FY: {fy} (ID: {fy_id})")

        # First, let's see what cases exist in the database for this FY
        cursor.execute(
            """
            SELECT COUNT(*) FROM cases
            WHERE fy_id = ? AND list != 'Deleted Cases'
        """,
            (fy_id,),
        )
        total_cases = cursor.fetchone()[0]
        print(f"DEBUG: Total cases in database for FY {fy}: {total_cases}")

        # Show a sample of existing cases
        cursor.execute(
            """
            SELECT transaction_no, responsibility_id, category, amount, list, fy_id
            FROM cases
            WHERE fy_id = ? AND list != 'Deleted Cases'
            LIMIT 5
        """,
            (fy_id,),
        )
        sample_cases = cursor.fetchall()
        print(f"DEBUG: Sample existing cases in FY {fy} (ID: {fy_id}): {sample_cases}")

        # Also check if there are cases in other financial years
        cursor.execute(
            """
            SELECT fy_id, COUNT(*) FROM cases
            WHERE list != 'Deleted Cases'
            GROUP BY fy_id
        """
        )
        fy_counts = cursor.fetchall()
        print(f"DEBUG: Cases by financial year: {fy_counts}")

        # Check all cases regardless of FY
        cursor.execute(
            """
            SELECT COUNT(*) FROM cases
            WHERE list != 'Deleted Cases'
        """
        )
        total_all_cases = cursor.fetchone()[0]
        print(f"DEBUG: Total cases in all FYs (excluding deleted): {total_all_cases}")

        # Search for cases with same responsibility, category, amount, and financial year
        # First, find responsibility ID by name
        resp_id = None
        cursor.execute(
            "SELECT id FROM responsibilities WHERE name = ?",
            (transaction["responsibility"],),
        )
        resp_result = cursor.fetchone()
        resp_id = resp_result[0] if resp_result else None

        print(
            f"DEBUG: Looking for responsibility '{transaction['responsibility']}' - found ID: {resp_id}"
        )
        print(
            f"DEBUG: Transaction details: responsibility='{transaction['responsibility']}', category='{category_name}', amount={abs(transaction['amount']):.2f}"
        )

        # Debug: Check what cases exist for this responsibility in the database
        if resp_id:
            cursor.execute(
                """
                SELECT COUNT(*), GROUP_CONCAT(transaction_no, ', ') FROM cases
                WHERE responsibility_id = ? AND fy_id = ? AND list != 'Deleted Cases'
            """,
                (resp_id, fy_id),
            )
            resp_count, resp_cases = cursor.fetchone()
            print(
                f"DEBUG: Cases for responsibility ID {resp_id} in FY {fy}: {resp_count} cases"
            )
            if resp_cases:
                print(f"DEBUG: Sample case numbers: {resp_cases[:200]}...")

            # Check cases for this responsibility in ALL financial years
            cursor.execute(
                """
                SELECT fy_id, COUNT(*), GROUP_CONCAT(transaction_no, ', ') FROM cases
                WHERE responsibility_id = ? AND list != 'Deleted Cases'
                GROUP BY fy_id
            """,
                (resp_id,),
            )
            all_fy_resp_cases = cursor.fetchall()
            print(
                f"DEBUG: Cases for responsibility ID {resp_id} in ALL FYs: {all_fy_resp_cases}"
            )

            # Check what lists the cases are in
            cursor.execute(
                """
                SELECT list, COUNT(*) FROM cases
                WHERE responsibility_id = ? AND fy_id = ?
                GROUP BY list
            """,
                (resp_id, fy_id),
            )
            list_counts = cursor.fetchall()
            print(
                f"DEBUG: Cases for responsibility ID {resp_id} by list in FY {fy}: {list_counts}"
            )

            # Check the actual responsibility names in existing cases
            cursor.execute(
                """
                SELECT DISTINCT r.name, COUNT(c.id) FROM cases c
                JOIN responsibilities r ON c.responsibility_id = r.id
                WHERE c.fy_id = ? AND c.list != 'Deleted Cases'
                GROUP BY r.name
                LIMIT 10
            """,
                (fy_id,),
            )
            resp_names_in_cases = cursor.fetchall()
            print(
                f"DEBUG: Responsibility names in existing cases (FY {fy}): {resp_names_in_cases}"
            )

            # Debug: Check category matching
            cursor.execute(
                """
                SELECT COUNT(*) FROM cases
                WHERE responsibility_id = ? AND category = ? AND fy_id = ? AND list != 'Deleted Cases'
            """,
                (resp_id, category_name, fy_id),
            )
            cat_count = cursor.fetchone()[0]
            print(f"DEBUG: Cases with matching category '{category_name}': {cat_count}")

            # Debug: Check amount matching (broader range)
            transaction_amount = abs(transaction["amount"])
            cursor.execute(
                """
                SELECT COUNT(*), MIN(amount), MAX(amount) FROM cases
                WHERE responsibility_id = ? AND fy_id = ? AND list != 'Deleted Cases'
            """,
                (resp_id, fy_id),
            )
            amt_count, min_amt, max_amt = cursor.fetchone()

            # Handle None values for min/max amounts when no cases exist
            min_amt_str = f"{min_amt:.2f}" if min_amt is not None else "N/A"
            max_amt_str = f"{max_amt:.2f}" if max_amt is not None else "N/A"
            print(
                f"DEBUG: Amount range for responsibility: {min_amt_str} - {max_amt_str} (transaction: {transaction_amount:.2f})"
            )

        if resp_id:
            # Only return exact matches (same responsibility, category, amount, FY)
            # Debug: Check the transaction amount type and value
            print(
                f"DEBUG: Transaction amount raw: {transaction['amount']} (type: {type(transaction['amount'])})"
            )

            # Ensure amount is numeric
            try:
                if isinstance(transaction["amount"], str):
                    # Remove currency symbols and clean the string
                    amount_str = (
                        transaction["amount"].replace("R", "").replace(",", "").strip()
                    )
                    transaction_amount = abs(float(amount_str))
                else:
                    transaction_amount = abs(float(transaction["amount"]))
            except (ValueError, TypeError) as e:
                print(f"DEBUG: Error converting amount: {e}")
                transaction_amount = 0.0

            print(f"DEBUG: Using transaction amount: {transaction_amount:.2f}")
            duplicates = []

            # First try exact match in current FY
            cursor.execute(
                """
                SELECT * FROM cases
                WHERE responsibility_id = ?
                  AND category = ?
                  AND ABS(amount - ?) < 0.01
                  AND fy_id = ?
                  AND list != 'Deleted Cases'
            """,
                (resp_id, category_name, transaction_amount, fy_id),
            )

            rows = cursor.fetchall()
            print(
                f"DEBUG: Exact match in current FY {fy_id} found {len(rows)} duplicates"
            )
            if len(rows) > 0:
                print(
                    f"DEBUG: Exact match sample: {rows[0][1]} | {rows[0][9]} | {rows[0][11]:.2f}"
                )
                # Convert all rows to dictionaries
                for row in rows:
                    case_dict = {
                        "id": row[0],
                        "transaction_no": row[1],
                        "date_incurred": row[2],
                        "date_identified": row[3],
                        "date_reported": row[4],
                        "description": row[5],
                        "bas_payment_no": row[6],
                        "bas_payment_date": row[7],
                        "persal_no": row[8],
                        "category": row[9],
                        "responsibility_id": row[10],
                        "amount": row[11],
                        "source_document": row[12],
                        "minutes": row[13],
                        "evidence_path": row[14],
                        "attachments": row[15],
                        "status": row[16],
                        "list": row[17],
                        "assessment_assessed_by": row[18],
                        "assessment_date": row[19],
                        "assessment_result": row[20],
                        "fy_id": row[21],
                        "period_id": row[22],
                        "criminal_charges": row[23],
                        "disciplinary_process": row[24],
                        "loss_recovery": row[25],
                        "prevention_steps": row[26],
                        "original_list": row[27],
                    }
                    duplicates.append(case_dict)
            else:
                # If no matches in current FY, check orphaned FYs
                for orphaned_fy_id in orphaned_fy_ids:
                    print(
                        f"DEBUG: Checking orphaned FY {orphaned_fy_id} for duplicates"
                    )
                    cursor.execute(
                        """
                        SELECT * FROM cases
                        WHERE responsibility_id = ?
                          AND category = ?
                          AND ABS(amount - ?) < 0.01
                          AND fy_id = ?
                          AND list != 'Deleted Cases'
                    """,
                        (resp_id, category_name, transaction_amount, orphaned_fy_id),
                    )

                    orphaned_rows = cursor.fetchall()
                    print(
                        f"DEBUG: Exact match in orphaned FY {orphaned_fy_id} found {len(orphaned_rows)} duplicates"
                    )
                    if len(orphaned_rows) > 0:
                        print(
                            f"DEBUG: Orphaned FY match sample: {orphaned_rows[0][1]} | {orphaned_rows[0][9]} | {orphaned_rows[0][11]:.2f}"
                        )
                        # Convert orphaned rows to dictionaries too
                        for row in orphaned_rows:
                            case_dict = {
                                "id": row[0],
                                "transaction_no": row[1],
                                "date_incurred": row[2],
                                "date_identified": row[3],
                                "date_reported": row[4],
                                "description": row[5],
                                "bas_payment_no": row[6],
                                "bas_payment_date": row[7],
                                "persal_no": row[8],
                                "category": row[9],
                                "responsibility_id": row[10],
                                "amount": row[11],
                                "source_document": row[12],
                                "minutes": row[13],
                                "evidence_path": row[14],
                                "attachments": row[15],
                                "status": row[16],
                                "list": row[17],
                                "assessment_assessed_by": row[18],
                                "assessment_date": row[19],
                                "assessment_result": row[20],
                                "fy_id": row[21],
                                "period_id": row[22],
                                "criminal_charges": row[23],
                                "disciplinary_process": row[24],
                                "loss_recovery": row[25],
                                "prevention_steps": row[26],
                                "original_list": row[27],
                            }
                            duplicates.append(case_dict)
                        break  # Stop after finding matches in first orphaned FY

                if not duplicates:
                    print(
                        f"DEBUG: No exact matches found for: resp_id={resp_id}, category='{category_name}', amount={transaction_amount:.2f}, fy_id={fy_id} or orphaned FYs"
                    )

            print(f"DEBUG: Total exact duplicates found: {len(duplicates)}")

            conn.close()
            return duplicates
        else:
            print(
                f"DEBUG: No responsibility ID found for '{transaction['responsibility']}' - cannot search for duplicates"
            )
            conn.close()
            return []

    except sqlite3.Error as e:
        print(f"Error finding duplicates: {e}")
        import traceback

        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return []
