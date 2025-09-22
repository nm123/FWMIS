from .config import DB_PATH, logging


def load_cases():
    import sqlite3

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, transaction_no, bas_payment_no, persal_no, amount, category, responsibility_id, status FROM cases"
        )
        cases = [
            {
                "id": row[0],
                "transaction_no": row[1],
                "bas_payment_no": row[2],
                "persal_no": row[3],
                "amount": row[4],
                "category": row[5],
                "responsibility_id": row[6],
                "status": row[7],
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        return cases
    except sqlite3.Error as e:
        logging.error(f"Failed to load cases: {e}")
        return []
