"""
Repository Factory

Factory for creating and managing repository instances with dependency injection.
"""

from scripts.Utilities.database_connection import DatabaseManager, get_database_manager

from .annexure_repository import AnnexureRepository
from .case_repository import CaseRepository


class RepositoryFactory:
    """Factory for creating repository instances."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._repositories = {}

    def get_case_repository(self) -> CaseRepository:
        """Get the case repository instance."""
        if "case" not in self._repositories:
            self._repositories["case"] = CaseRepository(self.db_manager)
        return self._repositories["case"]

    def get_annexure_repository(self) -> AnnexureRepository:
        """Get the annexure repository instance."""
        if "annexure" not in self._repositories:
            self._repositories["annexure"] = AnnexureRepository(self.db_manager)
        return self._repositories["annexure"]


# Global repository factory instance
_repository_factory: RepositoryFactory = None


def get_repository_factory() -> RepositoryFactory:
    """Get the global repository factory instance (singleton)."""
    global _repository_factory

    if _repository_factory is None:
        db_manager = get_database_manager()
        _repository_factory = RepositoryFactory(db_manager)

    return _repository_factory


def get_case_repository() -> CaseRepository:
    """Convenience function to get case repository."""
    return get_repository_factory().get_case_repository()


def get_annexure_repository() -> AnnexureRepository:
    """Convenience function to get annexure repository."""
    return get_repository_factory().get_annexure_repository()
