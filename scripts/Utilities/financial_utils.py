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
        print(f"DEBUG: generate_transaction_no for FY {fy}")
        print(f"DEBUG: fy_end_year = {fy_end_year}, start_year = {fy_end_year - 1}")

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
def get_active_period_display():
    """
    Get the active period as a display string "Current Open Month: [Month Year]"
    Returns None if no active period found
    """
    import sqlite3
    from calendar import month_name

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get the open financial year with active period
        cursor.execute("""
            SELECT start_year, end_year, active_period
            FROM financial_years
            WHERE status = 'open' AND active_period IS NOT NULL
            ORDER BY start_year DESC
            LIMIT 1
        """)
        fy = cursor.fetchone()
        conn.close()

        if not fy:
            return None

        start_year, end_year, active_period = fy

        # Map period to month and year
        # Financial year starts April (period 1) to March (period 12)
        months = [
            (4, start_year), (5, start_year), (6, start_year), (7, start_year), (8, start_year), (9, start_year),
            (10, start_year), (11, start_year), (12, start_year), (1, end_year), (2, end_year), (3, end_year)
        ]

        if 1 <= active_period <= 12:
            month_num, year = months[active_period - 1]
            month_name_str = month_name[month_num]
            return f"Current Open Month: {month_name_str} {year}"
        else:
            return f"Current Open Period: P{active_period}"

    except sqlite3.Error as e:
        logging.error(f"Failed to get active period display: {e}")
        return None

def get_all_financial_years():
    """
    Get all financial years from the database
    Returns list of tuples: [(id, fy_string, is_open), ...]
    """
    import sqlite3

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, start_year, end_year, status
            FROM financial_years
            ORDER BY start_year DESC
        """)

        financial_years = []
        for row in cursor.fetchall():
            fy_id, start_year, end_year, status = row
            fy_string = f"{start_year}-{end_year}"
            is_open = status == 'open'
            financial_years.append((fy_id, fy_string, is_open))

        conn.close()
        return financial_years

    except sqlite3.Error as e:
        logging.error(f"Failed to get financial years: {e}")
        return []

def get_current_open_financial_year():
    """
    Get the current open financial year
    Returns tuple: (id, fy_string) or None if no open year
    """
    import sqlite3

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, start_year, end_year
            FROM financial_years
            WHERE status = 'open'
            ORDER BY start_year DESC
            LIMIT 1
        """)

        result = cursor.fetchone()
        conn.close()

        if result:
            fy_id, start_year, end_year = result
            fy_string = f"{start_year}-{end_year}"
            return (fy_id, fy_string)

        return None

    except sqlite3.Error as e:
        logging.error(f"Failed to get current open financial year: {e}")
        return None