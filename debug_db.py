import sqlite3
from scripts.Utilities.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check installments table
try:
    cursor.execute('SELECT * FROM installments ORDER BY case_id')
    installments = cursor.fetchall()

    print(f'Total installments in database: {len(installments)}')
    print()

    for installment in installments:
        print(f'Installment: {installment}')
        print()

except sqlite3.OperationalError as e:
    print(f'Error accessing installments table: {e}')

# Check if installments table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='installments'")
table_exists = cursor.fetchone()

if table_exists:
    print('Installments table exists')
    cursor.execute('PRAGMA table_info(installments)')
    columns = cursor.fetchall()
    print('Installments table columns:')
    for col in columns:
        print(f'  {col}')
else:
    print('Installments table does NOT exist')

conn.close()
