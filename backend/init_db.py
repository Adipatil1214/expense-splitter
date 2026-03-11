import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS vendor (
    vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT,
    status TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS receipt (
    receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT,
    image_path TEXT,
    status TEXT
)
""")

c.execute("INSERT INTO vendor (vendor_name, status) VALUES ('STARBUCKS', 'approved')")

conn.commit()
conn.close()