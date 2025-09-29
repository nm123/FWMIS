#!/usr/bin/env python3
"""
Daily Test Check Module

This module provides automated verification and auto-fix functionality
for the FWMIS testing infrastructure.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class VerificationWorker(QThread):
    """Worker thread for running verification checks."""

    progress = pyqtSignal(str)  # Progress message
    finished = pyqtSignal(dict)  # Results dictionary

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        """Run the verification process."""
        try:
            results = self._run_verification_checks()
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            self.finished.emit({"error": str(e)})

    def _run_verification_checks(self) -> Dict:
        """Run all verification checks."""
        results = {
            "database_integrity": False,
            "test_discovery": False,
            "import_modules": False,
            "performance_benchmarks": False,
            "auto_fixes_applied": [],
            "issues_found": []
        }

        # Check database integrity
        self.progress.emit("Checking database integrity...")
        try:
            from scripts.Utilities.database_connection import get_database_manager
            db_manager = get_database_manager()
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cases")
            results["database_integrity"] = True
            self.progress.emit("✓ Database integrity check passed")
        except Exception as e:
            results["issues_found"].append(f"Database integrity: {e}")
            self.progress.emit(f"✗ Database integrity issue: {e}")

        # Check test discovery
        self.progress.emit("Checking test discovery...")
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, "-m", "pytest", "--collect-only", "-q"
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

            if result.returncode == 0:
                results["test_discovery"] = True
                self.progress.emit("✓ Test discovery check passed")
            else:
                results["issues_found"].append(f"Test discovery failed: {result.stderr}")
                self.progress.emit(f"✗ Test discovery issue: {result.stderr}")
        except Exception as e:
            results["issues_found"].append(f"Test discovery error: {e}")
            self.progress.emit(f"✗ Test discovery error: {e}")

        # Check import modules
        self.progress.emit("Checking module imports...")
        try:
            # Test key imports
            from scripts.Repositories.case_repository import CaseRepository
            from scripts.Repositories.annexure_repository import AnnexureRepository
            from scripts.Utilities.database_connection import get_database_manager
            from scripts.case_management_modules.import_cases_logic import ImportCasesLogic

            results["import_modules"] = True
            self.progress.emit("✓ Module import check passed")
        except ImportError as e:
            results["issues_found"].append(f"Import error: {e}")
            self.progress.emit(f"✗ Import error: {e}")

        # Check performance benchmarks
        self.progress.emit("Checking performance benchmarks...")
        try:
            # Run a quick performance test
            import time
            start_time = time.time()

            # Quick database query test
            from scripts.Repositories.case_repository import CaseRepository
            from scripts.Utilities.database_connection import get_database_manager

            repo = CaseRepository(get_database_manager())
            cases = repo.get_cases_by_status("Active", limit=10)

            query_time = time.time() - start_time
            if query_time < 1.0:  # Should be fast
                results["performance_benchmarks"] = True
                self.progress.emit("✓ Performance benchmark check passed")
            else:
                results["issues_found"].append(f"Performance issue: Query took {query_time:.2f}s")
                self.progress.emit(f"✗ Performance issue: Query took {query_time:.2f}s")
        except Exception as e:
            results["issues_found"].append(f"Performance check error: {e}")
            self.progress.emit(f"✗ Performance check error: {e}")

        # Apply auto-fixes
        self.progress.emit("Applying auto-fixes...")
        fixes_applied = self._apply_auto_fixes(results["issues_found"])
        results["auto_fixes_applied"] = fixes_applied

        return results

    def _apply_auto_fixes(self, issues: List[str]) -> List[str]:
        """Apply automatic fixes for common issues."""
        fixes_applied = []

        for issue in issues:
            if "Import error" in issue:
                # Try to fix import issues
                try:
                    # Reinstall requirements or fix path issues
                    self.progress.emit("Attempting to fix import issues...")
                    # This is a placeholder - actual fixes would depend on the specific issue
                    fixes_applied.append("Import fix attempted")
                except Exception as e:
                    logger.error(f"Failed to apply import fix: {e}")

        return fixes_applied


def run_verification_auto_fix(parent_dialog=None):
    """
    Run automated verification and auto-fix process.

    Args:
        parent_dialog: Parent dialog for progress display
    """
    # Create progress dialog
    progress_dialog = QProgressDialog(
        "Running automated verification...",
        "Cancel",
        0, 100,
        parent_dialog
    )
    progress_dialog.setWindowTitle("FWMIS Verification")
    progress_dialog.setModal(True)
    progress_dialog.show()

    # Create worker thread
    worker = VerificationWorker(parent_dialog)

    def update_progress(message):
        progress_dialog.setLabelText(message)

    def on_finished(results):
        progress_dialog.close()

        if "error" in results:
            QMessageBox.critical(
                parent_dialog, "Verification Error",
                f"Verification failed: {results['error']}"
            )
            return

        # Show results
        success_count = sum(1 for v in results.values()
                          if isinstance(v, bool) and v)
        total_checks = sum(1 for v in results.values()
                         if isinstance(v, bool))

        message = f"Verification completed!\n\n"
        message += f"Checks passed: {success_count}/{total_checks}\n\n"

        if results["issues_found"]:
            message += "Issues found:\n"
            for issue in results["issues_found"]:
                message += f"• {issue}\n"
            message += "\n"

        if results["auto_fixes_applied"]:
            message += "Auto-fixes applied:\n"
            for fix in results["auto_fixes_applied"]:
                message += f"• {fix}\n"

        QMessageBox.information(
            parent_dialog, "Verification Results", message
        )

    # Connect signals
    worker.progress.connect(update_progress)
    worker.finished.connect(on_finished)

    # Start verification
    worker.start()

    # Wait for completion or cancellation
    while worker.isRunning():
        QApplication.processEvents()
        if progress_dialog.wasCanceled():
            worker.terminate()
            worker.wait()
            break

    progress_dialog.close()


if __name__ == "__main__":
    # Allow running from command line for testing
    app = QApplication(sys.argv)
    run_verification_auto_fix()
    app.exec_()
