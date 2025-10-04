import sqlite3

conn = sqlite3.connect('data/fruitless.db')
cursor = conn.cursor()

# Update fy_id in cases from 7 to 6
cursor.execute('UPDATE cases SET fy_id = 6 WHERE fy_id = 7')

conn.commit()

# Verify update
cursor.execute('SELECT COUNT(*) FROM cases WHERE fy_id = 6')
updated_count = cursor.fetchone()[0]
print(f'Updated {updated_count} cases to fy_id=6')

# Show sample
cursor.execute('SELECT id, fy_id FROM cases LIMIT 5')
samples = cursor.fetchall()
print('Sample cases fy_id:', samples)

conn.close()