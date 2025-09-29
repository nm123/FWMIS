"""
Write-Off Management Package

This package contains modularized components for the write-off management dialog,
organized by functionality for better maintainability and readability.
"""

from .dialog import WriteOffManagementDialog
from .ui_setup import UISetupManager
from .annexure_manager import AnnexureManager

__all__ = [
    "WriteOffManagementDialog",
    "UISetupManager",
    "AnnexureManager",
]
