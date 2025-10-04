import sqlite3

conn = sqlite3.connect('data/fruitless.db')
cursor = conn.cursor()

# Update fy_string for existing FYs
updates = [
    (1, '2019-2020'),
    (2, '2020-2021'),
    (3, '2021-2022'),
    (4, '2022-2023'),
    (5, '2023-2024'),
    (6, '2024-2025')
]

for fy_id, fy_str in updates:
    cursor.execute("UPDATE financial_years SET fy_string = ? WHERE id = ?", (fy_str, fy_id))

conn.commit()

# Verify
cursor.execute('SELECT id, fy_string FROM financial_years ORDER BY id')
print('Updated FY strings:', cursor.fetchall())

conn.close()