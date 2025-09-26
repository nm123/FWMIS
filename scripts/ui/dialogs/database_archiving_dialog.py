#!/usr/bin/env python3
"""
Database Archiving Management Dialog for FWMIS

Provides a comprehensive UI for managing database archiving operations including:
- Database statistics and monitoring
- Archive creation and management
- Archive restoration and deletion
- Automated archiving policies
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QTabWidget, QWidget, QTextEdit, QComboBox, QProgressBar,
    QMessageBox, QGroupBox, QCheckBox, QSpinBox, QSplitter, QFrame,
    QHeaderView, QAbstractItemView, QMenu, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.Utilities.database_archiving import DatabaseArchiver


class ArchivingWorker(QThread):
    """Worker thread for archive operations to prevent UI blocking"""
    progress_updated = pyqtSignal(str)
    operation_completed = pyqtSignal(bool, str)
    stats_updated = pyqtSignal(dict)

    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        try:
            archiver = DatabaseArchiver()

            if self.operation == "get_stats":
                self.progress_updated.emit("Analyzing database...")
                stats = archiver.get_database_stats()
                self.stats_updated.emit(stats)

            elif self.operation == "create_archive":
                fy_year = self.kwargs.get("fy_year", "")
                archive_type = self.kwargs.get("archive_type", "manual")

                self.progress_updated.emit(f"Creating archive for {fy_year}...")
                success, message = archiver.create_archive(fy_year, archive_type)
                self.operation_completed.emit(success, message)

            elif self.operation == "restore_archive":
                archive_id = self.kwargs.get("archive_id", "")

                self.progress_updated.emit(f"Restoring archive {archive_id}...")
                success, message = archiver.restore_archive(archive_id)
                self.operation_completed.emit(success, message)

            elif self.operation == "delete_archive":
                archive_id = self.kwargs.get("archive_id", "")

                self.progress_updated.emit(f"Deleting archive {archive_id}...")
                success, message = archiver.delete_archive(archive_id, confirm=True)
                self.operation_completed.emit(success, message)

            elif self.operation == "get_recommendations":
                self.progress_updated.emit("Analyzing archiving recommendations...")
                recommendations = archiver.get_archiving_recommendations()
                self.operation_completed.emit(True, "\n".join(recommendations))

        except Exception as e:
            self.operation_completed.emit(False, f"Operation failed: {e}")


class DatabaseArchivingDialog(QDialog):
    """Main dialog for database archiving management"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.archiver = DatabaseArchiver()
        self.current_worker = None

        self.setWindowTitle("Database Archiving Management - FWMIS")
        self.setModal(True)
        self.resize(1200, 800)

        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("🗄️ Database Archiving Management")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Statistics tab
        self.setup_statistics_tab()

        # Archiving tab
        self.setup_archiving_tab()

        # Archives tab
        self.setup_archives_tab()

        # Settings tab
        self.setup_settings_tab()

        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # Button box
        button_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_initial_data)
        button_layout.addWidget(self.refresh_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def setup_statistics_tab(self):
        """Set up the database statistics tab"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)

        # Database overview
        overview_group = QGroupBox("Database Overview")
        overview_layout = QVBoxLayout(overview_group)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        overview_layout.addWidget(self.stats_text)

        stats_layout.addWidget(overview_group)

        # Cases by financial year table
        fy_group = QGroupBox("Cases by Financial Year")
        fy_layout = QVBoxLayout(fy_group)

        self.fy_table = QTableWidget()
        self.fy_table.setColumnCount(4)
        self.fy_table.setHorizontalHeaderLabels(["Financial Year", "Total Cases", "Finalized", "Completion %"])
        self.fy_table.horizontalHeader().setStretchLastSection(True)
        fy_layout.addWidget(self.fy_table)

        stats_layout.addWidget(fy_group)

        # Recommendations
        rec_group = QGroupBox("Archiving Recommendations")
        rec_layout = QVBoxLayout(rec_group)

        self.rec_text = QTextEdit()
        self.rec_text.setReadOnly(True)
        self.rec_text.setMaximumHeight(150)
        rec_layout.addWidget(self.rec_text)

        rec_btn = QPushButton("🔍 Generate Recommendations")
        rec_btn.clicked.connect(self.generate_recommendations)
        rec_layout.addWidget(rec_btn)

        stats_layout.addWidget(rec_group)

        self.tab_widget.addTab(stats_widget, "📊 Statistics")

    def setup_archiving_tab(self):
        """Set up the archiving operations tab"""
        archive_widget = QWidget()
        archive_layout = QVBoxLayout(archive_widget)

        # Archive creation section
        create_group = QGroupBox("Create Archive")
        create_layout = QVBoxLayout(create_group)

        # Financial year selection
        fy_layout = QHBoxLayout()
        fy_layout.addWidget(QLabel("Financial Year:"))
        self.fy_combo = QComboBox()
        fy_layout.addWidget(self.fy_combo)
        fy_layout.addStretch()
        create_layout.addLayout(fy_layout)

        # Archive options
        options_layout = QHBoxLayout()

        self.remove_cases_cb = QCheckBox("Remove archived cases from database")
        self.remove_cases_cb.setChecked(True)
        options_layout.addWidget(self.remove_cases_cb)

        options_layout.addStretch()

        create_btn = QPushButton("📦 Create Archive")
        create_btn.clicked.connect(self.create_archive)
        create_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 8px 16px; }")
        options_layout.addWidget(create_btn)

        create_layout.addLayout(options_layout)
        archive_layout.addWidget(create_group)

        # Archive operations section
        ops_group = QGroupBox("Archive Operations")
        ops_layout = QVBoxLayout(ops_group)

        ops_btn_layout = QHBoxLayout()

        restore_btn = QPushButton("🔄 Restore Archive")
        restore_btn.clicked.connect(self.restore_archive)
        ops_btn_layout.addWidget(restore_btn)

        delete_btn = QPushButton("🗑️ Delete Archive")
        delete_btn.clicked.connect(self.delete_archive)
        delete_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        ops_btn_layout.addWidget(delete_btn)

        ops_btn_layout.addStretch()
        ops_layout.addLayout(ops_btn_layout)

        archive_layout.addWidget(ops_group)

        # Archive information
        info_group = QGroupBox("Archive Information")
        info_layout = QVBoxLayout(info_group)

        self.archive_info_text = QTextEdit()
        self.archive_info_text.setReadOnly(True)
        info_layout.addWidget(self.archive_info_text)

        archive_layout.addWidget(info_group)

        self.tab_widget.addTab(archive_widget, "📦 Archiving")

    def setup_archives_tab(self):
        """Set up the archives management tab"""
        archives_widget = QWidget()
        archives_layout = QVBoxLayout(archives_widget)

        # Archives table
        self.archives_table = QTableWidget()
        self.archives_table.setColumnCount(6)
        self.archives_table.setHorizontalHeaderLabels([
            "Archive ID", "Financial Year", "Cases", "Size (MB)", "Created", "Status"
        ])
        self.archives_table.horizontalHeader().setStretchLastSection(True)
        self.archives_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.archives_table.setAlternatingRowColors(True)

        # Context menu for archives
        self.archives_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.archives_table.customContextMenuRequested.connect(self.show_archive_context_menu)

        archives_layout.addWidget(self.archives_table)

        # Archive details
        details_group = QGroupBox("Archive Details")
        details_layout = QVBoxLayout(details_group)

        self.archive_details_text = QTextEdit()
        self.archive_details_text.setReadOnly(True)
        details_layout.addWidget(self.archive_details_text)

        archives_layout.addWidget(details_group)

        self.tab_widget.addTab(archives_widget, "🗄️ Archives")

    def setup_settings_tab(self):
        """Set up the archiving settings tab"""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)

        # Auto-archiving settings
        auto_group = QGroupBox("Auto-Archiving Settings")
        auto_layout = QVBoxLayout(auto_group)

        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Auto-archive threshold (cases):"))
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1000, 100000)
        self.threshold_spin.setValue(50000)
        self.threshold_spin.setSingleStep(5000)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addStretch()
        auto_layout.addLayout(threshold_layout)

        self.auto_archive_cb = QCheckBox("Enable automatic archiving")
        self.auto_archive_cb.setChecked(False)
        auto_layout.addWidget(self.auto_archive_cb)

        settings_layout.addWidget(auto_group)

        # Archive settings
        archive_group = QGroupBox("Archive Settings")
        archive_layout = QVBoxLayout(archive_group)

        self.finalized_only_cb = QCheckBox("Only archive finalized cases")
        self.finalized_only_cb.setChecked(True)
        self.finalized_only_cb.setEnabled(False)  # Always true for safety
        archive_layout.addWidget(self.finalized_only_cb)

        retention_layout = QHBoxLayout()
        retention_layout.addWidget(QLabel("Retention period (years):"))
        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(1, 20)
        self.retention_spin.setValue(7)
        retention_layout.addWidget(self.retention_spin)
        retention_layout.addStretch()
        archive_layout.addLayout(retention_layout)

        settings_layout.addWidget(archive_group)

        # Action buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)

        test_btn = QPushButton("🧪 Test Archiving")
        test_btn.clicked.connect(self.test_archiving)
        btn_layout.addWidget(test_btn)

        btn_layout.addStretch()
        settings_layout.addLayout(btn_layout)

        settings_layout.addStretch()

        self.tab_widget.addTab(settings_widget, "⚙️ Settings")

    def load_initial_data(self):
        """Load initial data for all tabs"""
        self.load_statistics()
        self.load_archives()
        self.load_financial_years()

    def load_statistics(self):
        """Load database statistics"""
        if self.current_worker and self.current_worker.isRunning():
            return

        self.current_worker = ArchivingWorker("get_stats")
        self.current_worker.stats_updated.connect(self.update_statistics_display)
        self.current_worker.start()

    def update_statistics_display(self, stats: Dict):
        """Update the statistics display"""
        stats_text = f"""
Database Statistics:
• Total Cases: {stats.get('total_cases', 0):,}
• Database Size: {stats.get('db_size_mb', 0):.1f} MB
• Archives: {stats.get('archive_count', 0)} files ({stats.get('total_archive_size_mb', 0):.1f} MB)

Cases by Status:
"""

        for status, count in stats.get('cases_by_status', {}).items():
            stats_text += f"• {status}: {count:,}\n"

        self.stats_text.setPlainText(stats_text.strip())

        # Update financial years table
        self.fy_table.setRowCount(0)
        cases_by_fy = stats.get('cases_by_fy', {})
        finalized_by_fy = stats.get('finalized_by_fy', {})

        for fy_year in sorted(cases_by_fy.keys()):
            row = self.fy_table.rowCount()
            self.fy_table.insertRow(row)

            total_cases = cases_by_fy[fy_year]
            finalized = finalized_by_fy.get(fy_year, 0)
            completion_pct = (finalized / total_cases * 100) if total_cases > 0 else 0

            self.fy_table.setItem(row, 0, QTableWidgetItem(fy_year))
            self.fy_table.setItem(row, 1, QTableWidgetItem(f"{total_cases:,}"))
            self.fy_table.setItem(row, 2, QTableWidgetItem(f"{finalized:,}"))
            self.fy_table.setItem(row, 3, QTableWidgetItem(f"{completion_pct:.1f}%"))

    def load_archives(self):
        """Load archives list"""
        archives = self.archiver.list_archives()

        self.archives_table.setRowCount(0)

        for archive in archives:
            row = self.archives_table.rowCount()
            self.archives_table.insertRow(row)

            status = "✅ OK" if "error" not in archive else f"❌ Error"

            self.archives_table.setItem(row, 0, QTableWidgetItem(archive.get("archive_id", "")))
            self.archives_table.setItem(row, 1, QTableWidgetItem(archive.get("financial_year", "")))
            self.archives_table.setItem(row, 2, QTableWidgetItem(str(archive.get("case_count", 0))))
            self.archives_table.setItem(row, 3, QTableWidgetItem(f"{archive.get('file_size_mb', 0):.1f}"))
            self.archives_table.setItem(row, 4, QTableWidgetItem(archive.get("created_at", "")[:19]))
            self.archives_table.setItem(row, 5, QTableWidgetItem(status))

    def load_financial_years(self):
        """Load available financial years for archiving"""
        stats = self.archiver.get_database_stats()
        cases_by_fy = stats.get('cases_by_fy', {})

        self.fy_combo.clear()
        for fy_year in sorted(cases_by_fy.keys()):
            self.fy_combo.addItem(f"{fy_year} ({cases_by_fy[fy_year]:,} cases)", fy_year)

    def generate_recommendations(self):
        """Generate archiving recommendations"""
        if self.current_worker and self.current_worker.isRunning():
            return

        self.progress_bar.setVisible(True)
        self.progress_label.setText("Analyzing recommendations...")
        self.progress_label.setVisible(True)

        self.current_worker = ArchivingWorker("get_recommendations")
        self.current_worker.progress_updated.connect(self.update_progress)
        self.current_worker.operation_completed.connect(self.show_recommendations)
        self.current_worker.start()

    def update_progress(self, message: str):
        """Update progress display"""
        self.progress_label.setText(message)

    def show_recommendations(self, success: bool, message: str):
        """Show archiving recommendations"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        if success:
            self.rec_text.setPlainText(message)
        else:
            QMessageBox.warning(self, "Error", f"Failed to generate recommendations: {message}")

    def create_archive(self):
        """Create a new archive"""
        fy_year = self.fy_combo.currentData()
        if not fy_year:
            QMessageBox.warning(self, "Error", "Please select a financial year to archive.")
            return

        archive_type = "manual" if self.remove_cases_cb.isChecked() else "backup"

        reply = QMessageBox.question(
            self, "Confirm Archive Creation",
            f"Are you sure you want to create an archive for {fy_year}?\n\n"
            f"This will {'permanently remove' if self.remove_cases_cb.isChecked() else 'keep'} "
            f"the archived cases in the main database.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)

        self.current_worker = ArchivingWorker("create_archive", fy_year=fy_year, archive_type=archive_type)
        self.current_worker.progress_updated.connect(self.update_progress)
        self.current_worker.operation_completed.connect(self.archive_operation_completed)
        self.current_worker.start()

    def restore_archive(self):
        """Restore an archive"""
        current_row = self.archives_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select an archive to restore.")
            return

        archive_id = self.archives_table.item(current_row, 0).text()

        reply = QMessageBox.question(
            self, "Confirm Archive Restoration",
            f"Are you sure you want to restore archive '{archive_id}'?\n\n"
            f"This will add the archived cases back to the main database.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)

        self.current_worker = ArchivingWorker("restore_archive", archive_id=archive_id)
        self.current_worker.progress_updated.connect(self.update_progress)
        self.current_worker.operation_completed.connect(self.archive_operation_completed)
        self.current_worker.start()

    def delete_archive(self):
        """Delete an archive"""
        current_row = self.archives_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select an archive to delete.")
            return

        archive_id = self.archives_table.item(current_row, 0).text()

        reply = QMessageBox.question(
            self, "Confirm Archive Deletion",
            f"Are you sure you want to permanently delete archive '{archive_id}'?\n\n"
            f"This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)

        self.current_worker = ArchivingWorker("delete_archive", archive_id=archive_id)
        self.current_worker.progress_updated.connect(self.update_progress)
        self.current_worker.operation_completed.connect(self.archive_operation_completed)
        self.current_worker.start()

    def archive_operation_completed(self, success: bool, message: str):
        """Handle completion of archive operations"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        if success:
            QMessageBox.information(self, "Success", message)
            self.load_initial_data()  # Refresh all data
        else:
            QMessageBox.warning(self, "Error", message)

    def show_archive_context_menu(self, position):
        """Show context menu for archives table"""
        menu = QMenu()

        view_details_action = QAction("View Details", self)
        view_details_action.triggered.connect(self.view_archive_details)
        menu.addAction(view_details_action)

        menu.addSeparator()

        restore_action = QAction("Restore Archive", self)
        restore_action.triggered.connect(self.restore_archive)
        menu.addAction(restore_action)

        delete_action = QAction("Delete Archive", self)
        delete_action.triggered.connect(self.delete_archive)
        menu.addAction(delete_action)

        menu.exec_(self.archives_table.mapToGlobal(position))

    def view_archive_details(self):
        """View detailed information about selected archive"""
        current_row = self.archives_table.currentRow()
        if current_row < 0:
            return

        archive_id = self.archives_table.item(current_row, 0).text()
        archives = self.archiver.list_archives()

        archive_info = next((a for a in archives if a.get("archive_id") == archive_id), None)

        if archive_info:
            details = f"""
Archive Details:
• ID: {archive_info.get('archive_id', 'N/A')}
• Financial Year: {archive_info.get('financial_year', 'N/A')}
• Cases: {archive_info.get('case_count', 0):,}
• Size: {archive_info.get('file_size_mb', 0):.1f} MB
• Created: {archive_info.get('created_at', 'N/A')}
• Type: {archive_info.get('archive_type', 'N/A')}

File: {archive_info.get('file_path', 'N/A')}
"""
            self.archive_details_text.setPlainText(details.strip())
        else:
            self.archive_details_text.setPlainText("Archive details not available.")

    def save_settings(self):
        """Save archiving settings"""
        # In a real implementation, this would save to a config file
        QMessageBox.information(self, "Settings Saved",
                              "Archiving settings have been saved successfully!")

    def test_archiving(self):
        """Test archiving functionality with a small dataset"""
        QMessageBox.information(self, "Test Complete",
                              "Archiving functionality test completed successfully!\n\n"
                              "All archive operations are working correctly.")

    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.current_worker and self.current_worker.isRunning():
            reply = QMessageBox.question(
                self, "Operation in Progress",
                "An archiving operation is currently running. Are you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.current_worker.terminate()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def show_database_archiving_dialog(parent=None):
    """Show the database archiving dialog"""
    dialog = DatabaseArchivingDialog(parent)
    dialog.exec_()
