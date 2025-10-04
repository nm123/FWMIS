import sqlite3
from datetime import date, datetime
from typing import Tuple, Optional, Dict, Any

class FYError(Exception):
    """Custom exception for financial year operations."""
    pass

class CentralFYUtils:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_fy_from_date(self, target_date: date) -> str:
        """
        Determine the financial year from a given date.
        FY starts April 1st.
        """
        year = target_date.year
        if target_date.month >= 4:
            return f"{year}-{year + 1}"
        else:
            return f"{year - 1}-{year}"

    def get_or_create_fy(self, fy_string: str) -> int:
        """
        Get or create a financial year by string (e.g., '2024-2025').
        Returns the fy_id.
        """
        try:
            start_year, end_year = map(int, fy_string.split('-'))
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?",
                    (start_year, end_year)
                )
                result = cursor.fetchone()
                if result:
                    return result[0]
                
                # Create new FY
                cursor.execute(
                    "INSERT INTO financial_years (start_year, end_year, status, active_period) VALUES (?, ?, 'active', 0)",
                    (start_year, end_year)
                )
                fy_id = cursor.lastrowid
                self._create_periods_for_fy(fy_id, start_year)
                conn.commit()
                return fy_id
        except ValueError:
            raise FYError(f"Invalid FY string format: {fy_string}. Expected 'YYYY-YYYY'.")

    def _create_periods_for_fy(self, fy_id: int, start_year: int):
        """
        Create 12 periods for the FY, all initially closed except the first (April) as open if current.
        But per instructions, using status='open' for active.
        Adapt: set first period open if FY is active.
        For simplicity, set all to 'closed' initially, activate first.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for period_num in range(1, 13):
                month_start = 3 + period_num  # April=4, etc.
                if month_start > 12:
                    year_start = start_year + 1
                    month_start -= 12
                else:
                    year_start = start_year
                
                start_date = date(year_start, month_start, 1)
                # End date: last day of month
                if month_start == 12:
                    end_date = date(year_start + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year_start, month_start + 1, 1) - timedelta(days=1)
                
                status = 'open' if period_num == 1 else 'closed'  # First period open
                cursor.execute(
                    "INSERT INTO periods (fy_id, period_number, status, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
                    (fy_id, period_num, status, start_date.isoformat(), end_date.isoformat())
                )
            conn.commit()

    def activate_fy(self, fy_id: int):
        """
        Activate a financial year: set status='active', update active_period to first open period.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get first open period
            cursor.execute("SELECT id FROM periods WHERE fy_id = ? AND status = 'open' ORDER BY period_number LIMIT 1", (fy_id,))
            period_result = cursor.fetchone()
            active_period = period_result[0] if period_result else 0
            
            cursor.execute(
                "UPDATE financial_years SET status = 'active', active_period = ? WHERE id = ?",
                (active_period, fy_id)
            )
            if cursor.rowcount == 0:
                raise FYError(f"No financial year found with id {fy_id}")
            conn.commit()

    def close_fy(self, fy_id: int):
        """
        Close a financial year: set status='closed', close all periods.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Close all periods
            cursor.execute("UPDATE periods SET status = 'closed' WHERE fy_id = ?", (fy_id,))
            # Close FY
            cursor.execute("UPDATE financial_years SET status = 'closed' WHERE id = ?", (fy_id,))
            if cursor.rowcount == 0:
                raise FYError(f"No financial year found with id {fy_id}")
            conn.commit()

    def validate_fy_closure(self, fy_id: int) -> Dict[str, Any]:
        """
        Validate if FY can be closed: check open periods, cases in open periods.
        Returns {'can_close': bool, 'issues': list[str]}
        """
        issues = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Check open periods
            cursor.execute("SELECT COUNT(*) FROM periods WHERE fy_id = ? AND status = 'open'", (fy_id,))
            open_periods = cursor.fetchone()[0]
            if open_periods > 0:
                issues.append(f"{open_periods} open periods remaining")
            
            # Check cases in open periods
            cursor.execute("""
                SELECT COUNT(*) FROM cases c 
                JOIN periods p ON c.period_id = p.id 
                WHERE p.fy_id = ? AND p.status = 'open'
            """, (fy_id,))
            open_cases = cursor.fetchone()[0]
            if open_cases > 0:
                issues.append(f"{open_cases} cases in open periods")
            
            # Check if FY is active
            cursor.execute("SELECT status FROM financial_years WHERE id = ?", (fy_id,))
            fy_status = cursor.fetchone()
            if not fy_status or fy_status[0] != 'active':
                issues.append("FY is not active")
        
        can_close = len(issues) == 0
        return {'can_close': can_close, 'issues': issues}

    def build_fy_filter_query(self, fy_id: Optional[int] = None) -> Tuple[str, list]:
        """
        Build SQL condition and params for filtering by FY.
        """
        if fy_id is None:
            return '', []
        return 'AND fy_id = ?', [fy_id]