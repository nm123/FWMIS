import sqlite3

conn = sqlite3.connect('data/fruitless.db')
cursor = conn.cursor()

# Count cases in fy_id=6 before, excluding deleted
cursor.execute("SELECT COUNT(*) FROM cases WHERE fy_id=6 AND list != 'Deleted Cases'")
before_count = cursor.fetchone()[0]
print(f'Cases in fy_id=6 (non-deleted) before migration: {before_count}')

# Update
cursor.execute("UPDATE cases SET fy_id=149 WHERE fy_id=6 AND list != 'Deleted Cases'")
conn.commit()
print(f'Updated {cursor.rowcount} cases to fy_id=149')

# Verify after
cursor.execute("SELECT COUNT(*) FROM cases WHERE fy_id=149")
after_count = cursor.fetchone()[0]
print(f'Cases in fy_id=149 after migration: {after_count}')

cursor.execute("SELECT fy_id, COUNT(*) FROM cases GROUP BY fy_id")
groups = cursor.fetchall()
print('Updated fy_id groups:')
for row in groups:
    print(row)

conn.close()