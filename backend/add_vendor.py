import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

vendor_name = "BER GHOTEL"

# cursor.execute("INSERT INTO vendor (vendor_name) VALUES (?)", (vendor_name,))
# # cursor.execute("INSERT INTO vendor (status) VALUES (?)", ())
cursor.execute("INSERT INTO vendor (vendor_name , status) VALUES (?,?)",(vendor_name , "APPROVED"))
# cursor.execute("DELETE FROM vendor")
conn.commit()

print("Vendor added successfully!")

conn.close()