"""
Edit Case Save Operations

This module has been refactored into modular components for better maintainability.
The main save_case_components function is now in the edit_case_save package.

Provides case saving functionality with validation, data preparation, and database operations.
"""

# Import the modularized save operations
from .edit_case_save import save_case_components
