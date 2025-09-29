"""
Legacy Configuration Module

This module provides backward compatibility for existing code while
encouraging migration to the new configuration system in config.settings.
"""

import logging
import os
import sqlite3

# Import new configuration system
from scripts.config import get_config

# Get configuration instance
config = get_config()

# Backward compatibility constants - use new config system
BASE_DIR = str(config.base_dir)
DATA_DIR = str(config.data_dir)
DB_PATH = str(config.database.path)

# Ensure directories exist
os.makedirs(config.data_dir, exist_ok=True)
os.makedirs(config.logs_dir, exist_ok=True)
os.makedirs(config.temp_dir, exist_ok=True)

# Legacy database cleanup (keeping for backward compatibility)
fmis_db_path = os.path.join(DATA_DIR, "fwmis.db")
if os.path.exists(fmis_db_path):
    if os.path.getsize(fmis_db_path) == 0:
        os.remove(fmis_db_path)
        logging.info("Removed empty fwmis.db file")
    else:
        logging.warning("Non-empty fwmis.db found, not removing")


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
                "ALTER TABLE cases ADD COLUMN shared_document_id INTEGER REFERENCES shared_documents(id)"
            )

        conn.commit()
        conn.close()
        logging.info("Shared documents table initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing shared documents table: {e}")
