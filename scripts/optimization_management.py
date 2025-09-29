"""
Optimization Management Dialog for FWMIS.
Allows users to enable/disable performance optimizations.
"""

import logging

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from scripts.Utilities.optimization_manager import (
    get_optimization_manager,
    get_optimization_summary,
)
from scripts.Utilities.performance_profiler import memory_profiler, performance_profiler

logger = logging.getLogger(__name__)


class OptimizationManagementDialog(QDialog):
    """Dialog for managing FWMIS performance optimizations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Performance Optimization Management")
        self.setModal(True)
        self.resize(600, 500)

        # Get optimization manager
        self.optimization_manager = get_optimization_manager()

        self.setup_ui()
        self.load_current_settings()
        self.start_performance_monitoring()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("FWMIS Performance Optimization Management")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """
        )
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Configure performance optimizations for your system. "
            "Enable optimizations for better performance with large datasets, "
            "or disable them for maximum compatibility."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(
            """
            QLabel {
                color: #7f8c8d;
                margin-bottom: 20px;
            }
        """
        )
        layout.addWidget(desc_label)

        # Optimization settings group
        settings_group = QGroupBox("Optimization Settings")
        settings_layout = QFormLayout(settings_group)

        # Create checkboxes for each optimization
        self.optimization_checkboxes = {}
        optimization_descriptions = {
            "memory_efficient_imports": "Memory Efficient Imports",
            "streaming_excel_exports": "Streaming Excel Exports",
            "batch_database_operations": "Batch Database Operations",
            "performance_monitoring": "Performance Monitoring",
            "database_indexes": "Database Indexes",
            "adaptive_chunk_sizing": "Adaptive Chunk Sizing",
        }

        for key, description in optimization_descriptions.items():
            checkbox = QCheckBox(description)
            checkbox.setToolTip(self._get_optimization_tooltip(key))
            self.optimization_checkboxes[key] = checkbox
            settings_layout.addRow(checkbox)

        layout.addWidget(settings_group)

        # System Resources group
        resources_group = QGroupBox("System Resources")
        resources_layout = QFormLayout(resources_group)

        # Memory usage display
        self.memory_label = QLabel("Checking...")
        self.memory_label.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
                background-color: #e9ecef;
            }
        """
        )
        resources_layout.addRow("Memory Usage:", self.memory_label)

        # CPU usage display
        self.cpu_label = QLabel("Checking...")
        self.cpu_label.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
                background-color: #e9ecef;
            }
        """
        )
        resources_layout.addRow("CPU Usage:", self.cpu_label)

        layout.addWidget(resources_group)

        # Performance monitoring group
        perf_group = QGroupBox("Performance Status")
        perf_layout = QVBoxLayout(perf_group)

        # Performance status display
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """
        )
        perf_layout.addWidget(self.status_text)

        # Refresh button
        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.clicked.connect(self.refresh_performance_status)
        perf_layout.addWidget(refresh_btn)

        layout.addWidget(perf_group)

        # Action buttons
        button_layout = QHBoxLayout()

        # Quick action buttons
        enable_all_btn = QPushButton("Enable All")
        enable_all_btn.clicked.connect(self.enable_all_optimizations)
        enable_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """
        )

        disable_all_btn = QPushButton("Disable All")
        disable_all_btn.clicked.connect(self.disable_all_optimizations)
        disable_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """
        )

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        reset_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )

        button_layout.addWidget(enable_all_btn)
        button_layout.addWidget(disable_all_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Standard dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _get_optimization_tooltip(self, optimization_key):
        """Get tooltip text for optimization."""
        tooltips = {
            "memory_efficient_imports": "Use streaming processing for large CSV/BAS files. Reduces memory usage by 80%+.",
            "streaming_excel_exports": "Export large datasets to Excel using memory-efficient streaming. Prevents memory issues.",
            "batch_database_operations": "Use batch inserts and transactions for better database performance.",
            "performance_monitoring": "Monitor memory usage and performance metrics in real-time.",
            "database_indexes": "Create performance indexes on frequently queried columns.",
            "adaptive_chunk_sizing": "Automatically adjust processing chunk size based on available memory.",
        }
        return tooltips.get(optimization_key, "Performance optimization setting.")

    def load_current_settings(self):
        """Load current optimization settings."""
        status = self.optimization_manager.get_optimization_status()

        for key, checkbox in self.optimization_checkboxes.items():
            enabled = status["config"].get(key, False)
            checkbox.setChecked(enabled)

        self.refresh_performance_status()

    def enable_all_optimizations(self):
        """Enable all optimizations."""
        for checkbox in self.optimization_checkboxes.values():
            checkbox.setChecked(True)

        QMessageBox.information(
            self,
            "Optimizations Enabled",
            "All performance optimizations have been enabled.\n\n"
            "This will provide the best performance for large datasets.",
        )

    def disable_all_optimizations(self):
        """Disable all optimizations."""
        for checkbox in self.optimization_checkboxes.values():
            checkbox.setChecked(False)

        QMessageBox.information(
            self,
            "Optimizations Disabled",
            "All performance optimizations have been disabled.\n\n"
            "This will use the original processing methods for maximum compatibility.",
        )

    def reset_to_defaults(self):
        """Reset to default optimization settings."""
        # Default: enable all optimizations
        for checkbox in self.optimization_checkboxes.values():
            checkbox.setChecked(True)

        QMessageBox.information(
            self,
            "Reset to Defaults",
            "Optimization settings have been reset to defaults.\n\n"
            "All optimizations are enabled by default for best performance.",
        )

    def refresh_performance_status(self):
        """Refresh the performance status display."""
        try:
            # Update system resources display
            self._update_system_resources()

            # Get optimization summary
            summary = get_optimization_summary()

            # Get current status
            status = self.optimization_manager.get_optimization_status()

            # Format status text
            status_text = f"{summary}\n\n"
            status_text += "Current Settings:\n"
            status_text += "-" * 30 + "\n"

            for key, checkbox in self.optimization_checkboxes.items():
                enabled = checkbox.isChecked()
                status_icon = "✓" if enabled else "✗"
                status_text += (
                    f"{status_icon} {self.optimization_checkboxes[key].text()}\n"
                )

            # Add performance info if available
            try:
                memory_profiler.take_snapshot("optimization_dialog_refresh")
                status_text += f"\nMemory monitoring: Active\n"
            except Exception:
                status_text += f"\nMemory monitoring: Not available\n"

            self.status_text.setPlainText(status_text)

        except Exception as e:
            logger.error(f"Error refreshing performance status: {e}")
            self.status_text.setPlainText(f"Error loading performance status: {e}")

    def _update_system_resources(self):
        """Update the system resources display."""
        try:
            resources = self.optimization_manager.get_system_resources_info()

            if resources["psutil_available"]:
                # Update memory display with color coding
                memory_percent = resources["memory_used_percent"]
                memory_text = f"{memory_percent:.1f}% ({resources['memory_available_gb']:.1f}GB available)"

                if memory_percent < 50:
                    memory_color = "#28a745"  # Green
                elif memory_percent < 75:
                    memory_color = "#ffc107"  # Yellow
                elif memory_percent < 90:
                    memory_color = "#fd7e14"  # Orange
                else:
                    memory_color = "#dc3545"  # Red

                self.memory_label.setText(memory_text)
                self.memory_label.setStyleSheet(
                    f"""
                    QLabel {{
                        font-weight: bold;
                        padding: 5px;
                        border-radius: 3px;
                        background-color: {memory_color};
                        color: white;
                    }}
                """
                )

                # Update CPU display
                cpu_percent = resources["cpu_percent"]
                cpu_text = f"{cpu_percent:.1f}%"

                if cpu_percent < 50:
                    cpu_color = "#28a745"  # Green
                elif cpu_percent < 75:
                    cpu_color = "#ffc107"  # Yellow
                else:
                    cpu_color = "#dc3545"  # Red

                self.cpu_label.setText(cpu_text)
                self.cpu_label.setStyleSheet(
                    f"""
                    QLabel {{
                        font-weight: bold;
                        padding: 5px;
                        border-radius: 3px;
                        background-color: {cpu_color};
                        color: white;
                    }}
                """
                )
            else:
                # psutil not available
                self.memory_label.setText("psutil not available")
                self.memory_label.setStyleSheet(
                    """
                    QLabel {
                        font-weight: bold;
                        padding: 5px;
                        border-radius: 3px;
                        background-color: #6c757d;
                        color: white;
                    }
                """
                )

                self.cpu_label.setText("psutil not available")
                self.cpu_label.setStyleSheet(
                    """
                    QLabel {
                        font-weight: bold;
                        padding: 5px;
                        border-radius: 3px;
                        background-color: #6c757d;
                        color: white;
                    }
                """
                )

        except Exception as e:
            logger.error(f"Error updating system resources: {e}")
            self.memory_label.setText("Error")
            self.cpu_label.setText("Error")

    def start_performance_monitoring(self):
        """Start periodic performance monitoring."""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.refresh_performance_status)
        self.monitor_timer.start(5000)  # Refresh every 5 seconds

    def accept(self):
        """Apply optimization settings and close dialog."""
        try:
            # Apply settings
            settings = {}
            for key, checkbox in self.optimization_checkboxes.items():
                settings[key] = checkbox.isChecked()

            # Enable/disable optimizations
            self.optimization_manager.enable_optimizations(settings)

            # Apply database optimizations if enabled
            if settings.get("database_indexes", False):
                self.optimization_manager.apply_database_optimizations()

            # Show confirmation
            enabled_count = sum(settings.values())
            total_count = len(settings)

            QMessageBox.information(
                self,
                "Settings Applied",
                f"Optimization settings have been applied successfully.\n\n"
                f"Enabled: {enabled_count}/{total_count} optimizations\n\n"
                f"Changes will take effect immediately for new operations.",
            )

            super().accept()

        except Exception as e:
            logger.error(f"Error applying optimization settings: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to apply optimization settings:\n\n{str(e)}"
            )

    def reject(self):
        """Cancel changes and close dialog."""
        # Reload original settings
        self.load_current_settings()
        super().reject()


def open_optimization_management(parent=None):
    """Open the optimization management dialog."""
    try:
        dialog = OptimizationManagementDialog(parent)
        dialog.exec_()
    except Exception as e:
        logger.error(f"Error opening optimization management dialog: {e}")
        QMessageBox.critical(
            parent,
            "Error",
            f"Failed to open optimization management dialog:\n\n{str(e)}",
        )
