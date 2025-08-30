import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
triggers = cursor.fetchall()
print('Triggers:')
for t in triggers:
    print(t)
conn.close()