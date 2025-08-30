from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QPushButton,
    QMessageBox,
    QFileDialog,
)
from PyQt5.QtCore import Qt
from Utilities.utils import load_categories, load_responsibilities, load_cases, create_year_folder, get_subtree_resp_ids, DB_PATH
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os

class ReportManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Reports")
        self.setFixedSize(600, 400)
        self.categories = load_categories()
        self.responsibilities = load_responsibilities()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(["Cases by Category", "Cases by Responsibility", "Cases by Status"])
        form_layout.addRow("Report Type:", self.report_type_combo)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.addItems([c["name"] for c in self.categories])
        form_layout.addRow("Category:", self.category_combo)
        
        self.responsibility_combo = QComboBox()
        self.responsibility_combo.addItem("All Responsibilities")
        self.responsibility_combo.addItems([r["name"] for r in self.responsibilities])
        form_layout.addRow("Responsibility:", self.responsibility_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All Statuses", "Draft", "Awaiting Evidence", "Confirmed"])
        form_layout.addRow("Status:", self.status_combo)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate Report")
        self.generate_button.clicked.connect(self.generate_report)
        button_layout.addWidget(self.generate_button)
        layout.addLayout(button_layout)

    def generate_report(self):
        try:
            report_type = self.report_type_combo.currentText()
            category = self.category_combo.currentText()
            responsibility = self.responsibility_combo.currentText()
            status = self.status_combo.currentText()
            
            cases = load_cases()
            filtered_cases = cases
            
            if category != "All Categories":
                filtered_cases = [c for c in filtered_cases if c["category"] == category]
            if responsibility != "All Responsibilities":
                resp = next((r for r in self.responsibilities if r["name"] == responsibility), None)
                if resp:
                    subtree_ids = get_subtree_resp_ids(resp["id"], self.responsibilities)
                    filtered_cases = [c for c in filtered_cases if c["responsibility_id"] in subtree_ids]
            if status != "All Statuses":
                filtered_cases = [c for c in filtered_cases if c["status"] == status]
            
            if not filtered_cases:
                QMessageBox.information(self, "No Data", "No cases match the selected criteria.")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "", "PDF Files (*.pdf)")
            if not file_path:
                return
            
            self.create_pdf_report(report_type, filtered_cases, file_path)
            QMessageBox.information(self, "Success", f"Report saved to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")

    def create_pdf_report(self, report_type, cases, file_path):
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        title = Paragraph(f"Report: {report_type}", styles["Title"])
        elements.append(title)
        
        data = [["ID", "Transaction No", "BAS Payment No", "Persal No", "Amount", "Category", "Responsibility", "Status"]]
        for case in cases:
            responsibility = next((r["name"] for r in self.responsibilities if r["id"] == case["responsibility_id"]), "Unknown")
            data.append([
                case["id"],
                case["transaction_no"],
                case["bas_payment_no"],
                case["persal_no"],
                f"R {case['amount']:.2f}",
                case["category"],
                responsibility,
                case["status"]
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        
        doc.build(elements)