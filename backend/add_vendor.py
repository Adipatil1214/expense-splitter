import sqlite3

conn = sqlite3.connect("backend/database.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(receipt)")
print(cursor.fetchall())

conn.close()