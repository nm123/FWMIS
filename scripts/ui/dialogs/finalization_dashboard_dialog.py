"""
Finalization Dashboard Dialog
Shows case finalization status, aging reports, bottlenecks, and compliance metrics.
"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QTableWidget, QTableWidgetItem, QTabWidget, QWidget,
                             QComboBox, QPushButton, QProgressBar, QSplitter)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_all_financial_years


class FinalizationDashboardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Finalization Dashboard")
        self.setMinimumSize(1200, 800)

        self.setup_ui()
        self.load_data()
        self.update_dashboard()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Case Finalization Dashboard")
        header_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Financial Year:"))

        self.fy_filter_combo = QComboBox()
        self.fy_filter_combo.setFixedWidth(200)
        self.load_fy_filter()
        self.fy_filter_combo.currentTextChanged.connect(self.update_dashboard)
        filter_layout.addWidget(self.fy_filter_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Create tab widget for different views
        self.tab_widget = QTabWidget()

        # Overview Tab
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        self.setup_overview_tab(overview_layout)
        self.tab_widget.addTab(overview_tab, "Overview")

        # Aging Analysis Tab
        aging_tab = QWidget()
        aging_layout = QVBoxLayout(aging_tab)
        self.setup_aging_tab(aging_layout)
        self.tab_widget.addTab(aging_tab, "Aging Analysis")

        # Compliance Tab
        compliance_tab = QWidget()
        compliance_layout = QVBoxLayout(compliance_tab)
        self.setup_compliance_tab(compliance_layout)
        self.tab_widget.addTab(compliance_tab, "Compliance Metrics")

        layout.addWidget(self.tab_widget)

        # Bottom buttons
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.update_dashboard)
        button_layout.addWidget(refresh_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def setup_overview_tab(self, layout):
        """Setup the overview tab with summary statistics"""
        # Status Summary
        status_group = QGroupBox("Case Status Summary")
        status_layout = QVBoxLayout(status_group)

        self.status_table = QTableWidget()
        self.status_table.setColumnCount(4)
        self.status_table.setHorizontalHeaderLabels(["Status", "Count", "Percentage", "Total Amount"])
        self.status_table.setAlternatingRowColors(True)
        status_layout.addWidget(self.status_table)

        layout.addWidget(status_group)

        # Key Metrics Row
        metrics_layout = QHBoxLayout()

        # Finalization Rate
        finalization_group = QGroupBox("Finalization Rate")
        finalization_layout = QVBoxLayout(finalization_group)
        self.finalization_rate_label = QLabel("--%")
        self.finalization_rate_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.finalization_rate_label.setAlignment(Qt.AlignCenter)
        finalization_layout.addWidget(self.finalization_rate_label)
        self.finalization_progress = QProgressBar()
        finalization_layout.addWidget(self.finalization_progress)
        metrics_layout.addWidget(finalization_group)

        # Average Age
        age_group = QGroupBox("Average Case Age (Days)")
        age_layout = QVBoxLayout(age_group)
        self.avg_age_label = QLabel("--")
        self.avg_age_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.avg_age_label.setAlignment(Qt.AlignCenter)
        age_layout.addWidget(self.avg_age_label)
        metrics_layout.addWidget(age_group)

        # Bottlenecks
        bottleneck_group = QGroupBox("Bottlenecks")
        bottleneck_layout = QVBoxLayout(bottleneck_group)
        self.bottleneck_table = QTableWidget()
        self.bottleneck_table.setColumnCount(2)
        self.bottleneck_table.setHorizontalHeaderLabels(["Status", "Cases Stuck"])
        bottleneck_layout.addWidget(self.bottleneck_table)
        metrics_layout.addWidget(bottleneck_group)

        layout.addLayout(metrics_layout)

    def setup_aging_tab(self, layout):
        """Setup the aging analysis tab"""
        # Splitter for side-by-side view
        splitter = QSplitter(Qt.Horizontal)

        # Aging Buckets
        aging_group = QGroupBox("Case Aging Distribution")
        aging_layout = QVBoxLayout(aging_group)

        self.aging_table = QTableWidget()
        self.aging_table.setColumnCount(4)
        self.aging_table.setHorizontalHeaderLabels(["Age Range", "Count", "Percentage", "Status"])
        self.aging_table.setAlternatingRowColors(True)
        aging_layout.addWidget(self.aging_table)

        splitter.addWidget(aging_group)

        # Detailed Aging by Status
        detailed_group = QGroupBox("Aging by Status")
        detailed_layout = QVBoxLayout(detailed_group)

        self.detailed_aging_table = QTableWidget()
        self.detailed_aging_table.setColumnCount(5)
        self.detailed_aging_table.setHorizontalHeaderLabels(["Status", "0-30 days", "31-60 days", "61-90 days", "90+ days"])
        self.detailed_aging_table.setAlternatingRowColors(True)
        detailed_layout.addWidget(self.detailed_aging_table)

        splitter.addWidget(detailed_group)

        layout.addWidget(splitter)

    def setup_compliance_tab(self, layout):
        """Setup the compliance metrics tab"""
        # LC Committee Compliance
        lc_group = QGroupBox("LC Committee Recommendation Compliance (30-day target)")
        lc_layout = QVBoxLayout(lc_group)

        self.lc_compliance_table = QTableWidget()
        self.lc_compliance_table.setColumnCount(4)
        self.lc_compliance_table.setHorizontalHeaderLabels(["Metric", "Count", "Percentage", "Status"])
        self.lc_compliance_table.setAlternatingRowColors(True)
        lc_layout.addWidget(self.lc_compliance_table)

        layout.addWidget(lc_group)

        # Overall Compliance Metrics
        compliance_group = QGroupBox("Overall Compliance Metrics")
        compliance_layout = QVBoxLayout(compliance_group)

        self.compliance_table = QTableWidget()
        self.compliance_table.setColumnCount(3)
        self.compliance_table.setHorizontalHeaderLabels(["Metric", "Value", "Target"])
        self.compliance_table.setAlternatingRowColors(True)
        compliance_layout.addWidget(self.compliance_table)

        layout.addWidget(compliance_group)

    def load_fy_filter(self):
        """Load financial years into the filter combo"""
        try:
            financial_years = get_all_financial_years()

            self.fy_filter_combo.clear()
            self.fy_filter_combo.addItem("All Years", None)

            for fy_id, fy_string, is_open in financial_years:
                display_text = f"{fy_string}"
                if is_open:
                    display_text += " (Current)"
                self.fy_filter_combo.addItem(display_text, fy_id)

            # Default to current FY
            current_fy = datetime.now().year
            for i in range(self.fy_filter_combo.count()):
                if self.fy_filter_combo.itemData(i) and str(current_fy) in self.fy_filter_combo.itemText(i):
                    self.fy_filter_combo.setCurrentIndex(i)
                    break

        except Exception as e:
            print(f"Error loading FY filter: {e}")
            self.fy_filter_combo.addItem("All Years", None)

    def load_data(self):
        """Load dashboard data"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()

                # Get selected FY filter - handle case where combo might not be initialized
                selected_fy_id = None
                if hasattr(self, 'fy_filter_combo') and self.fy_filter_combo.count() > 0:
                    selected_fy_id = self.fy_filter_combo.currentData()

                # Build FY filter condition
                fy_condition = ""
                fy_params = []
                if selected_fy_id is not None:
                    fy_condition = " AND c.fy_id = ?"
                    fy_params = [selected_fy_id]

                # Query case data with aging information
                query = f"""
                    SELECT
                        c.id,
                        c.transaction_no,
                        c.assessment_status,
                        c.lc_status,
                        c.is_finalized,
                        c.date_reported,
                        c.lc_committee_date,
                        c.finalized_date,
                        c.amount,
                        c.fy_id,
                        CASE
                            WHEN c.is_finalized = 1 THEN 'Finalized'
                            WHEN c.lc_status = 'Write-Off Recommended' THEN 'Write-Off Recommended'
                            WHEN c.lc_status = 'Recovery in Progress' THEN 'Recovery in Progress'
                            WHEN c.lc_status = 'Recovered' THEN 'Recovered'
                            WHEN c.lc_status = 'Awaiting LC determination' THEN 'Awaiting LC determination'
                            WHEN c.assessment_status IN ('Valid', 'Confirmed') THEN 'Assessment Complete'
                            WHEN c.assessment_status = 'Alleged' THEN 'Alleged'
                            ELSE 'Other'
                        END as status_category,
                        CASE
                            WHEN c.is_finalized = 1 THEN
                                julianday(c.finalized_date) - julianday(c.date_reported)
                            WHEN c.lc_status IN ('Recovery in Progress', 'Recovered', 'Write-Off Recommended') THEN
                                CASE
                                    WHEN c.lc_committee_date IS NOT NULL THEN
                                        julianday('now') - julianday(c.lc_committee_date)
                                    ELSE
                                        julianday('now') - julianday(c.date_reported)
                                END
                            ELSE
                                julianday('now') - julianday(c.date_reported)
                        END as days_since_reported
                    FROM cases c
                    WHERE 1=1 {fy_condition}
                    ORDER BY c.date_reported DESC
                """

                cursor.execute(query, fy_params)
                self.cases_data = cursor.fetchall()

                print(f"Loaded {len(self.cases_data)} cases for dashboard")

        except Exception as e:
            print(f"Error loading dashboard data: {e}")
            self.cases_data = []

    def update_dashboard(self):
        """Update all dashboard components"""
        self.load_data()

        # Update each tab
        self.update_overview_tab()
        self.update_aging_tab()
        self.update_compliance_tab()

    def update_overview_tab(self):
        """Update the overview tab with current data"""
        if not self.cases_data:
            return

        # Calculate status summary
        status_counts = defaultdict(int)
        status_amounts = defaultdict(float)
        total_cases = len(self.cases_data)
        total_amount = 0.0

        for case in self.cases_data:
            status = case[9]  # status_category
            # Safely convert amount to float
            try:
                amount = float(case[7]) if case[7] is not None else 0.0
            except (ValueError, TypeError):
                amount = 0.0
            status_counts[status] += 1
            status_amounts[status] += amount
            total_amount += amount

        # Update status table
        self.status_table.setRowCount(len(status_counts))

        row = 0
        for status, count in status_counts.items():
            self.status_table.setItem(row, 0, QTableWidgetItem(status))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(count)))
            percentage = (count / total_cases * 100) if total_cases > 0 else 0
            self.status_table.setItem(row, 2, QTableWidgetItem(f"{percentage:.1f}%"))
            self.status_table.setItem(row, 3, QTableWidgetItem(f"R {status_amounts[status]:,.2f}"))
            row += 1

        # Calculate finalization rate
        finalized_count = status_counts.get('Finalized', 0) + status_counts.get('Recovered', 0) + status_counts.get('Written Off', 0)
        finalization_rate = (finalized_count / total_cases * 100) if total_cases > 0 else 0

        self.finalization_rate_label.setText(f"{finalization_rate:.1f}%")
        self.finalization_progress.setValue(int(finalization_rate))

        # Calculate average age
        if self.cases_data:
            total_days = 0.0
            valid_cases = 0
            for case in self.cases_data:
                try:
                    days = float(case[10]) if case[10] is not None else 0.0
                    total_days += days
                    valid_cases += 1
                except (ValueError, TypeError):
                    continue
            avg_age = total_days / valid_cases if valid_cases > 0 else 0.0
            self.avg_age_label.setText(f"{avg_age:.0f}")
        else:
            self.avg_age_label.setText("0")

        # Identify bottlenecks (statuses with cases older than 90 days)
        bottleneck_data = []
        for status, count in status_counts.items():
            old_cases = 0
            for case in self.cases_data:
                if case[9] == status:
                    try:
                        days = float(case[10]) if case[10] is not None else 0.0
                        if days > 90:
                            old_cases += 1
                    except (ValueError, TypeError):
                        continue
            if old_cases > 0:
                bottleneck_data.append((status, old_cases))

        self.bottleneck_table.setRowCount(len(bottleneck_data))
        for row, (status, count) in enumerate(bottleneck_data):
            self.bottleneck_table.setItem(row, 0, QTableWidgetItem(status))
            self.bottleneck_table.setItem(row, 1, QTableWidgetItem(str(count)))

    def update_aging_tab(self):
        """Update the aging analysis tab"""
        if not self.cases_data:
            return

        # Aging buckets
        aging_buckets = {
            '0-30 days': 0,
            '31-60 days': 0,
            '61-90 days': 0,
            '91-180 days': 0,
            '181+ days': 0
        }

        # Count cases in each bucket
        for case in self.cases_data:
            # Safely convert days to float
            try:
                days = float(case[10]) if case[10] is not None else 0.0
            except (ValueError, TypeError):
                days = 0.0
            if days <= 30:
                aging_buckets['0-30 days'] += 1
            elif days <= 60:
                aging_buckets['31-60 days'] += 1
            elif days <= 90:
                aging_buckets['61-90 days'] += 1
            elif days <= 180:
                aging_buckets['91-180 days'] += 1
            else:
                aging_buckets['181+ days'] += 1

        # Update aging table
        self.aging_table.setRowCount(len(aging_buckets))
        total_cases = len(self.cases_data)

        row = 0
        for bucket, count in aging_buckets.items():
            percentage = (count / total_cases * 100) if total_cases > 0 else 0
            self.aging_table.setItem(row, 0, QTableWidgetItem(bucket))
            self.aging_table.setItem(row, 1, QTableWidgetItem(str(count)))
            self.aging_table.setItem(row, 2, QTableWidgetItem(f"{percentage:.1f}%"))

            # Color coding
            if '181+' in bucket:
                self.aging_table.item(row, 0).setBackground(QColor('#fed7d7'))  # Red
            elif '91-180' in bucket:
                self.aging_table.item(row, 0).setBackground(QColor('#fef5e7'))  # Yellow

            row += 1

        # Detailed aging by status
        status_aging = defaultdict(lambda: {'0-30': 0, '31-60': 0, '61-90': 0, '90+': 0})

        for case in self.cases_data:
            status = case[9]
            # Safely convert days to float
            try:
                days = float(case[10]) if case[10] is not None else 0.0
            except (ValueError, TypeError):
                days = 0.0
            if days <= 30:
                status_aging[status]['0-30'] += 1
            elif days <= 60:
                status_aging[status]['31-60'] += 1
            elif days <= 90:
                status_aging[status]['61-90'] += 1
            else:
                status_aging[status]['90+'] += 1

        self.detailed_aging_table.setRowCount(len(status_aging))
        row = 0
        for status, buckets in status_aging.items():
            self.detailed_aging_table.setItem(row, 0, QTableWidgetItem(status))
            self.detailed_aging_table.setItem(row, 1, QTableWidgetItem(str(buckets['0-30'])))
            self.detailed_aging_table.setItem(row, 2, QTableWidgetItem(str(buckets['31-60'])))
            self.detailed_aging_table.setItem(row, 3, QTableWidgetItem(str(buckets['61-90'])))
            self.detailed_aging_table.setItem(row, 4, QTableWidgetItem(str(buckets['90+'])))

            # Highlight rows with cases in 90+ days
            if buckets['90+'] > 0:
                for col in range(5):
                    self.detailed_aging_table.item(row, col).setBackground(QColor('#fed7d7'))

            row += 1

    def update_compliance_tab(self):
        """Update the compliance metrics tab"""
        if not self.cases_data:
            return

        # LC Committee compliance (30-day target from date reported)
        lc_cases = [case for case in self.cases_data if case[2] in ('Valid', 'Confirmed')]  # Cases that need LC determination
        total_lc_cases = len(lc_cases)

        compliant_cases = 0
        non_compliant_cases = 0

        for case in lc_cases:
            date_reported = case[5]
            lc_committee_date = case[6]

            try:
                if date_reported and lc_committee_date:
                    reported_date = datetime.strptime(str(date_reported), '%Y-%m-%d').date()
                    committee_date = datetime.strptime(str(lc_committee_date), '%Y-%m-%d').date()

                    days_to_decision = (committee_date - reported_date).days
                    if days_to_decision <= 30:
                        compliant_cases += 1
                    else:
                        non_compliant_cases += 1
                elif date_reported:
                    # No committee date set yet, check if it's past 30 days
                    reported_date = datetime.strptime(str(date_reported), '%Y-%m-%d').date()
                    days_since_reported = (datetime.now().date() - reported_date).days
                    if days_since_reported > 30:
                        non_compliant_cases += 1
            except (ValueError, TypeError):
                # Skip this case if date parsing fails
                continue

        compliance_rate = (compliant_cases / total_lc_cases * 100) if total_lc_cases > 0 else 0

        # Update LC compliance table
        self.lc_compliance_table.setRowCount(3)
        self.lc_compliance_table.setItem(0, 0, QTableWidgetItem("Total Cases Requiring LC Decision"))
        self.lc_compliance_table.setItem(0, 1, QTableWidgetItem(str(total_lc_cases)))
        self.lc_compliance_table.setItem(0, 2, QTableWidgetItem("100%"))
        self.lc_compliance_table.setItem(0, 3, QTableWidgetItem("Target"))

        self.lc_compliance_table.setItem(1, 0, QTableWidgetItem("Decided Within 30 Days"))
        self.lc_compliance_table.setItem(1, 1, QTableWidgetItem(str(compliant_cases)))
        self.lc_compliance_table.setItem(1, 2, QTableWidgetItem(f"{compliance_rate:.1f}%"))
        self.lc_compliance_table.setItem(1, 3, QTableWidgetItem("Compliant" if compliance_rate >= 95 else "Needs Attention"))

        self.lc_compliance_table.setItem(2, 0, QTableWidgetItem("Decided After 30 Days"))
        self.lc_compliance_table.setItem(2, 1, QTableWidgetItem(str(non_compliant_cases)))
        non_compliance_rate = (non_compliant_cases / total_lc_cases * 100) if total_lc_cases > 0 else 0
        self.lc_compliance_table.setItem(2, 2, QTableWidgetItem(f"{non_compliance_rate:.1f}%"))
        self.lc_compliance_table.setItem(2, 3, QTableWidgetItem("Non-Compliant" if non_compliance_rate > 5 else "Acceptable"))

        # Color coding
        for row in range(3):
            status_item = self.lc_compliance_table.item(row, 3)
            if status_item:
                if "Compliant" in status_item.text() or "Target" in status_item.text():
                    status_item.setBackground(QColor('#c6f6d5'))  # Green
                elif "Needs Attention" in status_item.text():
                    status_item.setBackground(QColor('#fef5e7'))  # Yellow
                elif "Non-Compliant" in status_item.text():
                    status_item.setBackground(QColor('#fed7d7'))  # Red

        # Overall compliance metrics
        total_cases = len(self.cases_data)
        finalized_cases = sum(1 for case in self.cases_data if case[4])  # is_finalized
        finalization_rate = (finalized_cases / total_cases * 100) if total_cases > 0 else 0

        self.compliance_table.setRowCount(4)
        self.compliance_table.setItem(0, 0, QTableWidgetItem("Overall Finalization Rate"))
        self.compliance_table.setItem(0, 1, QTableWidgetItem(f"{finalization_rate:.1f}%"))
        self.compliance_table.setItem(0, 2, QTableWidgetItem("95%"))

        self.compliance_table.setItem(1, 0, QTableWidgetItem("LC Committee Compliance"))
        self.compliance_table.setItem(1, 1, QTableWidgetItem(f"{compliance_rate:.1f}%"))
        self.compliance_table.setItem(1, 2, QTableWidgetItem("95%"))

        # Cases stuck in each status for >90 days
        stuck_cases = 0
        for case in self.cases_data:
            try:
                days = float(case[10]) if case[10] is not None else 0.0
                if days > 90:
                    stuck_cases += 1
            except (ValueError, TypeError):
                continue
        stuck_rate = (stuck_cases / total_cases * 100) if total_cases > 0 else 0

        self.compliance_table.setItem(2, 0, QTableWidgetItem("Cases Stuck >90 Days"))
        self.compliance_table.setItem(2, 1, QTableWidgetItem(f"{stuck_cases} ({stuck_rate:.1f}%)"))
        self.compliance_table.setItem(2, 2, QTableWidgetItem("<5%"))

        # Average resolution time for finalized cases
        finalized_ages = []
        for case in self.cases_data:
            if case[4]:  # is_finalized
                try:
                    age = float(case[10]) if case[10] is not None else 0.0
                    finalized_ages.append(age)
                except (ValueError, TypeError):
                    continue
        avg_resolution_time = sum(finalized_ages) / len(finalized_ages) if finalized_ages else 0

        self.compliance_table.setItem(3, 0, QTableWidgetItem("Average Resolution Time"))
        self.compliance_table.setItem(3, 1, QTableWidgetItem(f"{avg_resolution_time:.0f} days"))
        self.compliance_table.setItem(3, 2, QTableWidgetItem("<60 days"))
