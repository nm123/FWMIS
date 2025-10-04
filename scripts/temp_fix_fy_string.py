import sqlite3

conn = sqlite3.connect('data/fruitless.db')
cursor = conn.cursor()

cursor.execute("UPDATE financial_years SET fy_string = '2025-26' WHERE id = 149")
conn.commit()
print('Updated fy_string for FY 149 to 2025-26')

# Verify
cursor.execute("SELECT * FROM financial_years WHERE id=149")
result = cursor.fetchone()
print('FY 149 details:', result)

conn.close()