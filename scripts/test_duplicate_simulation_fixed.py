import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime
from unittest.mock import patch
from scripts.models.bas_parser import BASParser
from scripts.Utilities.import_duplicate_utils import find_duplicates

DB_PATH = 'data/fruitless.db'

def setup_db():
    """Setup DB with schema matching import_duplicate_utils case_dict"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop tables to start fresh
    cursor.execute("DROP TABLE IF EXISTS cases")
    cursor.execute("DROP TABLE IF EXISTS responsibilities")
    cursor.execute("DROP TABLE IF EXISTS financial_years")
    
    # Create exact schema as assumed by case_dict in import_duplicate_utils (28 columns including id)
    cursor.execute("""
    CREATE TABLE financial_years (
        id INTEGER PRIMARY KEY,
        start_year INTEGER,
        end_year INTEGER,
        status TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE responsibilities (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    )
    """)
    
    cursor.execute("""
    CREATE TABLE cases (
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
    
    # Insert FY7 (2024-2025) as open
    cursor.execute("INSERT INTO financial_years (id, start_year, end_year, status) VALUES (7, 2024, 2025, 'open')")
    
    # Insert responsibilities matching parsed names
    responsibilities = [
        ("OFFICE OF THE CFO (POST)", 1),
        ("NIEMEYER MEMORIAL HOSPITAL", 2),
        ("GROENVLEI CLINIC (UTRECHT)", 3),
        ("HLUHLUWE CLINIC (MSEL)", 4),
        ("PROV DIST OFFICE KING CETSHWAYO", 5),
    ]
    for name, resp_id in responsibilities:
        cursor.execute("INSERT INTO responsibilities (id, name) VALUES (?, ?)", (resp_id, name))
    
    conn.commit()
    conn.close()
    print("DB setup complete with matching schema, FY7, and responsibilities.")

def insert_partial_cases():
    """Parse partial file and insert 6 cases"""
    parser = BASParser()
    transactions = parser.parse_file('data/Int_pd_other_partial.TXT', None, None)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted_ids = []
    for i, trans in enumerate(transactions[:6]):
        resp_name = trans['responsibility'].strip()
        cursor.execute("SELECT id FROM responsibilities WHERE LOWER(TRIM(name)) = LOWER(?) LIMIT 1", (resp_name,))
        resp_result = cursor.fetchone()
        resp_id = resp_result[0] if resp_result else 1
        print(f"Resolved '{resp_name}' to ID: {resp_id}")
        
        date_str = trans['date'].strftime('%Y-%m-%d')
        bas_payment_no = trans['number'] if trans['type'] != 'GJ' else None
        bas_payment_date = date_str if trans['type'] != 'GJ' else None
        
        case_data = (
            f'TEST{i+1}', date_str, date_str, date_str, trans['description'],
            bas_payment_no, bas_payment_date, None, 'Interest - Other', resp_id,
            abs(trans['amount']), None, None, None, '[]', 'Alleged', None,
            None, None, None, 7, 1, 'N/A', 'N/A', 'N/A', 'N/A', None
        )
        
        cursor.execute("""
        INSERT INTO cases (
            transaction_no, date_incurred, date_identified, date_reported, description,
            bas_payment_no, bas_payment_date, persal_no, category, responsibility_id,
            amount, source_document, minutes, evidence_path, attachments,
            status, list, assessment_assessed_by, assessment_date, assessment_result,
            fy_id, period_id, criminal_charges, disciplinary_process, loss_recovery,
            prevention_steps, original_list
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, case_data)
        
        inserted_id = cursor.lastrowid
        inserted_ids.append(inserted_id)
        print(f"Inserted case {i+1}: ID={inserted_id}, Resp ID={resp_id}, Amount={abs(trans['amount'])}, Category='Interest - Other', FY ID=7, List=None")
    
    conn.commit()
    conn.close()
    print(f"Successfully inserted {len(inserted_ids)} cases from partial file.")
    return inserted_ids

def verify_partial_import():
    """Query DB for inserted cases to verify"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, responsibility_id, category, amount, fy_id, list FROM cases WHERE fy_id=7 ORDER BY id DESC LIMIT 6")
    rows = cursor.fetchall()
    print("\n=== Verification of Partial Import (Query Results) ===")
    for row in rows:
        print(f"Case ID: {row[0]}, Resp ID: {row[1]}, Category: '{row[2]}', Amount: {row[3]}, FY ID: {row[4]}, List: {row[5]}")
    conn.close()

def mock_get_financial_year():
    """Mock to return '2024-2025' for simulation"""
    return "2024-2025"

def simulate_second_import_check():
    """Parse complete file, check duplicates for first 6"""
    parser = BASParser()
    transactions = parser.parse_file('data/Int_pd_other_complete.TXT', None, None)
    
    print("\n=== Duplicate Check Simulation for First 6 Transactions of Complete File ===")
    match_count = 0
    for i, trans in enumerate(transactions[:6]):
        print(f"\n--- Transaction {i+1} ---")
        print(f"Responsibility: '{trans['responsibility'].strip()}'")
        print(f"Amount: {abs(trans['amount'])}")
        print(f"Date: {trans['date']}")
        
        category_name = 'Interest - Other'
        
        with patch('scripts.Utilities.import_duplicate_utils.get_financial_year', mock_get_financial_year):
            duplicates = find_duplicates(trans, category_name)
        
        print(f"find_duplicates returned {len(duplicates)} matches")
        if len(duplicates) > 0:
            match_count += 1
            print(f"  Matches found for transaction {i+1}")
        else:
            print(f"  No match for transaction {i+1}")
    
    print(f"\nTotal matches: {match_count}/6")
    if match_count == 6:
        print("✅ All 6 duplicates detected successfully.")
    else:
        print("❌ Not all duplicates detected.")

if __name__ == "__main__":
    print("=== Duplicate Detection Test ===")
    setup_db()
    insert_partial_cases()
    verify_partial_import()
    simulate_second_import_check()
    print("\nTest complete.")