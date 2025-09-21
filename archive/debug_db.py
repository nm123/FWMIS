import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import DB_PATH

def debug_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print('=== DATABASE TRIGGERS ===')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
    triggers = cursor.fetchall()
    if triggers:
        for trigger in triggers:
            print(f'Trigger: {trigger[0]}')
    else:
        print('No triggers found')

    print('\n=== CASES TABLE SCHEMA ===')
    cursor.execute('PRAGMA table_info(cases)')
    columns = cursor.fetchall()
    print(f'Total columns: {len(columns)}')
    for i, col in enumerate(columns):
        print(f'{i}: {col[1]} ({col[2]}) notnull={col[3]} default={col[4]}')

    print('\n=== AUDIT_LOG TABLE SCHEMA ===')
    cursor.execute('PRAGMA table_info(audit_log)')
    audit_columns = cursor.fetchall()
    print(f'Total columns: {len(audit_columns)}')
    for i, col in enumerate(audit_columns):
        print(f'{i}: {col[1]} ({col[2]}) notnull={col[3]} default={col[4]}')

    print('\n=== TESTING INSERT ===')
    # Test the exact INSERT statement
    test_sql = """
    INSERT INTO cases (
        transaction_no, date_incurred, date_identified, date_reported, description,
        bas_payment_no, bas_payment_date, persal_no, category, responsibility_id, amount,
        source_document, minutes, evidence_path, attachments, status, list, assessment_assessed_by,
        assessment_date, assessment_result, fy_id, period_id, criminal_charges, disciplinary_process,
        loss_recovery, prevention_steps, original_list
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    test_params = (
        'TEST123', '2025-08-30', '2025-08-30', '2025-08-30', 'Test description',
        '', '2025-08-30', '', 'Test Category', 1, 100.0,
        '', '', '', '[]', 'Alleged', 'Checklist', '',
        '2025-08-30', '', None, None, 'N/A', 'N/A',
        'N/A', 'Test steps', 'Checklist'
    )

    try:
        cursor.execute(test_sql, test_params)
        print('Test INSERT succeeded')
        conn.rollback()  # Don't actually save
    except Exception as e:
        print(f'Test INSERT failed: {e}')
        print(f'Error type: {type(e)}')

    conn.close()

if __name__ == "__main__":
    debug_database()