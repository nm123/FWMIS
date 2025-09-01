import os
import logging
import sqlite3

# Set BASE_DIR to the project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'fruitless.db')
os.makedirs(DATA_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=os.path.join(DATA_DIR, 'app.log'),
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def initialize_shared_documents_table():
    """Create the shared_documents table if it doesn't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
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
        """)

        # Add shared_document_id column to cases table if it doesn't exist
        cursor.execute("PRAGMA table_info(cases)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'shared_document_id' not in columns:
            cursor.execute("ALTER TABLE cases ADD COLUMN shared_document_id INTEGER REFERENCES shared_documents(id)")

        conn.commit()
        conn.close()
        print("Shared documents table initialized successfully")
    except Exception as e:
        print(f"Error initializing shared documents table: {e}")