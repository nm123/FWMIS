import json
import os
import sqlite3
from utils import BASE_DIR, init_db

def migrate_json_to_sqlite():
    init_db()
    conn = sqlite3.connect(os.path.join(BASE_DIR, "fruitless.db"))
    cursor = conn.cursor()

    # Migrate cases
    cases_file = os.path.join(BASE_DIR, "cases.json")
    try:
        if os.path.exists(cases_file):
            with open(cases_file, 'r') as f:
                cases = json.load(f)
            for case in cases:
                cursor.execute("""
                    INSERT OR REPLACE INTO cases (
                        id, transaction_no, date_incurred, date_identified, date_reported, description,
                        bas_payment_no, bas_payment_date, persal_no, category, responsibility_id, amount,
                        source_document, minutes, evidence, status, list,
                        assessment_assessed_by, assessment_date, assessment_result
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    case.get("id"), case.get("transaction_no"), case.get("date_incurred"), case.get("date_identified"),
                    case.get("date_reported"), case.get("description"), case.get("bas_payment_no"),
                    case.get("bas_payment_date"), case.get("persal_no"), case.get("category"),
                    case.get("responsibility_id"), case.get("amount"), case.get("source_document", ""),
                    case.get("minutes", ""), case.get("evidence", ""), case.get("status", "Alleged"),
                    case.get("list", "Checklist"),
                    case["assessment"]["assessed_by"] if case.get("assessment") else None,
                    case["assessment"]["assessment_date"] if case.get("assessment") else None,
                    case["assessment"]["result"] if case.get("assessment") else None
                ))
            print(f"Migrated {len(cases)} cases.")
        else:
            print("No cases.json found, skipping case migration.")
    except Exception as e:
        print(f"Error migrating cases: {str(e)}")

    # Migrate responsibilities
    resp_file = os.path.join(BASE_DIR, "responsibilities.json")
    try:
        if os.path.exists(resp_file):
            with open(resp_file, 'r') as f:
                responsibilities = json.load(f)
            for resp in responsibilities:
                cursor.execute("""
                    INSERT INTO responsibilities (id, name, parent_id, is_posting_level, contacts)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    resp.get("id"), resp.get("name"), resp.get("parent_id"),
                    resp.get("is_posting_level", False), str(resp.get("contacts", []))
                ))
            print(f"Migrated {len(responsibilities)} responsibilities.")
        else:
            print("No responsibilities.json found, skipping responsibility migration.")
    except Exception as e:
        print(f"Error migrating responsibilities: {str(e)}")

    # Migrate categories
    cat_file = os.path.join(BASE_DIR, "categories.json")
    try:
        if os.path.exists(cat_file):
            with open(cat_file, 'r') as f:
                categories = json.load(f)
            for cat in categories:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
            print(f"Migrated {len(categories)} categories.")
        else:
            print("No categories.json found, skipping category migration.")
    except Exception as e:
        print(f"Error migrating categories: {str(e)}")

    # Migrate email templates
    template_file = os.path.join(BASE_DIR, "email_templates.json")
    try:
        if os.path.exists(template_file):
            with open(template_file, 'r') as f:
                templates = json.load(f)
            if isinstance(templates, list):
                for template in templates:
                    if isinstance(template, dict) and "name" in template and "body" in template:
                        cursor.execute("INSERT INTO email_templates (name, body) VALUES (?, ?)", 
                                      (template["name"], template["body"]))
                print(f"Migrated {len(templates)} email templates (list format).")
            elif isinstance(templates, dict):
                for name, body in templates.items():
                    cursor.execute("INSERT INTO email_templates (name, body) VALUES (?, ?)", (name, body))
                print(f"Migrated {len(templates)} email templates (dict format).")
            else:
                print("Unexpected format in email_templates.json, skipping template migration.")
        else:
            print("No email_templates.json found, skipping template migration.")
    except Exception as e:
        print(f"Error migrating email templates: {str(e)}")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate_json_to_sqlite()