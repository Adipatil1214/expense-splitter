import sqlite3

conn = sqlite3.connect("backend/database.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM receipt;")
cursor.execute("DELETE FROM sqlite_sequence WHERE name='receipt';")

conn.commit()   # VERY IMPORTANT

conn.close()