import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from scripts.Utilities.config import DB_PATH
from scripts.Utilities.db_utils import get_db_connection, get_current_delegation

def get_write_off_recommended_cases() -> List[Dict]:
    """Get all cases with Write-Off Recommended status."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.transaction_no, c.base_transaction_no, 
                       c.assessment_status, c.lc_status, c.suffixes,
                       c.responsibility_id, c.amount, c.description,
                       c.evidence_paths, r.name as responsibility_name
                FROM cases c
                LEFT JOIN responsibilities r ON c.responsibility_id = r.id
                WHERE c.lc_status = 'Write-Off Recommended'
                AND c.suffixes LIKE '%-WOR%'
                ORDER BY c.transaction_no
            """)
            
            cases = []
            for row in cursor.fetchall():
                case = {
                    'id': row[0],
                    'transaction_no': row[1],
                    'base_transaction_no': row[2],
                    'assessment_status': row[3],
                    'lc_status': row[4],
                    'suffixes': row[5],
                    'responsibility_id': row[6],
                    'amount': row[7] or 0,
                    'description': row[8] or '',
                    'evidence_paths': row[9],
                    'responsibility_name': row[10] or 'Unknown'
                }
                cases.append(case)
            return cases
    except Exception as e:
        print(f"Error fetching write-off recommended cases: {e}")
        return []

def group_cases_by_delegation(cases: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Group cases by delegation (CFO vs HOD) based on current delegation limits."""
    delegation = get_current_delegation()
    if not delegation:
        # Fallback to default if no delegation found
        cfo_limit = 50000
    else:
        cfo_limit = delegation['cfo_limit']
    
    cfo_cases = []
    hod_cases = []
    
    for case in cases:
        if case['amount'] <= cfo_limit:
            cfo_cases.append(case)
        else:
            hod_cases.append(case)
    
    return cfo_cases, hod_cases

def generate_annexure_number(role: str, financial_year_id: int) -> str:
    """Generate next annexure number for given role and financial year."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get the financial year end year for formatting
            cursor.execute("""
                SELECT end_year FROM financial_years WHERE id = ?
            """, (financial_year_id,))
            
            fy_row = cursor.fetchone()
            if not fy_row:
                raise ValueError(f"Financial year ID {financial_year_id} not found")
            
            end_year = fy_row[0]
            
            # Get the next sequence number for this role and FY
            cursor.execute("""
                SELECT COUNT(*) FROM annexures 
                WHERE role = ? AND financial_year_id = ?
            """, (role, financial_year_id))
            
            count = cursor.fetchone()[0]
            next_seq = count + 1
            
            # Format: FWWOC-2026001 or FWWOH-2026001
            prefix = "FWWOC" if role == "CFO" else "FWWOH"
            annexure_no = f"{prefix}-{end_year}{next_seq:03d}"
            
            return annexure_no
    except Exception as e:
        print(f"Error generating annexure number: {e}")
        return f"FWWO{'C' if role == 'CFO' else 'H'}-2026001"

def create_annexure(role: str, financial_year_id: int, case_ids: List[int]) -> Optional[int]:
    """Create a new annexure and assign cases to it."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Generate annexure number
            annexure_no = generate_annexure_number(role, financial_year_id)
            
            # Create annexure record
            cursor.execute("""
                INSERT INTO annexures (annexure_no, role, financial_year_id)
                VALUES (?, ?, ?)
            """, (annexure_no, role, financial_year_id))
            
            annexure_id = cursor.lastrowid
            
            # Assign cases to annexure
            for case_id in case_ids:
                cursor.execute("""
                    INSERT INTO annexure_cases (annexure_id, case_id)
                    VALUES (?, ?)
                """, (annexure_id, case_id))
                
                # Update case status
                cursor.execute("""
                    UPDATE cases 
                    SET write_off_status = 'Write-Off Pending'
                    WHERE id = ?
                """, (case_id,))
            
            return annexure_id
    except Exception as e:
        print(f"Error creating annexure: {e}")
        return None

def get_annexure_details(annexure_id: int) -> Optional[Dict]:
    """Get detailed information about an annexure."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get annexure info
            cursor.execute("""
                SELECT a.id, a.annexure_no, a.role, a.financial_year_id, a.created_at
                FROM annexures a
                WHERE a.id = ?
            """, (annexure_id,))
            
            annexure_row = cursor.fetchone()
            if not annexure_row:
                return None
            
            annexure = {
                'id': annexure_row[0],
                'annexure_no': annexure_row[1],
                'role': annexure_row[2],
                'financial_year_id': annexure_row[3],
                'created_at': annexure_row[4]
            }
            
            # Get cases in this annexure
            cursor.execute("""
                SELECT c.id, c.transaction_no, c.base_transaction_no,
                       c.responsibility_id, c.amount, c.description,
                       c.evidence_paths, r.name as responsibility_name
                FROM cases c
                JOIN annexure_cases ac ON c.id = ac.case_id
                LEFT JOIN responsibilities r ON c.responsibility_id = r.id
                WHERE ac.annexure_id = ?
                ORDER BY c.transaction_no
            """, (annexure_id,))
            
            cases = []
            for row in cursor.fetchall():
                case = {
                    'id': row[0],
                    'transaction_no': row[1],
                    'base_transaction_no': row[2],
                    'responsibility_id': row[3],
                    'amount': row[4] or 0,
                    'description': row[5] or '',
                    'evidence_paths': row[6],
                    'responsibility_name': row[7] or 'Unknown'
                }
                cases.append(case)
            
            annexure['cases'] = cases
            annexure['total_amount'] = sum(case['amount'] for case in cases)
            annexure['case_count'] = len(cases)
            
            return annexure
    except Exception as e:
        print(f"Error getting annexure details: {e}")
        return None

def get_lc_minutes_path(case_id: int) -> Optional[str]:
    """Get the LC minutes file path for a case."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT evidence_paths FROM cases WHERE id = ?", (case_id,))
            row = cursor.fetchone()
            
            if row and row[0]:
                evidence_data = json.loads(row[0])
                # Look for LC minutes in evidence paths
                lc_minutes = evidence_data.get('lc_minutes') or evidence_data.get('loss_control_minutes')
                if lc_minutes and isinstance(lc_minutes, str):
                    return lc_minutes
            return None
    except Exception as e:
        print(f"Error getting LC minutes path: {e}")
        return None

def get_current_financial_year_id() -> Optional[int]:
    """Get the current active financial year ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Try different column names for active status
            cursor.execute("""
                SELECT id FROM financial_years 
                ORDER BY id DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        print(f"Error getting current financial year: {e}")
        return None

def get_all_annexures() -> List[Dict]:
    """Get all annexures with summary information."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.id, a.annexure_no, a.role, a.financial_year_id, a.created_at,
                       COUNT(ac.case_id) as case_count,
                       COALESCE(SUM(c.amount), 0) as total_amount
                FROM annexures a
                LEFT JOIN annexure_cases ac ON a.id = ac.annexure_id
                LEFT JOIN cases c ON ac.case_id = c.id
                GROUP BY a.id
                ORDER BY a.created_at DESC
            """)
            
            annexures = []
            for row in cursor.fetchall():
                annexure = {
                    'id': row[0],
                    'annexure_no': row[1],
                    'role': row[2],
                    'financial_year_id': row[3],
                    'created_at': row[4],
                    'case_count': row[5],
                    'total_amount': row[6]
                }
                annexures.append(annexure)
            
            return annexures
    except Exception as e:
        print(f"Error getting all annexures: {e}")
        return []
