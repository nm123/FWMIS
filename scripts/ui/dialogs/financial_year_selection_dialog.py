import sqlite3

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QFont, QWheelEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import (
    get_all_financial_years,
    get_financial_year,
)
from scripts.Utilities.ui_theme import apply_theme, create_professional_button


class NoWheelComboBox(QComboBox):
    """Custom QComboBox that ignores mouse wheel events unless focused"""

    def wheelEvent(self, event: QWheelEvent):
        """Override wheel event to only accept when widget has focus"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # Ignore wheel event when not focused
            event.ignore()


class FinancialYearSelectionDialog(QDialog):
    """Dialog for selecting financial year when the determined FY doesn't exist"""

    def __init__(self, determined_fy=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ Financial Year Selection Required")
        self.setFixedSize(500, 350)
        self.setWindowIconText("📅")

        # Apply professional theme
        apply_theme(self)

        self.determined_fy = determined_fy
        self.selected_fy = None
        self.selected_fy_id = None

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        # Warning header
        warning_group = QGroupBox("🚨 Critical Warning")
        warning_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dc3545;
                border-radius: 8px;
                margin-top: 1ex;
                background-color: #fff5f5;
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

        warning_layout = QVBoxLayout()
        warning_label = QLabel(
            "The system has determined a financial year that does not exist in the database.\n\n"
            "Importing cases into a non-existent financial year will create orphaned cases "
            "that cannot be properly managed or viewed in the system."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(
            """
            QLabel {
                color: #721c24;
                font-size: 13px;
                line-height: 1.4;
            }
        """
        )
        warning_layout.addWidget(warning_label)
        warning_group.setLayout(warning_layout)
        layout.addWidget(warning_group)

        # FY Information
        info_group = QGroupBox("📊 Financial Year Information")
        info_layout = QFormLayout()
        info_layout.setSpacing(10)

        determined_label = QLabel(
            f"System Determined FY: {self.determined_fy or 'Unknown'}"
        )
        determined_label.setStyleSheet("font-weight: bold; color: #856404;")
        info_layout.addRow("Auto-Determined:", determined_label)

        status_label = QLabel("❌ Does Not Exist in Database")
        status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        info_layout.addRow("Status:", status_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # FY Selection
        selection_group = QGroupBox("🎯 Select Correct Financial Year")
        selection_layout = QVBoxLayout()
        selection_layout.setSpacing(15)

        instruction_label = QLabel(
            "Please select the correct financial year for these transactions:"
        )
        instruction_label.setStyleSheet("font-size: 13px;")
        selection_layout.addWidget(instruction_label)

        # FY Combo box
        self.fy_combo = NoWheelComboBox()
        self.fy_combo.setMinimumHeight(35)
        self.fy_combo.setStyleSheet(
            """
            QComboBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """
        )

        # Load available financial years
        self.load_financial_years()
        selection_layout.addWidget(self.fy_combo)

        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.cancel_button = create_professional_button("❌ Cancel Import", "secondary")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.select_button = create_professional_button("✅ Use Selected FY", "success")
        self.select_button.clicked.connect(self.accept_selection)
        self.select_button.setDefault(True)
        buttons_layout.addWidget(self.select_button)

        layout.addLayout(buttons_layout)

        # Connect signals
        self.fy_combo.currentIndexChanged.connect(self.on_fy_selected)

    def load_financial_years(self):
        """Load available financial years into the combo box"""
        try:
            financial_years = get_all_financial_years()

            self.fy_combo.clear()
            self.fy_combo.addItem("Select Financial Year...", None)

            for fy_id, fy_string, is_open in financial_years:
                status_text = " (Open)" if is_open else " (Closed)"
                display_text = f"{fy_string}{status_text}"
                self.fy_combo.addItem(display_text, (fy_id, fy_string, is_open))

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load financial years:\n{str(e)}"
            )
            self.fy_combo.addItem("Error loading financial years", None)

    def on_fy_selected(self, index):
        """Handle financial year selection"""
        if index > 0:  # Skip "Select Financial Year..." item
            fy_data = self.fy_combo.itemData(index)
            if fy_data:
                self.selected_fy_id, self.selected_fy, is_open = fy_data
                print(
                    f"DEBUG: Selected FY: {self.selected_fy} (ID: {self.selected_fy_id}, Open: {is_open})"
                )

    def accept_selection(self):
        """Accept the selected financial year"""
        if not self.selected_fy:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a financial year from the dropdown list.",
            )
            return

        # Confirm selection
        reply = QMessageBox.question(
            self,
            "Confirm Financial Year Selection",
            f"Are you sure you want to import cases into financial year '{self.selected_fy}'?\n\n"
            f"This will ensure all imported cases are properly linked to the correct financial year "
            f"and can be managed within the system.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.accept()

    def get_selected_financial_year(self):
        """Get the selected financial year data"""
        return {"fy_string": self.selected_fy, "fy_id": self.selected_fy_id}


def show_fy_selection_dialog(determined_fy=None, parent=None):
    """Convenience function to show the FY selection dialog"""
    dialog = FinancialYearSelectionDialog(determined_fy, parent)
    if dialog.exec_():
        return dialog.get_selected_financial_year()
    return None
