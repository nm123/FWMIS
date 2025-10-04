import sqlite3

conn = sqlite3.connect('data/fruitless.db')
cursor = conn.cursor()
cursor.execute("INSERT INTO financial_years (id, start_year, end_year, status, active_period, fy_string) VALUES (149, 2025, 2026, 'open', NULL, '2025-2026')")
conn.commit()
print('FY 149 inserted')
conn.close()