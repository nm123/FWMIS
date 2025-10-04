import unittest
from unittest.mock import patch, MagicMock
from datetime import date
from scripts.Utilities.central_fy_utils import CentralFYUtils, FYError
from PyQt5.QtWidgets import QMessageBox  # Mock if needed

class TestCentralFYUtils(unittest.TestCase):
    def setUp(self):
        self.utils = CentralFYUtils('test.db')

    def test_get_fy_from_date_edges(self):
        self.assertEqual(self.utils.get_fy_from_date(date(2024, 4, 1)), '2024-2025')
        self.assertEqual(self.utils.get_fy_from_date(date(2024, 3, 31)), '2023-2024')
        self.assertEqual(self.utils.get_fy_from_date(date(2024, 2, 29)), '2023-2024')

    @patch('sqlite3.connect')
    def test_validate_fy_closure(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = (0,)
        mock_connect.return_value.__enter__.return_value = mock_conn
        result = self.utils.validate_fy_closure(1)
        self.assertTrue(result['can_close'])
        # Test with issue
        mock_cursor.fetchone.return_value = (1,)
        result = self.utils.validate_fy_closure(1)
        self.assertFalse(result['can_close'])
        self.assertIn('open periods', result['issues'][0])

    def test_build_fy_filter_query(self):
        cond, params = self.utils.build_fy_filter_query(7)
        self.assertEqual(cond, 'AND fy_id = ?')
        self.assertEqual(params, [7])
        cond, params = self.utils.build_fy_filter_query()
        self.assertEqual(cond, '')

    @patch('scripts.Utilities.central_fy_utils.CentralFYUtils.activate_fy')
    def test_dialog_integration(self, mock_activate):
        mock_activate.side_effect = FYError('Test error')
        # Simulate dialog (simple assert or mock QMessageBox)
        with patch('PyQt5.QtWidgets.QMessageBox.warning') as mock_warning:
            # Assume dialog instance with utils
            class MockDialog:
                utils = CentralFYUtils()
            dialog = MockDialog()
            try:
                dialog.utils.activate_fy(1)
            except FYError:
                pass
            mock_warning.assert_called()

if __name__ == '__main__':
    unittest.main()