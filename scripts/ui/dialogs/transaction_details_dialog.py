from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class TransactionDetailsDialog(QDialog):
    """Dialog to show detailed transaction information"""

    def __init__(self, transaction, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transaction Details")
        self.setFixedSize(600, 400)

        self.transaction = transaction
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Transaction details
        form_layout = QFormLayout()

        form_layout.addRow(
            "Responsibility:", QLabel(self.transaction["responsibility"])
        )
        form_layout.addRow("Item:", QLabel(self.transaction["item"]))
        form_layout.addRow("Type:", QLabel(self.transaction["type"]))
        form_layout.addRow("Transaction Number:", QLabel(self.transaction["number"]))

        try:
            # Try relative imports first (when used as part of a package)
            from ...Utilities.utils import format_currency_amount
        except ImportError:
            # Fall back to absolute imports (when run directly)
            from scripts.Utilities.utils import format_currency_amount
        amount = self.transaction["amount"]
        amount_str = format_currency_amount(amount)
        if self.transaction["is_credit"]:
            amount_str += " (Credit)"
        else:
            amount_str += " (Debit)"
        form_layout.addRow("Amount:", QLabel(amount_str))

        form_layout.addRow(
            "Date:", QLabel(self.transaction["date"].strftime("%Y-%m-%d"))
        )
        form_layout.addRow("User ID:", QLabel(self.transaction["user_id"]))

        layout.addLayout(form_layout)

        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        desc_edit = QTextEdit()
        desc_edit.setPlainText(self.transaction["description"])
        desc_edit.setReadOnly(True)
        desc_edit.setMaximumHeight(80)
        desc_layout.addWidget(desc_edit)
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
