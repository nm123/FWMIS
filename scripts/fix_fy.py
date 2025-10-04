import sqlite3

conn = sqlite3.connect('data/fruitless.db')
cursor = conn.cursor()

# Delete existing FY with id=7 if present
cursor.execute('DELETE FROM financial_years WHERE id = 7')

# Insert financial years 1 to 6
financial_years = [
    (1, 2019, 2020, 'closed', None),
    (2, 2020, 2021, 'closed', None),
    (3, 2021, 2022, 'closed', None),
    (4, 2022, 2023, 'closed', None),
    (5, 2023, 2024, 'closed', None),
    (6, 2024, 2025, 'open', None)
]

for fy in financial_years:
    cursor.execute(
        "INSERT OR IGNORE INTO financial_years (id, start_year, end_year, status, active_period) VALUES (?, ?, ?, ?, ?)",
        fy
    )

conn.commit()

# Verify insertion
cursor.execute('SELECT * FROM financial_years ORDER BY id')
fys = cursor.fetchall()
print('Financial years restored successfully')
print('Current FYs:', fys)

conn.close()