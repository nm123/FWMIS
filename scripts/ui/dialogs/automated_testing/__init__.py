"""
Automated Testing Package

This package contains modularized components for the automated testing dialog,
organized by functionality for better maintainability and readability.
"""

from .dialog import AutomatedTestingDialog
from .test_worker import TestRunnerWorker
from .test_execution import TestExecutionManager
from .results_handling import ResultsHandler
from .ui_setup import UISetupManager

__all__ = [
    "AutomatedTestingDialog",
    "TestRunnerWorker",
    "TestExecutionManager",
    "ResultsHandler",
    "UISetupManager",
]
