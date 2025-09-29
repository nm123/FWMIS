"""
Mock Classes Module for Responsibility Management

Contains mock UI classes for testing responsibility operations without full UI.
"""


class MockTreeWidgetItem:
    """
    Mock tree widget item for testing.
    """

    def __init__(self, mock_item):
        """
        Initialize mock tree widget item.

        Args:
            mock_item: Mock item data
        """
        self.mock_item = mock_item
        self.resp_id = mock_item.get("id")
        self.text_data = mock_item.get("text", "")

    def text(self, column):
        """
        Get text for specified column.

        Args:
            column: Column index

        Returns:
            str: Text data for the column
        """
        if column == 0:
            return self.text_data
        return ""

    def setText(self, column, text):
        """
        Set text for specified column.

        Args:
            column: Column index
            text: Text to set
        """
        if column == 0:
            self.text_data = text


class MockTreeWidget:
    """
    Mock tree widget for testing.
    """

    def __init__(self, mock_item):
        """
        Initialize mock tree widget.

        Args:
            mock_item: Mock item data
        """
        self.mock_item = mock_item
        self.current_item = MockTreeWidgetItem(mock_item)

    def currentItem(self):
        """
        Get current selected item.

        Returns:
            MockTreeWidgetItem: Current item
        """
        return self.current_item

    def setCurrentItem(self, item):
        """
        Set current selected item.

        Args:
            item: Item to set as current
        """
        self.current_item = item


class MockDialog:
    """
    Mock dialog for testing responsibility operations.
    """

    def __init__(self, parent, resp_id, mock_item):
        """
        Initialize mock dialog.

        Args:
            parent: Parent widget
            resp_id: Responsibility ID
            mock_item: Mock item data
        """
        self.parent = parent
        self.resp_id = resp_id
        self.mock_item = mock_item
        self.tree = MockTreeWidget(mock_item)
        self.saved = False

    def refresh_tree(self):
        """
        Refresh the tree display.
        """
        print(f"Refreshing tree for responsibility {self.resp_id}")

    def clear_form(self):
        """
        Clear the form data.
        """
        print(f"Clearing form for responsibility {self.resp_id}")

    def accept(self):
        """
        Accept the dialog changes.
        """
        self.saved = True
        print(f"Dialog accepted for responsibility {self.resp_id}")

    def exec_(self):
        """
        Execute the dialog.

        Returns:
            int: Dialog result code
        """
        return 1 if self.saved else 0
