"""
Unit tests for message box utilities.
"""

import pytest
from unittest.mock import Mock, patch


class TestMessageBoxUtils:
    """Test cases for message box utility functions."""

    @patch('PyQt5.QtWidgets.QMessageBox.information')
    def test_show_info_message(self, mock_info):
        """Test showing an informational message."""
        from scripts.Utilities.message_box_utils import show_info_message

        # Mock parent widget
        parent = Mock()

        # Call function
        show_info_message(parent, "Test Title", "Test Message")

        # Verify QMessageBox.information was called correctly
        mock_info.assert_called_once_with(parent, "Test Title", "Test Message")

    @patch('PyQt5.QtWidgets.QMessageBox.warning')
    def test_show_warning_message(self, mock_warning):
        """Test showing a warning message."""
        from scripts.Utilities.message_box_utils import show_warning_message

        parent = Mock()
        show_warning_message(parent, "Warning Title", "Warning Message")

        mock_warning.assert_called_once_with(parent, "Warning Title", "Warning Message")

    @patch('PyQt5.QtWidgets.QMessageBox.critical')
    def test_show_error_message(self, mock_critical):
        """Test showing an error message."""
        from scripts.Utilities.message_box_utils import show_error_message

        parent = Mock()
        show_error_message(parent, "Error Title", "Error Message")

        mock_critical.assert_called_once_with(parent, "Error Title", "Error Message")

    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_show_confirmation_dialog_yes(self, mock_question):
        """Test confirmation dialog returning Yes."""
        from scripts.Utilities.message_box_utils import show_confirmation_dialog
        from PyQt5.QtWidgets import QMessageBox

        # Mock QMessageBox.question to return Yes
        mock_question.return_value = QMessageBox.Yes

        parent = Mock()
        result = show_confirmation_dialog(parent, "Confirm", "Are you sure?")

        assert result is True
        mock_question.assert_called_once()

    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_show_confirmation_dialog_no(self, mock_question):
        """Test confirmation dialog returning No."""
        from scripts.Utilities.message_box_utils import show_confirmation_dialog
        from PyQt5.QtWidgets import QMessageBox

        # Mock QMessageBox.question to return No
        mock_question.return_value = QMessageBox.No

        parent = Mock()
        result = show_confirmation_dialog(parent, "Confirm", "Are you sure?")

        assert result is False
        mock_question.assert_called_once()

    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_show_save_confirmation_save(self, mock_question):
        """Test save confirmation returning Save."""
        from scripts.Utilities.message_box_utils import show_save_confirmation
        from PyQt5.QtWidgets import QMessageBox

        # Mock QMessageBox.question to return Save
        mock_question.return_value = QMessageBox.Save

        parent = Mock()
        result = show_save_confirmation(parent, "Save changes?")

        assert result is True
        mock_question.assert_called_once()

    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_show_save_confirmation_cancel(self, mock_question):
        """Test save confirmation returning Cancel."""
        from scripts.Utilities.message_box_utils import show_save_confirmation
        from PyQt5.QtWidgets import QMessageBox

        # Mock QMessageBox.question to return Cancel
        mock_question.return_value = QMessageBox.Cancel

        parent = Mock()
        result = show_save_confirmation(parent, "Save changes?")

        assert result is False
        mock_question.assert_called_once()

    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_show_delete_confirmation_yes(self, mock_question):
        """Test delete confirmation returning Yes."""
        from scripts.Utilities.message_box_utils import show_delete_confirmation
        from PyQt5.QtWidgets import QMessageBox

        # Mock QMessageBox.question to return Yes
        mock_question.return_value = QMessageBox.Yes

        parent = Mock()
        result = show_delete_confirmation(parent, "record")

        assert result is True
        # Verify the message contains the item type
        call_args = mock_question.call_args
        message = call_args[0][2]  # Third positional argument is the message
        assert "record" in message

    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_show_delete_confirmation_no(self, mock_question):
        """Test delete confirmation returning No."""
        from scripts.Utilities.message_box_utils import show_delete_confirmation
        from PyQt5.QtWidgets import QMessageBox

        # Mock QMessageBox.question to return No
        mock_question.return_value = QMessageBox.No

        parent = Mock()
        result = show_delete_confirmation(parent, "item")

        assert result is False
