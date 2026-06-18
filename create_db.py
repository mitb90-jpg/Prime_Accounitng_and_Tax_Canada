import sqlite3

conn = sqlite3.connect("prime_accounting.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS clients
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    account_name TEXT,
    account_type TEXT
)
""")

conn.commit()
conn.close()
