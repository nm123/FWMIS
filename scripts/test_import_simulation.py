import sys
sys.path.append('scripts')
sys.path.append('scripts/Utilities')

import sqlite3
from scripts.models.bas_parser import BASParser
from datetime import datetime

DB_PATH = 'data/fruitless.db'

def setup_db():
    """Setup minimal DB structure for simulation"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if needed (minimal schema)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_years (
        id INTEGER PRIMARY KEY,
        start_year INTEGER,
        end_year INTEGER,
        status TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS responsibilities (
        id INTEGER PRIMARY KEY,
        name TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_no TEXT,
        date_incurred DATE,
        date_identified DATE,
        date_reported DATE,
        description TEXT,
        bas_payment_no TEXT,
        bas_payment_date DATE,
        persal_no TEXT,
        category TEXT,
        responsibility_id INTEGER,
        amount REAL,
        source_document TEXT,
        minutes TEXT,
        evidence_path TEXT,
        attachments TEXT,
        status TEXT,
        list TEXT,
        assessment_assessed_by TEXT,
        assessment_date DATE,
        assessment_result TEXT,
        fy_id INTEGER,
        period_id INTEGER,
        criminal_charges TEXT,
        disciplinary_process TEXT,
        loss_recovery TEXT,
        prevention_steps TEXT,
        original_list TEXT
    )
    """)
    
    # Insert FY7 (assuming 2024-2025)
    cursor.execute("INSERT OR IGNORE INTO financial_years (id, start_year, end_year, status) VALUES (7, 2024, 2025, 'open')")
    
    # Insert Test responsibility id=5
    cursor.execute("INSERT OR IGNORE INTO responsibilities (id, name) VALUES (5, 'Test')")
    
    conn.commit()
    conn.close()
    print("DB setup complete.")

def insert_partial_cases():
    """Parse partial file and insert first 6 as cases with fixed params"""
    parser = BASParser()
    transactions = parser.parse_file('data/Int_pd_other_partial.TXT', None, None)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted_ids = []
    for i, trans in enumerate(transactions[:6]):
        # Override with simulation params
        case_data = {
            'transaction_no': f'TEST{i+1}',
            'date_incurred': trans['date'].strftime('%Y-%m-%d'),
            'date_identified': trans['date'].strftime('%Y-%m-%d'),
            'date_reported': trans['date'].strftime('%Y-%m-%d'),
            'description': trans['description'],
            'bas_payment_no': trans['number'] if trans['type'] != 'GJ' else None,
            'bas_payment_date': trans['date'].strftime('%Y-%m-%d') if trans['type'] != 'GJ' else None,
            'bas_journal_no': trans['number'] if trans['type'] == 'GJ' else None,
            'bas_journal_date': trans['date'].strftime('%Y-%m-%d') if trans['type'] == 'GJ' else None,
            'persal_no': None,
            'category': 'Interest - Other',
            'responsibility_id': 5,
            'amount': abs(trans['amount']),
            'source_document': None,
            'minutes': None,
            'evidence_path': None,
            'attachments': '[]',
            'status': 'Alleged',
            'list': None,  # As per task
            'assessment_assessed_by': None,
            'assessment_date': None,
            'assessment_result': None,
            'fy_id': 7,
            'period_id': 1,  # Dummy
            'criminal_charges': 'N/A',
            'disciplinary_process': 'N/A',
            'loss_recovery': 'N/A',
            'prevention_steps': 'N/A',
            'original_list': None
        }
        
        cursor.execute("""
        INSERT INTO cases (
            transaction_no, date_incurred, date_identified, date_reported, description,
            bas_payment_no, bas_payment_date, bas_journal_no, bas_journal_date,
            persal_no, category, responsibility_id, amount, source_document, minutes, evidence_path,
            attachments, status, list, assessment_assessed_by, assessment_date, assessment_result,
            fy_id, period_id, criminal_charges, disciplinary_process, loss_recovery,
            prevention_steps, original_list
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(case_data.values()))
        
        inserted_id = cursor.lastrowid
        inserted_ids.append(inserted_id)
        print(f"Inserted case {i+1}: ID={inserted_id}, Amount={case_data['amount']}, Category='{case_data['category']}', Resp ID={case_data['responsibility_id']}, FY ID={case_data['fy_id']}, List={case_data['list']}")
    
    conn.commit()
    conn.close()
    print(f"Inserted {len(inserted_ids)} cases.")
    return inserted_ids

def query_inserted_cases():
    """Query the inserted cases"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE fy_id=7 ORDER BY id DESC LIMIT 6")
    rows = cursor.fetchall()
    print("\n=== Inserted Cases Query ===")
    for row in rows:
        print(f"ID: {row[0]}, Transaction: {row[1]}, Category: '{row[9]}', Amount: {row[11]}, Resp ID: {row[10]}, FY ID: {row[21]}, List: {row[17]}")
    conn.close()

def simulate_second_import_check():
    """Parse complete file first 6, simulate find_duplicates for each"""
    parser = BASParser()
    transactions = parser.parse_file('data/Int_pd_other_complete.TXT', None, None)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n=== Simulation of find_duplicates on Complete File First 6 ===")
    for i, trans in enumerate(transactions[:6]):
        # Simulate call to find_duplicates
        # Hardcode params as per task
        simulated_transaction = {
            'responsibility': 'Test',  # To match resp_id=5
            'amount': trans['amount']
        }
        # Manually simulate the query since find_duplicates uses dynamic FY, but we fix to 7
        transaction_amount = abs(trans['amount'])
        cursor.execute("""
            SELECT id, transaction_no, category, amount, list, fy_id 
            FROM cases
            WHERE responsibility_id = 5
              AND category = 'Interest - Other'
              AND ABS(amount - ?) < 0.01
              AND fy_id = 7
              AND (list != 'Deleted Cases' OR list IS NULL)
        """, (transaction_amount,))
        rows = cursor.fetchall()
        print(f"Transaction {i+1}: Amount={transaction_amount}")
        print(f"  Query returned {len(rows)} matches")
        if rows:
            for row in rows:
                print(f"    Match: ID={row[0]}, Trans={row[1]}, Cat='{row[2]}', Amt={row[3]}, List={row[4]}, FY={row[5]}")
        else:
            print("  No match - possible reasons: category mismatch, amount precision, resp_id, fy_id, list filter")
            # Check category in DB
            cursor.execute("SELECT DISTINCT category FROM cases WHERE fy_id=7")
            db_cats = [r[0] for r in cursor.fetchall()]
            print(f"  DB categories for FY7: {db_cats}")
            # Check amounts in DB
            cursor.execute("SELECT amount FROM cases WHERE fy_id=7 ORDER BY id DESC LIMIT 6")
            db_amounts = [r[0] for r in cursor.fetchall()]
            print(f"  DB amounts for FY7 first 6: {db_amounts}")
            print(f"  Parsed amount (str): '{trans['amount']}', float: {trans['amount']}")
    
    conn.close()

if __name__ == "__main__":
    print("=== Test Import Simulation ===")
    setup_db()
    insert_partial_cases()
    query_inserted_cases()
    simulate_second_import_check()
    print("\nSimulation complete. Likely issue: Category in parsed transactions is 'INT PAID:OVERDUE ACCOUNTS' but dialog uses 'Interest - Other' - string mismatch in find_duplicates.")