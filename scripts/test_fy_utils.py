import unittest
from unittest.mock import patch, MagicMock
from datetime import date
import sqlite3

from scripts.Utilities.central_fy_utils import CentralFYUtils, FYError


class TestCentralFYUtils(unittest.TestCase):
    def setUp(self):
        self.utils = CentralFYUtils(db_path=':memory:')  # In-memory DB for testing
        self.setup_test_db()

    def setup_test_db(self):
        """Setup a minimal test database."""
        conn = sqlite3.connect(self.utils.db_path)
        cursor = conn.cursor()
        
        # Create financial_years table
        cursor.execute("""
            CREATE TABLE financial_years (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_year INTEGER,
                end_year INTEGER,
                status TEXT,
                active_period INTEGER
            )
        """)
        
        # Create periods table
        cursor.execute("""
            CREATE TABLE periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fy_id INTEGER,
                period_number INTEGER,
                start_date TEXT,
                end_date TEXT,
                status TEXT
            )
        """)
        
        # Create cases table (minimal)
        cursor.execute("""
            CREATE TABLE cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fy_id INTEGER,
                is_finalized BOOLEAN
            )
        """)
        
        conn.commit()
        conn.close()

    def test_get_fy_from_date(self):
        """Test FY determination for various dates, including edges and leap years."""
        # April 1, 2024 -> 2024-2025
        self.assertEqual(self.utils.get_fy_from_date(date(2024, 4, 1)), '2024-2025')
        
        # March 31, 2024 -> 2023-2024
        self.assertEqual(self.utils.get_fy_from_date(date(2024, 3, 31)), '2023-2024')
        
        # Feb 29, 2024 (leap) -> 2023-2024
        self.assertEqual(self.utils.get_fy_from_date(date(2024, 2, 29)), '2023-2024')
        
        # Jan 1, 2024 -> 2023-2024
        self.assertEqual(self.utils.get_fy_from_date(date(2024, 1, 1)), '2023-2024')
        
        # April 1, 2023 -> 2023-2024
        self.assertEqual(self.utils.get_fy_from_date(date(2023, 4, 1)), '2023-2024')

    @patch('sqlite3.connect')
    def test_validate_fy_closure(self, mock_connect):
        """Test FY closure validation with mocked DB fetches."""
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value
        
        # Case 1: Valid - no open periods, no non-finalized cases
        mock_cursor.fetchone.return_value = (0,)  # open periods
        mock_cursor.fetchone.return_value = (0,)  # non-finalized cases (call twice)
        mock_connect.return_value.__enter__.return_value = mock_conn
        
        result = self.utils.validate_fy_closure(1)
        self.assertTrue(result['can_close'])
        self.assertEqual(result['issues'], [])
        
        # Case 2: Invalid - open periods
        mock_cursor.fetchone.side_effect = [(1,), (0,)]
        result = self.utils.validate_fy_closure(1)
        self.assertFalse(result['can_close'])
        self.assertIn('open periods', result['issues'][0])

    def test_build_fy_filter_query(self):
        """Test building FY filter query."""
        utils = CentralFYUtils()
        
        # With fy_id
        condition, params = utils.build_fy_filter_query(1)
        self.assertEqual(condition, 'fy_id = ?')
        self.assertEqual(params, [1])
        
        # Without fy_id
        condition, params = utils.build_fy_filter_query(None)
        self.assertIsNone(condition)
        self.assertEqual(params, [])


if __name__ == '__main__':
    unittest.main()