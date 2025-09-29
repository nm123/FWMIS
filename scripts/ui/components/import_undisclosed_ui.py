from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from scripts.Utilities.ui_theme import (
    apply_theme,
    create_professional_button,
    create_professional_groupbox,
    create_status_label,
    setup_professional_table,
)


def setup_ui(dialog):
    dialog.setStyleSheet(
        """
        QDialog {
            background-color: #f8f9fa;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            margin-top: 1ex;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            color: #495057;
            font-size: 14px;
        }
        QLabel {
            color: #495057;
            font-size: 13px;
        }
        QLineEdit, QDateEdit, QComboBox {
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
            font-size: 13px;
        }
        QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
            border-color: #007bff;
            box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
        }
        QPushButton {
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 500;
            border: none;
            min-width: 100px;
        }
        QPushButton:enabled {
            background-color: #007bff;
            color: white;
        }
        QPushButton:enabled:hover {
            background-color: #0056b3;
        }
        QPushButton:disabled {
            background-color: #6c757d;
            color: #adb5bd;
        }
    """
    )

    layout = QVBoxLayout(dialog)
    layout.setSpacing(15)
    layout.setContentsMargins(20, 20, 20, 20)

    # Header section
    header_layout = QHBoxLayout()
    header_label = QLabel("📊 Import Undisclosed Cases")
    header_label.setStyleSheet(
        """
        QLabel {
            font-size: 18px;
            font-weight: bold;
            color: #343a40;
            margin-bottom: 5px;
        }
    """
    )
    header_layout.addWidget(header_label)
    header_layout.addStretch()
    layout.addLayout(header_layout)

    # File selection section
    file_group = QGroupBox("📁 BAS Report File Selection")
    file_group.setStyleSheet(
        """
        QGroupBox {
            font-weight: bold;
            border: 2px solid #007bff;
            border-radius: 8px;
            margin-top: 1ex;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            color: #007bff;
            font-size: 14px;
        }
    """
    )
    file_layout = QHBoxLayout()
    file_layout.setSpacing(10)

    dialog.file_path_edit = QLineEdit()
    dialog.file_path_edit.setPlaceholderText(
        "Click Browse to select BAS report file (.txt)..."
    )
    dialog.file_path_edit.setReadOnly(True)
    dialog.file_path_edit.setMinimumHeight(35)

    dialog.browse_button = QPushButton("📂 Browse")
    dialog.browse_button.clicked.connect(dialog.browse_file)
    dialog.browse_button.setStyleSheet(
        """
        QPushButton {
            background-color: #28a745;
            color: white;
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 500;
            min-width: 100px;
        }
        QPushButton:hover {
            background-color: #218838;
        }
    """
    )

    file_layout.addWidget(dialog.file_path_edit, 1)
    file_layout.addWidget(dialog.browse_button)
    file_group.setLayout(file_layout)
    layout.addWidget(file_group)

    # Import settings section
    settings_group = QGroupBox("⚙️ Import Configuration")
    settings_layout = QGridLayout()
    settings_layout.setSpacing(15)

    # Category selection
    category_label = QLabel("📋 Category:")
    category_label.setStyleSheet("font-weight: bold;")
    dialog.category_button = QPushButton("🎯 Select Category")
    dialog.category_button.clicked.connect(dialog.select_category)
    dialog.category_button.setMinimumHeight(35)
    dialog.category_label = QLabel("No category selected")
    dialog.category_label.setStyleSheet(
        """
        QLabel {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 8px;
            color: #856404;
            font-style: italic;
        }
    """
    )

    # Date range selection
    date_label = QLabel("📅 Date Range:")
    date_label.setStyleSheet("font-weight: bold;")

    date_range_layout = QHBoxLayout()
    date_range_layout.setSpacing(10)

    from_label = QLabel("From:")
    from_label.setMinimumWidth(40)
    dialog.date_from_edit = QDateEdit()
    dialog.date_from_edit.setDate(QDate.currentDate().addMonths(-1))
    dialog.date_from_edit.setCalendarPopup(True)
    dialog.date_from_edit.setMinimumHeight(35)

    to_label = QLabel("To:")
    to_label.setMinimumWidth(25)
    dialog.date_to_edit = QDateEdit()
    dialog.date_to_edit.setDate(QDate.currentDate())
    dialog.date_to_edit.setCalendarPopup(True)
    dialog.date_to_edit.setMinimumHeight(35)

    date_range_layout.addWidget(from_label)
    date_range_layout.addWidget(dialog.date_from_edit)
    date_range_layout.addWidget(to_label)
    date_range_layout.addWidget(dialog.date_to_edit)
    date_range_layout.addStretch()

    # Parse button
    dialog.parse_button = QPushButton("🔍 Parse File")
    dialog.parse_button.clicked.connect(dialog.parse_file)
    dialog.parse_button.setEnabled(False)
    dialog.parse_button.setMinimumHeight(40)
    dialog.parse_button.setStyleSheet(
        """
        QPushButton {
            background-color: #17a2b8;
            color: white;
            border-radius: 6px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: bold;
            min-width: 120px;
        }
        QPushButton:hover:enabled {
            background-color: #138496;
        }
        QPushButton:disabled {
            background-color: #6c757d;
            color: #adb5bd;
        }
    """
    )

    # Layout arrangement
    settings_layout.addWidget(category_label, 0, 0)
    settings_layout.addWidget(dialog.category_button, 0, 1)
    settings_layout.addWidget(dialog.category_label, 0, 2, 1, 2)

    settings_layout.addWidget(date_label, 1, 0)
    settings_layout.addLayout(date_range_layout, 1, 1, 1, 3)

    settings_layout.addWidget(dialog.parse_button, 2, 1, 1, 2, Qt.AlignCenter)

    settings_group.setLayout(settings_layout)
    layout.addWidget(settings_group)

    # Results section
    results_group = QGroupBox("📋 Transaction Analysis & Processing")
    results_group.setStyleSheet(
        """
        QGroupBox {
            font-weight: bold;
            border: 2px solid #6f42c1;
            border-radius: 8px;
            margin-top: 1ex;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            color: #6f42c1;
            font-size: 14px;
        }
    """
    )
    results_layout = QVBoxLayout()
    results_layout.setSpacing(10)

    # Status display
    status_layout = QHBoxLayout()
    dialog.results_label = QLabel("⏳ Ready to parse BAS file...")
    dialog.results_label.setStyleSheet(
        """
        QLabel {
            background-color: #e9ecef;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 10px;
            color: #495057;
            font-size: 13px;
            font-weight: 500;
        }
    """
    )
    dialog.results_label.setMinimumHeight(40)
    status_layout.addWidget(dialog.results_label)
    results_layout.addLayout(status_layout)

    # Progress bar
    dialog.progress_bar = QProgressBar()
    dialog.progress_bar.setVisible(False)
    dialog.progress_bar.setMinimumHeight(25)
    dialog.progress_bar.setStyleSheet(
        """
        QProgressBar {
            border: 2px solid #ced4da;
            border-radius: 4px;
            text-align: center;
            background-color: #f8f9fa;
        }
        QProgressBar::chunk {
            background-color: #007bff;
            border-radius: 2px;
        }
    """
    )
    results_layout.addWidget(dialog.progress_bar)

    # Transactions table
    table_container = QWidget()
    table_layout = QVBoxLayout()
    table_layout.setContentsMargins(0, 0, 0, 0)

    table_header = QLabel("📊 Parsed Transactions:")
    table_header.setStyleSheet(
        """
        QLabel {
            font-size: 14px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }
    """
    )
    table_layout.addWidget(table_header)

    dialog.transactions_table = QTableWidget()
    dialog.transactions_table.setColumnCount(9)
    dialog.transactions_table.setHorizontalHeaderLabels(
        [
            "🏢 Responsibility",
            "🔢 Type",
            "💰 Amount",
            "📅 Date",
            "📝 Description",
            "✅ Resp Status",
            "🔍 Dup Status",
            "🎫 Case Number",
            "⚡ Actions",
        ]
    )
    dialog.transactions_table.setStyleSheet(
        """
        QTableWidget {
            gridline-color: #dee2e6;
            selection-background-color: #007bff;
            selection-color: white;
            border: 1px solid #ced4da;
            border-radius: 4px;
        }
        QHeaderView::section {
            background-color: #f8f9fa;
            padding: 8px;
            border: 1px solid #dee2e6;
            font-weight: bold;
            color: #495057;
            font-size: 12px;
        }
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #f1f3f4;
        }
        QTableWidget::item:selected {
            background-color: #007bff;
            color: white;
        }
    """
    )

    header = dialog.transactions_table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Interactive)
    header.setStretchLastSection(True)
    dialog.transactions_table.setColumnWidth(0, 200)  # Responsibility
    dialog.transactions_table.setColumnWidth(1, 70)  # Type
    dialog.transactions_table.setColumnWidth(2, 110)  # Amount
    dialog.transactions_table.setColumnWidth(3, 110)  # Date
    dialog.transactions_table.setColumnWidth(4, 220)  # Description
    dialog.transactions_table.setColumnWidth(5, 110)  # Resp Status
    dialog.transactions_table.setColumnWidth(6, 110)  # Dup Status
    dialog.transactions_table.setColumnWidth(7, 130)  # Case Number

    # Connect double-click signal for editing responsibilities
    dialog.transactions_table.itemDoubleClicked.connect(dialog.on_table_double_click)

    # Set minimum row height to accommodate buttons
    dialog.transactions_table.verticalHeader().setDefaultSectionSize(60)

    table_layout.addWidget(dialog.transactions_table)
    table_container.setLayout(table_layout)
    results_layout.addWidget(table_container)

    results_group.setLayout(results_layout)
    layout.addWidget(results_group)

    # Action buttons section
    actions_group = QGroupBox("🎯 Import Actions")
    actions_group.setStyleSheet(
        """
        QGroupBox {
            font-weight: bold;
            border: 2px solid #dc3545;
            border-radius: 8px;
            margin-top: 1ex;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            color: #dc3545;
            font-size: 14px;
        }
    """
    )
    actions_layout = QVBoxLayout()
    actions_layout.setSpacing(15)

    # Workflow buttons
    workflow_layout = QHBoxLayout()
    workflow_layout.setSpacing(12)

    dialog.manage_resp_button = QPushButton("👥 Manage Responsibilities")
    dialog.manage_resp_button.clicked.connect(dialog.manage_responsibilities)
    dialog.manage_resp_button.setEnabled(False)
    dialog.manage_resp_button.setMinimumHeight(40)
    dialog.manage_resp_button.setStyleSheet(
        """
        QPushButton {
            background-color: #6f42c1;
            color: white;
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 500;
            min-width: 160px;
        }
        QPushButton:hover:enabled {
            background-color: #5a32a3;
        }
    """
    )

    dialog.check_duplicates_button = QPushButton("🔍 Check Duplicates")
    dialog.check_duplicates_button.clicked.connect(dialog.check_duplicates)
    dialog.check_duplicates_button.setEnabled(False)
    dialog.check_duplicates_button.setMinimumHeight(40)
    dialog.check_duplicates_button.setStyleSheet(
        """
        QPushButton {
            background-color: #fd7e14;
            color: white;
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 500;
            min-width: 140px;
        }
        QPushButton:hover:enabled {
            background-color: #e8680f;
        }
    """
    )

    dialog.assign_case_numbers_button = QPushButton("🎫 Assign Case Numbers")
    dialog.assign_case_numbers_button.clicked.connect(dialog.assign_case_numbers)
    dialog.assign_case_numbers_button.setEnabled(False)
    dialog.assign_case_numbers_button.setMinimumHeight(45)
    dialog.assign_case_numbers_button.setStyleSheet(
        """
        QPushButton {
            background-color: #2196F3;
            color: white;
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: bold;
            min-width: 180px;
        }
        QPushButton:hover:enabled {
            background-color: #1976d2;
        }
        QPushButton:disabled {
            background-color: #90caf9;
            color: #e3f2fd;
        }
    """
    )

    workflow_layout.addWidget(dialog.manage_resp_button)
    workflow_layout.addWidget(dialog.check_duplicates_button)
    workflow_layout.addWidget(dialog.assign_case_numbers_button)
    workflow_layout.addStretch()

    actions_layout.addLayout(workflow_layout)

    # Final action buttons
    final_actions_layout = QHBoxLayout()
    final_actions_layout.addStretch()

    dialog.import_button = QPushButton("🚀 Import Cases")
    dialog.import_button.clicked.connect(dialog.import_cases)
    dialog.import_button.setEnabled(False)
    dialog.import_button.setMinimumHeight(50)
    dialog.import_button.setStyleSheet(
        """
        QPushButton {
            background-color: #28a745;
            color: white;
            border-radius: 8px;
            padding: 14px 24px;
            font-size: 16px;
            font-weight: bold;
            min-width: 160px;
        }
        QPushButton:hover:enabled {
            background-color: #218838;
            transform: translateY(-1px);
        }
        QPushButton:pressed {
            background-color: #1e7e34;
        }
        QPushButton:disabled {
            background-color: #6c757d;
            color: #adb5bd;
        }
    """
    )

    dialog.cancel_button = QPushButton("❌ Cancel")
    dialog.cancel_button.clicked.connect(dialog.reject)
    dialog.cancel_button.setMinimumHeight(45)
    dialog.cancel_button.setStyleSheet(
        """
        QPushButton {
            background-color: #6c757d;
            color: white;
            border-radius: 6px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 500;
            min-width: 120px;
        }
        QPushButton:hover {
            background-color: #5a6268;
        }
    """
    )

    final_actions_layout.addWidget(dialog.import_button)
    final_actions_layout.addWidget(dialog.cancel_button)

    actions_layout.addLayout(final_actions_layout)
    actions_group.setLayout(actions_layout)
    layout.addWidget(actions_group)
