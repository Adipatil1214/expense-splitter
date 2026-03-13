from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import pytesseract
from PIL import Image
import os
from flask import send_from_directory
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Change path if different
pytesseract.pytesseract.tesseract_cmd = r"C:<PATH>/Tesseract-OCR/tesseract.exe"


# ---------------------------
# Upload Receipt + OCR
# ---------------------------
@app.route("/upload", methods=["POST"])
def upload():

    if "receipt" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["receipt"]
    user_id = request.form.get("user_id")

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    text = pytesseract.image_to_string(Image.open(filepath))
    vendor_name = text.split("\n")[0].strip().upper()

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # check vendor
    c.execute("SELECT * FROM vendor WHERE UPPER(vendor_name)=?", (vendor_name,))
    result = c.fetchone()

    status = "APPROVED" if result else "PENDING"

    # insert receipt
    c.execute(
        "INSERT INTO receipt (vendor_name, image_path, status, user_id) VALUES (?, ?, ?, ?)",
        (vendor_name, filepath, status, user_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "vendor": vendor_name,
        "status": status,
        "user_id": user_id
    })


# ---------------------------
# Get All Receipts (Admin Panel)
# ---------------------------
@app.route("/receipts", methods=["GET"])
def get_receipts():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT receipt_id, vendor_name, status, user_id, image_path FROM receipt")
    rows = cursor.fetchall()

    conn.close()

    receipts = []
    for row in rows:
        receipts.append({
            "id": row[0],
            "vendor_name": row[1],
            "status": row[2],
            "user_id": row[3],
            "image_path": row[4]
        })

    return {"receipts": receipts}


# ---------------------------
# Approve Receipt (ONLY status update)
# ---------------------------
@app.route("/approve/<int:receipt_id>", methods=["POST"])
def approve_receipt(receipt_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE receipt SET status = ? WHERE receipt_id = ?",
        ("APPROVED", receipt_id)
    )

    conn.commit()
    conn.close()

    return {"message": "Receipt approved"}


# ---------------------------
# Add Vendor To Database
# ---------------------------
@app.route("/add-vendor/<int:receipt_id>", methods=["POST"])
def add_vendor_to_db(receipt_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get vendor name from receipt
    cursor.execute(
        "SELECT vendor_name FROM receipt WHERE receipt_id = ?",
        (receipt_id,)
    )

    result = cursor.fetchone()

    if not result:
        conn.close()
        return {"error": "Receipt not found"}, 404

    vendor_name = result[0]

    # Insert vendor into vendor table
    cursor.execute(
        "INSERT OR IGNORE INTO vendor (vendor_name, status) VALUES (?, ?)",
        (vendor_name, "APPROVED")
    )

    conn.commit()
    conn.close()

    return {"message": "Vendor added to database"}

# ---------------------------
# Images
# ---------------------------
@app.route('/uploads/<filename>')
def view_image(filename):
    return send_from_directory('uploads', filename)
# ---------------------------
# Run Server
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
