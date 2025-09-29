"""
Import Worker Module

This module has been refactored into modular components for better maintainability.
The main ImportWorker class is now in the import_worker package.

Provides threaded import functionality for processing BAS transactions into FWMIS cases.
"""

# Import the modularized import worker
from .import_worker import ImportWorker
