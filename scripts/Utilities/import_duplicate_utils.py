import sqlite3

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import (get_current_open_financial_year,
                                               get_financial_year)


def _row_to_case_dict(row):
    return {
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


def _find_orphaned_fy_ids(cursor):
    cursor.execute(
        """
        SELECT DISTINCT c.fy_id
        FROM cases c
        LEFT JOIN financial_years fy ON fy.id = c.fy_id
        WHERE c.list != 'Deleted Cases'
          AND c.fy_id IS NOT NULL
          AND fy.id IS NULL
        """
    )
    return [row[0] for row in cursor.fetchall()]


def _fetch_duplicates(cursor, resp_id, category_name, amount, fy_id):
    if fy_id is None:
        return []
    cursor.execute(
        """
        SELECT *
        FROM cases
        WHERE responsibility_id = ?
          AND category = ?
          AND ABS(amount - ?) < 0.01
          AND fy_id = ?
          AND list != 'Deleted Cases'
        """,
        (resp_id, category_name, amount, fy_id),
    )
    rows = cursor.fetchall()
    if not rows:
        return []
    sample = rows[0]
    print(
        "DEBUG: Found %s duplicates in FY %s (sample: %s | %s | %.2f)"
        % (len(rows), fy_id, sample[1], sample[9], sample[11])
    )
    return [_row_to_case_dict(row) for row in rows]


def find_duplicates(transaction, category_name):
    """Find potential duplicate cases for a transaction."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        fy = get_financial_year()
        start_year, end_year = map(int, fy.split("-"))
        cursor.execute(
            "SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?",
            (start_year, end_year),
        )
        fy_row = cursor.fetchone()
        fy_id = fy_row[0] if fy_row else None

        if fy_id is None:
            current_fy = get_current_open_financial_year()
            if current_fy:
                fy_id = current_fy[0]
                print("DEBUG: Switched to current open FY ID: %s" % fy_id)
            else:
                print("DEBUG: No open financial year found for duplicate checking")

        print(
            "DEBUG: Duplicate checking - Current FY: %s, start_year: %s, end_year: %s, fy_id: %s"
            % (fy, start_year, end_year, fy_id)
        )

        cursor.execute(
            "SELECT start_year, end_year FROM financial_years WHERE id = 149"
        )
        print("DEBUG: FY 149 represents: %s" % (cursor.fetchone(),))

        duplicates = []
        resp_id = None
        cursor.execute(
            "SELECT id FROM responsibilities WHERE name = ?",
            (transaction["responsibility"],),
        )
        resp_row = cursor.fetchone()
        resp_id = resp_row[0] if resp_row else None

        if resp_id is None:
            print(
                "DEBUG: No responsibility ID found for '%s' - cannot search for duplicates"
                % transaction["responsibility"]
            )
            conn.close()
            return []

        amount = abs(transaction["amount"])
        primary_dupes = _fetch_duplicates(cursor, resp_id, category_name, amount, fy_id)

        if not primary_dupes:
            orphaned_ids = _find_orphaned_fy_ids(cursor)
            for orphaned_fy in orphaned_ids:
                print(
                    "DEBUG: Checking orphaned FY %s for duplicates" % orphaned_fy
                )
                orphaned_dupes = _fetch_duplicates(
                    cursor, resp_id, category_name, amount, orphaned_fy
                )
                if orphaned_dupes:
                    duplicates.extend(orphaned_dupes)
                    break
        else:
            duplicates.extend(primary_dupes)

        print("DEBUG: Total exact duplicates found: %s" % len(duplicates))

        conn.close()
        return duplicates

    except sqlite3.Error as err:
        import traceback

        print(f"Error finding duplicates: {err}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return []
