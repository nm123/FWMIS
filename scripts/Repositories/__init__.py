"""
Repositories Package

Data access layer following the Repository pattern for clean separation of concerns.
"""

from .repository_factory import (
    RepositoryFactory,
    get_repository_factory,
    get_case_repository,
    get_annexure_repository,
)
from .case_repository import CaseRepository
from .annexure_repository import AnnexureRepository

__all__ = [
    # Factories
    "RepositoryFactory",
    "get_repository_factory",
    # Repositories
    "CaseRepository",
    "AnnexureRepository",
    # Convenience functions
    "get_case_repository",
    "get_annexure_repository",
]
