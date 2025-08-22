import os
import sqlite3
import datetime
from pathlib import Path
import json
import re
import logging

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Set up logging
logging.basicConfig(filename=os.path.join(BASE_DIR, 'app.log'), level=logging.ERROR)

def get_financial_year():
    today = datetime.date.today()
    year = today.year if today.month >= 4 else today.year - 1
    return f"{year}-{year+1}"

def generate_transaction_no(case_id):
    financial_year = get_financial_year()
    return f"{financial_year}-{str(case_id).zfill(4)}"

def create_year_folder():
    financial_year = get_financial_year()
    year_folder = os.path.join(BASE_DIR, financial_year)
    os.makedirs(year_folder, exist_ok=True)
    return year_folder

def save_cases(cases):
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY,
            transaction_no TEXT UNIQUE,
            date_incurred TEXT,
            date_identified TEXT,
            date_reported TEXT,
            description TEXT,
            bas_payment_no TEXT,
            bas_payment_date TEXT,
            persal_no TEXT,
            category TEXT,
            responsibility_id INTEGER,
            amount REAL,
            source_document TEXT,
            minutes TEXT,
            evidence_path TEXT,
            status TEXT,
            list TEXT,
            assessment_assessed_by TEXT,
            assessment_date TEXT,
            assessment_result TEXT
        )
    """)
    cursor.executemany("""
        INSERT OR REPLACE INTO cases (
            id, transaction_no, date_incurred, date_identified, date_reported, description,
            bas_payment_no, bas_payment_date, persal_no, category, responsibility_id, amount,
            source_document, minutes, evidence_path, status, list, assessment_assessed_by,
            assessment_date, assessment_result
        )
        VALUES (
            :id, :transaction_no, :date_incurred, :date_identified, :date_reported, :description,
            :bas_payment_no, :bas_payment_date, :persal_no, :category, :responsibility_id, :amount,
            :source_document, :minutes, :evidence_path, :status, :list, :assessment_assessed_by,
            :assessment_date, :assessment_result
        )
    """, cases)
    conn.commit()
    conn.close()

def load_cases():
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, transaction_no, date_incurred, date_identified, date_reported, description,
               bas_payment_no, bas_payment_date, persal_no, category, responsibility_id, amount,
               source_document, minutes, evidence_path, status, list, assessment_assessed_by,
               assessment_date, assessment_result
        FROM cases
    """)
    rows = cursor.fetchall()
    cases = [
        {
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
            "status": row[15],
            "list": row[16],
            "assessment_assessed_by": row[17],
            "assessment_date": row[18],
            "assessment_result": row[19]
        }
        for row in rows
    ]
    conn.close()
    return cases

def save_audit_log(action, details):
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            details TEXT,
            timestamp TEXT
        )
    """)
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO audit_logs (action, details, timestamp) VALUES (?, ?, ?)", (action, json.dumps(details), timestamp))
    conn.commit()
    conn.close()

def get_effective_contacts(responsibility_id, responsibilities):
    contacts = []
    resp = next((r for r in responsibilities if r["id"] == responsibility_id), None)
    if resp and resp["contacts"]:
        contacts.extend(resp["contacts"])
    if resp and resp["parent_id"]:
        contacts.extend(get_effective_contacts(resp["parent_id"], responsibilities))
    return contacts

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def get_subtree_resp_ids(resp_id, responsibilities):
    subtree_ids = [resp_id]
    children = [r["id"] for r in responsibilities if r["parent_id"] == resp_id]
    for child_id in children:
        subtree_ids.extend(get_subtree_resp_ids(child_id, responsibilities))
    return subtree_ids

def load_responsibilities():
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS responsibilities (
            id INTEGER PRIMARY KEY,
            name TEXT,
            parent_id INTEGER,
            is_posting_level BOOLEAN,
            contacts TEXT
        )
    """)
    cursor.execute("SELECT id, name, parent_id, is_posting_level, contacts FROM responsibilities")
    rows = cursor.fetchall()
    responsibilities = []
    for row in rows:
        try:
            contacts = json.loads(row[4]) if row[4] else []
            if not isinstance(contacts, list):
                logging.error(f"Invalid contacts format for responsibility ID {row[0]}: {row[4]}")
                contacts = []
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error for responsibility ID {row[0]}: {str(e)}, data: {row[4]}")
            if row[4]:
                try:
                    fixed_json = row[4].replace("'", '"')
                    contacts = json.loads(fixed_json)
                    if not isinstance(contacts, list):
                        contacts = []
                except json.JSONDecodeError:
                    contacts = []
            else:
                contacts = []
        responsibilities.append({
            "id": row[0],
            "name": row[1],
            "parent_id": row[2],
            "is_posting_level": bool(row[3]),
            "contacts": contacts
        })
    conn.close()
    return responsibilities

def save_responsibilities(responsibilities):
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM responsibilities")
    cursor.executemany("""
        INSERT INTO responsibilities (id, name, parent_id, is_posting_level, contacts)
        VALUES (?, ?, ?, ?, ?)
    """, [
        (r["id"], r["name"], r["parent_id"], r["is_posting_level"], json.dumps(r["contacts"]))
        for r in responsibilities
    ])
    conn.commit()
    conn.close()

def load_categories():
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    """)
    cursor.execute("SELECT id, name FROM categories")
    rows = cursor.fetchall()
    categories = [{"id": row[0], "name": row[1]} for row in rows]
    conn.close()
    return categories

def save_categories(categories):
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories")
    cursor.executemany("""
        INSERT INTO categories (id, name)
        VALUES (?, ?)
    """, [(c["id"], c["name"]) for c in categories])
    conn.commit()
    conn.close()

def load_email_templates():
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_templates (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            body TEXT
        )
    """)
    cursor.execute("SELECT id, name, body FROM email_templates")
    rows = cursor.fetchall()
    templates = [{"id": row[0], "name": row[1], "body": row[2]} for row in rows]
    conn.close()
    return templates

def save_email_templates(templates):
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM email_templates")
    cursor.executemany("""
        INSERT INTO email_templates (id, name, body)
        VALUES (?, ?, ?)
    """, [(t["id"], t["name"], t["body"]) for t in templates])
    conn.commit()
    conn.close()