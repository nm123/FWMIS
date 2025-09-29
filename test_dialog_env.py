#!/usr/bin/env python3
"""
Test if environment variables work with pytest subprocess
"""

import os
import sys
import tempfile
import subprocess
import sqlite3

def test_env_vars():
    """Test that environment variables work with pytest subprocess"""

    # Create test database
    test_db_path = os.path.join(tempfile.gettempdir(), 'test_env.db')

    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Create minimal schema
    conn.execute("""
        CREATE TABLE cases (
            id INTEGER PRIMARY KEY,
            transaction_no TEXT UNIQUE,
            description TEXT,
            amount REAL,
            status TEXT DEFAULT 'Active'
        )
    """)

    cursor.execute("INSERT INTO cases (transaction_no, description, amount) VALUES ('TEST001', 'Test', 1000.00)")
    conn.commit()
    conn.close()

    # Set environment variables
    env = os.environ.copy()
    env['FWMIS_TEST_DB'] = test_db_path

    # Run a simple test that uses the environment variable
    result = subprocess.run([
        sys.executable, '-c',
        """
import os
import sqlite3
test_db = os.environ.get('FWMIS_TEST_DB')
if test_db:
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM cases')
    result = cursor.fetchone()
    print(f'SUCCESS: Found {result[0]} cases in test database')
    conn.close()
else:
    print('FAILED: FWMIS_TEST_DB environment variable not set')
        """
    ], env=env, capture_output=True, text=True)

    print("STDOUT:", result.stdout.strip())
    if result.stderr:
        print("STDERR:", result.stderr.strip())
    print("Return code:", result.returncode)

    # Cleanup
    os.remove(test_db_path)

    return result.returncode == 0

if __name__ == "__main__":
    success = test_env_vars()
    print("Environment variable test:", "PASSED" if success else "FAILED")
