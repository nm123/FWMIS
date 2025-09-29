"""
Results Handling Module

Contains functionality for processing, recording, and analyzing test results.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PyQt5.QtWidgets import QTableWidgetItem


class ResultsHandler:
    """
    Handles test results processing, recording, and display.
    """

    def __init__(self, dialog):
        """
        Initialize the results handler.

        Args:
            dialog: The parent AutomatedTestingDialog instance
        """
        self.dialog = dialog

    def verification_completed(self, results: Dict) -> None:
        """
        Handle completion of verification tests.

        Args:
            results: Verification test results
        """
        self.record_verification_result(results)

        # Update UI
        if results.get("success", False):
            self.dialog.verification_status_label.setText("✅ PASSED")
            self.dialog.verification_status_label.setStyleSheet(
                "QLabel { color: green; font-weight: bold; }"
            )
        else:
            self.dialog.verification_status_label.setText("❌ FAILED")
            self.dialog.verification_status_label.setStyleSheet(
                "QLabel { color: red; font-weight: bold; }"
            )

        # Update last run time
        self.dialog.last_verification_label.setText(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def record_verification_result(self, results: Dict) -> None:
        """
        Record verification results to database and history.

        Args:
            results: Verification test results
        """
        # Add timestamp
        results["timestamp"] = datetime.now().isoformat()
        results["type"] = "verification"

        # Add to history
        self.dialog.test_history.insert(0, results)

        # Save to database
        self._save_result_to_database(results)

        # Update UI table
        self._update_results_table(results)

    def test_suite_completed(self, results: Dict) -> None:
        """
        Handle completion of test suite execution.

        Args:
            results: Test suite execution results
        """
        self.record_test_result(results)

        # Update progress display
        if results.get("success", False):
            self.dialog.progress_label.setText("✅ Test suite completed successfully")
        else:
            self.dialog.progress_label.setText("❌ Test suite failed")

    def record_test_result(self, results: Dict) -> None:
        """
        Record test suite results to database and history.

        Args:
            results: Test suite execution results
        """
        # Add metadata
        results["timestamp"] = datetime.now().isoformat()
        results["type"] = "suite"

        # Add to history
        self.dialog.test_history.insert(0, results)

        # Save to database
        self._save_result_to_database(results)

        # Update UI
        self._update_results_table(results)
        self.load_test_history()

    def _save_result_to_database(self, results: Dict) -> None:
        """
        Save test results to the database.

        Args:
            results: Test results to save
        """
        try:
            # Get database path
            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Create test_results table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    type TEXT,
                    success BOOLEAN,
                    return_code INTEGER,
                    output TEXT,
                    duration REAL
                )
            """
            )

            # Insert result
            cursor.execute(
                """
                INSERT INTO test_results (timestamp, type, success, return_code, output, duration)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    results.get("timestamp"),
                    results.get("type"),
                    results.get("success", False),
                    results.get("return_code", -1),
                    results.get("output", ""),
                    results.get("duration", 0),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error saving test result to database: {e}")

    def _update_results_table(self, results: Dict) -> None:
        """
        Update the results table in the UI.

        Args:
            results: Test results to display
        """
        try:
            table = self.dialog.results_table
            row_count = table.rowCount()

            # Insert new row at top
            table.insertRow(0)

            # Set data
            timestamp = datetime.fromisoformat(results["timestamp"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            table.setItem(0, 0, QTableWidgetItem(timestamp))
            table.setItem(
                0, 1, QTableWidgetItem(results.get("type", "unknown").title())
            )
            table.setItem(
                0,
                2,
                QTableWidgetItem("✅ PASS" if results.get("success") else "❌ FAIL"),
            )
            table.setItem(0, 3, QTableWidgetItem(f"{results.get('duration', 0):.2f}s"))

        except Exception as e:
            print(f"Error updating results table: {e}")

    def load_test_history(self) -> None:
        """
        Load test history from database and update UI.
        """
        try:
            # Get database path
            from scripts.Utilities.config import DB_PATH

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Load recent results
            cursor.execute(
                """
                SELECT timestamp, type, success, return_code, output, duration
                FROM test_results
                ORDER BY timestamp DESC
                LIMIT 50
            """
            )

            results = cursor.fetchall()
            conn.close()

            # Update history
            self.dialog.test_history = []
            for row in results:
                result = {
                    "timestamp": row[0],
                    "type": row[1],
                    "success": bool(row[2]),
                    "return_code": row[3],
                    "output": row[4],
                    "duration": row[5],
                }
                self.dialog.test_history.append(result)

            # Update UI table
            self._populate_results_table()

        except Exception as e:
            print(f"Error loading test history: {e}")

    def _populate_results_table(self) -> None:
        """Populate the results table with current history."""
        try:
            table = self.dialog.results_table
            table.setRowCount(0)  # Clear table

            for result in self.dialog.test_history:
                row_count = table.rowCount()
                table.insertRow(row_count)

                timestamp = datetime.fromisoformat(result["timestamp"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                table.setItem(row_count, 0, QTableWidgetItem(timestamp))
                table.setItem(
                    row_count,
                    1,
                    QTableWidgetItem(result.get("type", "unknown").title()),
                )
                table.setItem(
                    row_count,
                    2,
                    QTableWidgetItem("✅ PASS" if result.get("success") else "❌ FAIL"),
                )
                table.setItem(
                    row_count, 3, QTableWidgetItem(f"{result.get('duration', 0):.2f}s")
                )

        except Exception as e:
            print(f"Error populating results table: {e}")

    def analyze_performance_trends(self) -> Dict:
        """
        Analyze performance trends from test history.

        Returns:
            Dictionary containing performance analysis results
        """
        try:
            if len(self.dialog.test_history) < 2:
                return {"error": "Insufficient data for trend analysis"}

            # Extract duration data
            durations = [
                r.get("duration", 0)
                for r in self.dialog.test_history
                if r.get("success")
            ]

            if len(durations) < 2:
                return {"error": "Insufficient successful test data"}

            # Calculate trends
            avg_duration = sum(durations) / len(durations)
            recent_avg = sum(durations[:5]) / min(5, len(durations))  # Last 5 tests
            trend = "stable"

            if recent_avg > avg_duration * 1.1:
                trend = "slowing"
            elif recent_avg < avg_duration * 0.9:
                trend = "improving"

            return {
                "average_duration": avg_duration,
                "recent_average": recent_avg,
                "trend": trend,
                "total_tests": len(self.dialog.test_history),
                "success_rate": len(durations) / len(self.dialog.test_history),
            }

        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    def generate_test_recommendations(self) -> List[str]:
        """
        Generate test improvement recommendations based on history.

        Returns:
            List of recommendation strings
        """
        recommendations = []
        analysis = self.analyze_performance_trends()

        if "error" in analysis:
            return [f"Cannot generate recommendations: {analysis['error']}"]

        # Performance recommendations
        if analysis.get("trend") == "slowing":
            recommendations.append(
                "⚠️ Performance regression detected. Consider optimizing slow tests."
            )
        elif analysis.get("trend") == "improving":
            recommendations.append(
                "✅ Performance is improving. Keep up the good work!"
            )

        # Success rate recommendations
        success_rate = analysis.get("success_rate", 0)
        if success_rate < 0.8:
            recommendations.append(
                "❌ Low success rate detected. Focus on fixing failing tests."
            )
        elif success_rate < 0.95:
            recommendations.append(
                "⚠️ Moderate success rate. Consider improving test stability."
            )

        # Frequency recommendations
        total_tests = analysis.get("total_tests", 0)
        if total_tests < 10:
            recommendations.append(
                "📊 Limited test history. Run more tests for better analysis."
            )

        if not recommendations:
            recommendations.append(
                "✅ Test suite is performing well. Continue regular testing."
            )

        return recommendations
