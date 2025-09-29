"""
Database Connection Manager

Provides centralized, thread-safe database connection management with connection pooling,
transaction support, and consistent error handling.
"""

import logging
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    path: str
    enable_foreign_keys: bool = True
    enable_wal: bool = True
    synchronous_mode: str = "NORMAL"
    cache_size: int = -64000  # 64MB cache
    temp_store: str = "MEMORY"
    journal_mode: str = "WAL"
    max_connections: int = 10


class ConnectionPool:
    """Thread-safe SQLite connection pool."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool: Dict[int, sqlite3.Connection] = {}
        self._lock = threading.RLock()
        self._created_connections = 0

    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool for the current thread."""
        thread_id = threading.get_ident()

        with self._lock:
            if thread_id in self._pool:
                conn = self._pool[thread_id]
                # Verify connection is still valid
                try:
                    conn.execute("SELECT 1").fetchone()
                    return conn
                except sqlite3.Error:
                    # Connection is dead, remove it
                    del self._pool[thread_id]

            # Create new connection
            if self._created_connections >= self.config.max_connections:
                raise RuntimeError(
                    f"Maximum connections ({self.config.max_connections}) reached"
                )

            conn = self._create_connection()
            self._pool[thread_id] = conn
            self._created_connections += 1
            logger.debug(f"Created new database connection for thread {thread_id}")

            return conn

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimized settings."""
        conn = sqlite3.connect(
            self.config.path,
            timeout=30.0,
            isolation_level=None,  # Enable autocommit mode
        )

        # Enable row factory for dict-like access
        conn.row_factory = sqlite3.Row

        # Configure pragmas for performance and reliability
        pragmas = [
            ("foreign_keys", "ON" if self.config.enable_foreign_keys else "OFF"),
            ("journal_mode", self.config.journal_mode),
            ("synchronous", self.config.synchronous_mode),
            ("cache_size", str(self.config.cache_size)),
            ("temp_store", self.config.temp_store),
            ("mmap_size", "268435456"),  # 256MB memory map
            ("busy_timeout", "30000"),  # 30 second timeout
        ]

        with conn:
            for pragma, value in pragmas:
                conn.execute(f"PRAGMA {pragma} = {value}")

        return conn

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            for thread_id, conn in self._pool.items():
                try:
                    conn.close()
                    logger.debug(f"Closed connection for thread {thread_id}")
                except Exception as e:
                    logger.warning(
                        f"Error closing connection for thread {thread_id}: {e}"
                    )

            self._pool.clear()
            self._created_connections = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        with self._lock:
            return {
                "active_connections": len(self._pool),
                "total_created": self._created_connections,
                "max_connections": self.config.max_connections,
                "threads_with_connections": list(self._pool.keys()),
            }


class DatabaseManager:
    """Main database manager with connection pooling and transaction support."""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        if config is None:
            from .config import DB_PATH

            config = DatabaseConfig(path=DB_PATH)

        self.config = config
        self._pool = ConnectionPool(config)
        self._local = threading.local()

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection for the current thread."""
        return self._pool.get_connection()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """
        Context manager for database transactions.

        Automatically commits on success, rolls back on exception.
        """
        conn = self.get_connection()
        try:
            # Begin transaction
            conn.execute("BEGIN")
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction failed, rolled back: {e}")
            raise
        finally:
            # Connection stays in pool for reuse
            pass

    def execute_query(
        self, query: str, params: Optional[List[Any]] = None, fetch: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.

        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results

        Returns:
            List of result rows as dictionaries
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])

            if fetch:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                return []

    def execute_update(self, query: str, params: Optional[List[Any]] = None) -> int:
        """
        Execute an update/insert/delete query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            return cursor.rowcount

    def execute_script(self, script: str) -> None:
        """
        Execute a SQL script.

        Args:
            script: SQL script to execute
        """
        with self.transaction() as conn:
            conn.executescript(script)

    def get_stats(self) -> Dict[str, Any]:
        """Get database manager statistics."""
        return {
            "pool_stats": self._pool.get_stats(),
            "config": {
                "path": self.config.path,
                "max_connections": self.config.max_connections,
                "foreign_keys": self.config.enable_foreign_keys,
                "wal_mode": self.config.enable_wal,
            },
        }

    def close(self) -> None:
        """Close all connections."""
        self._pool.close_all()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None
_db_lock = threading.Lock()


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance (singleton)."""
    global _db_manager

    if _db_manager is None:
        with _db_lock:
            if _db_manager is None:
                _db_manager = DatabaseManager()

    return _db_manager


def get_db_connection() -> sqlite3.Connection:
    """
    Legacy compatibility function.

    Returns a database connection from the pool.
    """
    return get_database_manager().get_connection()


@contextmanager
def db_transaction() -> Iterator[sqlite3.Connection]:
    """
    Legacy compatibility context manager.

    Use get_database_manager().transaction() instead for new code.
    """
    with get_database_manager().transaction() as conn:
        yield conn


def db_execute_query(
    query: str, params: Optional[List[Any]] = None, fetch: bool = True
) -> List[Dict[str, Any]]:
    """
    Legacy compatibility function.

    Use get_database_manager().execute_query() instead for new code.
    """
    return get_database_manager().execute_query(query, params, fetch)


def db_execute_update(query: str, params: Optional[List[Any]] = None) -> int:
    """
    Legacy compatibility function.

    Use get_database_manager().execute_update() instead for new code.
    """
    return get_database_manager().execute_update(query, params)
