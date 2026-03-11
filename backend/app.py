from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import pytesseract
from PIL import Image
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Change path if different
pytesseract.pytesseract.tesseract_cmd = r"C:/Users/padit/AppData/Local/Programs/Tesseract-OCR/tesseract.exe"

@app.route("/upload", methods=["POST"])
def upload():
    if "receipt" not in request.files:
       return jsonify({"error": "No file uploaded"}), 400
    file = request.files["receipt"]
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    print("Upload route hit")
    text = pytesseract.image_to_string(Image.open(filepath))
    vendor_name = text.split("\n")[0].strip().upper()

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM vendor WHERE UPPER(vendor_name)=?", (vendor_name,))
    result = c.fetchone()

    status = "APPROVED" if result else "PENDING"

    c.execute("INSERT INTO receipt (vendor_name, image_path, status) VALUES (?, ?, ?)",
              (vendor_name, filepath, status))

    conn.commit()
    conn.close()

    return jsonify({"vendor": vendor_name, "status": status})

@app.route("/receipts", methods=["GET"])
def get_receipts():
    import sqlite3
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT  receipt_id, vendor_name, status FROM receipt")
    rows = cursor.fetchall()

    conn.close()

    receipts = []
    for row in rows:
        receipts.append({
            "id": row[0],
            "vendor_name": row[1],
            "status": row[2]
        })

    return {"receipts": receipts}

@app.route("/approve/<int:receipt_id>", methods=["POST"])
def approve_receipt(receipt_id):
    import sqlite3
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE receipt SET status = ? WHERE receipt_id = ?",
        ("APPROVED", receipt_id)
    )

    conn.commit()
    conn.close()

    return {"message": "Receipt approved"}

@app.route("/approve-vendor/<int:receipt_id>", methods=["POST"])
def approve_vendor(receipt_id):
    import sqlite3

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # 1️⃣ Get vendor name from receipt
    cursor.execute(
        "SELECT vendor_name FROM receipt WHERE receipt_id = ?",
        (receipt_id,)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return {"error": "Receipt not found"}, 404

    vendor_name = result[0]

    # 2️⃣ Insert vendor into vendors table
    cursor.execute(
        "INSERT OR IGNORE INTO vendor (vendor_name, status) VALUES (?, ?)",
        (vendor_name, "APPROVED")
    )

    # 3️⃣ Update receipt status
    cursor.execute(
        "UPDATE receipt SET status = ? WHERE receipt_id = ?",
        ("APPROVED", receipt_id)
    )

    conn.commit()
    conn.close()

    return {"message": "Vendor approved and added to database"}


if __name__ == "__main__":
    app.run(debug=True)