import logging
import os
import sqlite3
from typing import Callable, Tuple

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Set BASE_DIR to the project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "fruitless.db")
os.makedirs(DATA_DIR, exist_ok=True)

# Schema migration registry
Migration = Tuple[str, str, Callable[[sqlite3.Connection], None]]
SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


def _ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (
            id TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    """
    )


def _has_migration_run(conn: sqlite3.Connection, migration_id: str) -> bool:
    cursor = conn.execute(
        f"SELECT 1 FROM {SCHEMA_MIGRATIONS_TABLE} WHERE id = ? LIMIT 1",
        (migration_id,),
    )
    return cursor.fetchone() is not None


def _record_migration(
    conn: sqlite3.Connection, migration_id: str, description: str
) -> None:
    conn.execute(
        f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (id, description) VALUES (?, ?)",
        (migration_id, description),
    )


def _migration_add_shared_document_fk(conn: sqlite3.Connection) -> None:
    cursor = conn.execute("PRAGMA table_info(cases)")
    columns = {column[1] for column in cursor.fetchall()}

    if "shared_document_id" not in columns:
        conn.execute(
            """
            ALTER TABLE cases
            ADD COLUMN shared_document_id INTEGER REFERENCES shared_documents(id)
        """
        )


MIGRATIONS: Tuple[Migration, ...] = (
    (
        "20241019_add_shared_document_fk",
        "Ensure cases table tracks shared document relationships",
        _migration_add_shared_document_fk,
    ),
)


def _run_schema_migrations(conn: sqlite3.Connection) -> None:
    _ensure_schema_migrations_table(conn)

    for migration_id, description, apply_migration in MIGRATIONS:
        if _has_migration_run(conn, migration_id):
            continue

        logger.info("Applying migration '%s'", migration_id)
        apply_migration(conn)
        _record_migration(conn, migration_id, description)
        logger.info("Migration '%s' applied successfully", migration_id)

# Check for and remove empty FMIS.db if it exists
fmis_db_path = os.path.join(DATA_DIR, "fwmis.db")
if os.path.exists(fmis_db_path):
    if os.path.getsize(fmis_db_path) == 0:
        os.remove(fmis_db_path)
        logger.info("Removed empty fwmis.db file")
    else:
        logger.warning("Non-empty fwmis.db found, not removing")


def initialize_shared_documents_table():
    """Create the shared_documents table if it doesn't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS shared_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_path TEXT NOT NULL,
                document_name TEXT,
                upload_date TEXT,
                fy_id TEXT,
                document_type TEXT,
                uploaded_by TEXT,
                description TEXT
            )
        """
        )

        # Add shared_document_id column to cases table if it doesn't exist
        cursor.execute("PRAGMA table_info(cases)")
        columns = [column[1] for column in cursor.fetchall()]

        if "shared_document_id" not in columns:
            cursor.execute(
                (
                    "ALTER TABLE cases ADD COLUMN shared_document_id "
                    "INTEGER REFERENCES shared_documents(id)"
                )
            )

        _run_schema_migrations(conn)

        conn.commit()
        conn.close()
        logger.info("Shared documents table initialized successfully")
    except Exception:
        logger.exception("Error initializing shared documents table")
