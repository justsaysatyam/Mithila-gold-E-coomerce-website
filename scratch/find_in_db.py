import sqlite3
import os

db_path = 'db_makhana.sqlite3'
if not os.path.exists(db_path):
    print(f"{db_path} not found")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

target = "Advertisement_Video_Generation_Request.mp4"
found = False

for table_name in [t[0] for t in tables]:
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        for row in rows:
            if target in str(row):
                print(f"FOUND IN TABLE {table_name}: {row}")
                found = True
    except Exception as e:
        continue

if not found:
    print(f"'{target}' not found in any table.")

conn.close()
