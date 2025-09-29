from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from scripts.Utilities.ui_theme import (
    create_professional_button,
    setup_professional_table,
)


class ProfessionalTable:
    """A professional table component with consistent styling and functionality"""

    def __init__(self, headers=None, emojis=None):
        self.table = QTableWidget()
        self.headers = headers or []
        self.emojis = emojis or []

        self.setup_table()

    def setup_table(self):
        """Setup the table with professional styling"""
        if self.headers:
            self.table.setColumnCount(len(self.headers))
            self.table.setHorizontalHeaderLabels(self.headers)

        if self.emojis:
            # Add emojis to headers if provided
            header = self.table.horizontalHeader()
            for i, emoji in enumerate(self.emojis):
                if i < len(self.headers):
                    current_text = self.headers[i]
                    self.table.setHorizontalHeaderItem(
                        i, QTableWidgetItem(f"{emoji} {current_text}")
                    )

        setup_professional_table(self.table)

        # Set default properties
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

        # Set row height for better button display
        self.table.verticalHeader().setDefaultSectionSize(60)

    def get_table(self):
        """Get the table widget"""
        return self.table

    def set_column_width(self, column, width):
        """Set the width of a specific column"""
        self.table.setColumnWidth(column, width)

    def set_column_widths(self, widths):
        """Set widths for multiple columns"""
        for i, width in enumerate(widths):
            if i < self.table.columnCount():
                self.table.setColumnWidth(i, width)

    def add_row(self, data, actions=None):
        """Add a row to the table"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Add data columns
        for col, value in enumerate(data):
            if col < self.table.columnCount():
                if (
                    isinstance(value, str)
                    and value.replace(".", "")
                    .replace("-", "")
                    .replace("/", "")
                    .isdigit()
                ):
                    # Right-align numeric values
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row, col, item)
                else:
                    self.table.setItem(row, col, item)

        # Add actions column if provided
        if actions and len(data) < self.table.columnCount():
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            for action_text, action_callback in actions:
                action_btn = create_professional_button(action_text, "secondary")
                action_btn.clicked.connect(action_callback)
                actions_layout.addWidget(action_btn)

            self.table.setCellWidget(row, self.table.columnCount() - 1, actions_widget)

    def clear_rows(self):
        """Clear all rows from the table"""
        self.table.setRowCount(0)

    def get_selected_row_data(self):
        """Get data from the selected row"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            return None

        # Get data from first selected row
        row = min(selected_rows)
        row_data = []

        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                row_data.append(item.text())
            else:
                # Check if it's a widget (like actions column)
                widget = self.table.cellWidget(row, col)
                if widget:
                    row_data.append(str(widget))
                else:
                    row_data.append("")

        return row_data

    def select_row(self, row_index):
        """Select a specific row"""
        if row_index < self.table.rowCount():
            self.table.selectRow(row_index)

    def get_row_count(self):
        """Get the number of rows"""
        return self.table.rowCount()

    def get_column_count(self):
        """Get the number of columns"""
        return self.table.columnCount()

    def set_selection_mode(self, mode):
        """Set the selection mode"""
        self.table.setSelectionMode(mode)

    def set_selection_behavior(self, behavior):
        """Set the selection behavior"""
        self.table.setSelectionBehavior(behavior)


class TableWithControls:
    """A table component with built-in controls"""

    def __init__(self, title="", headers=None, emojis=None):
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)
        self.layout.setSpacing(10)

        # Title
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #495057;"
            )
            self.layout.addWidget(title_label)

        # Create table
        self.table = ProfessionalTable(headers, emojis)
        self.layout.addWidget(self.table.get_table())

        # Controls layout
        self.controls_layout = QHBoxLayout()
        self.controls_layout.setSpacing(10)
        self.layout.addLayout(self.controls_layout)

    def get_widget(self):
        """Get the main widget"""
        return self.widget

    def get_table(self):
        """Get the table component"""
        return self.table

    def add_control(self, text, callback, button_type="secondary"):
        """Add a control button"""
        button = create_professional_button(text, button_type)
        button.clicked.connect(callback)
        self.controls_layout.addWidget(button)
        return button

    def add_stretch(self):
        """Add stretch to controls layout"""
        self.controls_layout.addStretch()


class DataTable:
    """A data table with pagination and search capabilities"""

    def __init__(self, headers=None, emojis=None):
        self.headers = headers or []
        self.emojis = emojis or []
        self.all_data = []
        self.filtered_data = []
        self.current_page = 0
        self.page_size = 50

        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)

        # Search controls
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_data)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        self.layout.addLayout(search_layout)

        # Table
        self.table = ProfessionalTable(self.headers, self.emojis)
        self.layout.addWidget(self.table.get_table())

        # Pagination controls
        pagination_layout = QHBoxLayout()

        self.prev_button = create_professional_button("Previous", "secondary")
        self.prev_button.clicked.connect(self.previous_page)

        self.page_label = QLabel("Page 1 of 1")

        self.next_button = create_professional_button("Next", "secondary")
        self.next_button.clicked.connect(self.next_page)

        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.next_button)

        self.layout.addLayout(pagination_layout)

    def get_widget(self):
        """Get the main widget"""
        return self.widget

    def set_data(self, data):
        """Set the data for the table"""
        self.all_data = data
        self.filtered_data = data.copy()
        self.current_page = 0
        self.update_display()

    def filter_data(self):
        """Filter data based on search input"""
        search_text = self.search_input.text().lower().strip()

        if not search_text:
            self.filtered_data = self.all_data.copy()
        else:
            self.filtered_data = []
            for row in self.all_data:
                if any(search_text in str(cell).lower() for cell in row):
                    self.filtered_data.append(row)

        self.current_page = 0
        self.update_display()

    def update_display(self):
        """Update the table display with current page data"""
        self.table.clear_rows()

        start_index = self.current_page * self.page_size
        end_index = start_index + self.page_size

        page_data = self.filtered_data[start_index:end_index]

        for row_data in page_data:
            self.table.add_row(row_data)

        # Update pagination controls
        total_pages = max(
            1, (len(self.filtered_data) + self.page_size - 1) // self.page_size
        )
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")

        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_display()

    def next_page(self):
        """Go to next page"""
        total_pages = max(
            1, (len(self.filtered_data) + self.page_size - 1) // self.page_size
        )
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_display()
