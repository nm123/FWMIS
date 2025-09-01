from datetime import datetime
from .config import DB_PATH, logging

def get_financial_year():
    today = datetime.now()
    year = today.year
    if today.month >= 4:
        return f"{year}-{year + 1}"
    return f"{year - 1}-{year}"

def generate_transaction_no(fy):
    """
    Generate transaction number in format YYYY00001 based on financial year
    Example: 202600001, 202600002, etc. for FY 2025-2026
    """
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Extract the ending year from financial year (e.g., "2025-2026" -> 2026)
        fy_end_year = int(fy.split('-')[1])

        # Get or create case counter for this financial year
        cursor.execute("""
            SELECT counter FROM fy_case_counters WHERE fy_id = (
                SELECT id FROM financial_years WHERE start_year = ?
            )
        """, (fy_end_year - 1,))

        result = cursor.fetchone()

        if result:
            counter = result[0] + 1
            cursor.execute("""
                UPDATE fy_case_counters SET counter = ? WHERE fy_id = (
                    SELECT id FROM financial_years WHERE start_year = ?
                )
            """, (counter, fy_end_year - 1))
        else:
            # Create new counter if it doesn't exist
            cursor.execute("""
                SELECT id FROM financial_years WHERE start_year = ?
            """, (fy_end_year - 1,))
            fy_result = cursor.fetchone()

            if fy_result:
                fy_id = fy_result[0]
                counter = 1
                cursor.execute("""
                    INSERT INTO fy_case_counters (fy_id, counter) VALUES (?, ?)
                """, (fy_id, counter))
            else:
                # Fallback to timestamp format if FY not found
                conn.close()
                return f"TRANS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        conn.commit()
        conn.close()

        # Format as YYYY00001 (padded to 5 digits)
        return f"{fy_end_year}{counter:05d}"

    except sqlite3.Error as e:
        logging.error(f"Failed to generate transaction number: {e}")
        # Fallback to timestamp format
        return f"TRANS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

def create_year_folder(fy):
    import os
    from .config import DATA_DIR
    folder = os.path.join(DATA_DIR, fy)
    os.makedirs(folder, exist_ok=True)
    return folder