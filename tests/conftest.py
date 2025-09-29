"""
Pytest configuration and shared fixtures for FWMIS testing.
"""

import os
import pytest
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture(scope="session")
def temp_db_path() -> Generator[Path, None, None]:
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="function")
def in_memory_db() -> Generator[sqlite3.Connection, None, None]:
    """Create an in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    # Create basic schema for testing
    conn.execute("""
        CREATE TABLE cases (
            id INTEGER PRIMARY KEY,
            transaction_no TEXT UNIQUE,
            base_transaction_no TEXT,
            description TEXT,
            amount REAL,
            status TEXT DEFAULT 'Active',
            fy_id INTEGER,
            responsibility_id INTEGER,
            created_date TEXT,
            updated_date TEXT,
            assessment_status TEXT,
            suffixes TEXT,
            date_reported TEXT,
            reference_no TEXT,
            lc_status TEXT,
            debtor_name TEXT,
            category TEXT,
            is_finalized INTEGER DEFAULT 0,
            finalized_date TEXT,
            finalization_reason TEXT,
            evidence_paths TEXT,
            write_off_group_id TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE write_off_annexures (
            id INTEGER PRIMARY KEY,
            annexure_no TEXT,
            status TEXT DEFAULT 'Draft',
            role TEXT,
            decline_reason TEXT,
            created_date TEXT,
            updated_date TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE write_off_annexure_cases (
            id INTEGER PRIMARY KEY,
            annexure_id INTEGER,
            case_id INTEGER,
            added_date TEXT,
            FOREIGN KEY (annexure_id) REFERENCES write_off_annexures (id),
            FOREIGN KEY (case_id) REFERENCES cases (id)
        )
    """)

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def mock_config(temp_db_path: Path) -> Generator[dict, None, None]:
    """Create mock configuration for testing."""
    config = {
        "database": {
            "path": str(temp_db_path),
            "max_connections": 5,
            "enable_foreign_keys": False,  # Disable for simpler testing
            "enable_wal": False
        },
        "logging": {
            "level": "DEBUG",
            "enable_console": False,
            "enable_file": False
        },
        "performance": {
            "pagination_size": 50,
            "max_table_rows": 1000
        }
    }
    yield config


@pytest.fixture(scope="function")
def db_manager_mock(mock_config: dict) -> Generator['DatabaseManager', None, None]:
    """Create a database manager with mock configuration."""
    from scripts.Utilities.database_connection import DatabaseManager, DatabaseConfig

    db_config = DatabaseConfig(
        path=mock_config["database"]["path"],
        max_connections=mock_config["database"]["max_connections"],
        enable_foreign_keys=mock_config["database"]["enable_foreign_keys"],
        enable_wal=mock_config["database"]["enable_wal"]
    )

    manager = DatabaseManager(db_config)
    yield manager
    manager.close()


@pytest.fixture(scope="function")
def case_repository(in_memory_db) -> Generator['CaseRepository', None, None]:
    """Create a case repository for testing."""
    from scripts.Repositories.case_repository import CaseRepository

    # Create a mock database manager that uses the in-memory database
    class MockDatabaseManager:
        def __init__(self, conn):
            self.conn = conn

        def execute_query(self, query, params=None):
            try:
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                results = cursor.fetchall()
                # Convert sqlite3.Row objects to dicts
                return [dict(row) for row in results]
            except Exception as e:
                raise e

        def execute_non_query(self, query, params=None):
            try:
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                self.conn.commit()
                return cursor.rowcount
            except Exception as e:
                raise e

        def execute_update(self, query, params=None):
            """Alias for execute_non_query for update operations."""
            return self.execute_non_query(query, params)

        def transaction(self):
            """Context manager for transactions."""
            return self.conn

    mock_manager = MockDatabaseManager(in_memory_db)
    yield CaseRepository(mock_manager)


@pytest.fixture(scope="function")
def annexure_repository(in_memory_db) -> Generator['AnnexureRepository', None, None]:
    """Create an annexure repository for testing."""
    from scripts.Repositories.annexure_repository import AnnexureRepository

    # Create a mock database manager that uses the in-memory database
    class MockDatabaseManager:
        def __init__(self, conn):
            self.conn = conn

        def execute_query(self, query, params=None):
            try:
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                results = cursor.fetchall()
                # Convert sqlite3.Row objects to dicts
                return [dict(row) for row in results]
            except Exception as e:
                raise e

        def execute_non_query(self, query, params=None):
            try:
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                self.conn.commit()
                return cursor.rowcount
            except Exception as e:
                raise e

        def execute_update(self, query, params=None):
            """Alias for execute_non_query for update operations."""
            return self.execute_non_query(query, params)

        def transaction(self):
            """Context manager for transactions."""
            return self.conn

    mock_manager = MockDatabaseManager(in_memory_db)
    yield AnnexureRepository(mock_manager)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    # Set test environment
    os.environ["FWMIS_ENVIRONMENT"] = "test"
    os.environ["FWMIS_DEBUG"] = "true"
    os.environ["FWMIS_LOG_LEVEL"] = "DEBUG"
    os.environ["FWMIS_LOG_CONSOLE"] = "false"

    yield

    # Cleanup test environment variables
    test_vars = ["FWMIS_ENVIRONMENT", "FWMIS_DEBUG", "FWMIS_LOG_LEVEL", "FWMIS_LOG_CONSOLE"]
    for var in test_vars:
        os.environ.pop(var, None)


# Custom pytest markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


# Test configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on path."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)

        # Mark slow tests
        if "slow" in item.keywords or "performance" in str(item.fspath):
            item.add_marker(pytest.mark.slow)
