from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import pytesseract
from pytesseract import Output
import os
import cv2
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:/Users/padit/appdata/local/programs/Tesseract-OCR/tesseract.exe"


# ---------------------------
# DB Helper
# ---------------------------
def get_db():
    return sqlite3.connect("database.db")


# ---------------------------
# Amount Extraction
# ---------------------------
def extract_amount(text):
    amounts = re.findall(r"\d+\.\d{2}", text)
    if not amounts:
        return None
    return str(max([float(a) for a in amounts]))


def extract_bottom_total(data):
    candidates = []

    for i in range(len(data["text"])):
        txt = data["text"][i].strip().replace("$", "").replace("₹", "")

        if txt.replace(".", "", 1).isdigit():
            y = data["top"][i]
            candidates.append((float(txt), y))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[1], reverse=True)
    return str(candidates[0][0])


def extract_total_aligned(data):
    keywords = ["TOTAL", "AMOUNT", "BALANCE", "DUE", "SUBTOTAL"]

    for keyword in keywords:
        for i in range(len(data["text"])):
            word = data["text"][i].strip().upper()

            if keyword in word:
                total_y = data["top"][i]
                total_x = data["left"][i]

                for j in range(len(data["text"])):
                    txt = data["text"][j].strip().replace("$", "").replace("₹", "")

                    if txt.replace(".", "", 1).isdigit():
                        y = data["top"][j]
                        x = data["left"][j]

                        if abs(y - total_y) < 20 and x > total_x:
                            return txt

    return None


# ---------------------------
# Upload Receipt
# ---------------------------
@app.route("/upload", methods=["POST"])
def upload():
    if "receipt" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["receipt"]
    user_id = request.form.get("user_id")
    receipt_date = request.form.get("receipt_date")

    # ✅ fallback to current date
    if not receipt_date:
        receipt_date = datetime.now().strftime("%Y-%m-%d")

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Image preprocessing
    img = cv2.imread(filepath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    # OCR
    text = pytesseract.image_to_string(gray)
    data = pytesseract.image_to_data(gray, output_type=Output.DICT)

    vendor_name = text.split("\n")[0].strip().upper()

    amount = extract_total_aligned(data) or extract_amount(text) or extract_bottom_total(data)

    conn = get_db()
    c = conn.cursor()

    # Check vendor
    c.execute("SELECT * FROM vendor WHERE UPPER(vendor_name)=?", (vendor_name,))
    result = c.fetchone()

    status = "APPROVED" if result else "PENDING"

    # ✅ Insert with date
    c.execute("""
        INSERT INTO receipt 
        (vendor_name, image_path, status, user_id, amount, receipt_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (vendor_name, filepath, status, user_id, amount, receipt_date))

    conn.commit()
    conn.close()

    return jsonify({
        "vendor": vendor_name,
        "amount": amount,
        "status": status,
        "user_id": user_id,
        "receipt_date": receipt_date
    })


# ---------------------------
# Get Receipts
# ---------------------------
@app.route("/receipts", methods=["GET"])
def get_receipts():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT receipt_id, vendor_name, status, user_id, image_path, amount, receipt_date 
        FROM receipt
    """)

    rows = cursor.fetchall()
    conn.close()

    receipts = []
    for row in rows:
        receipts.append({
            "id": row[0],
            "vendor_name": row[1],
            "status": row[2],
            "user_id": row[3],
            "image_path": row[4],
            "amount": row[5],
            "receipt_date": row[6]
        })

    return {"receipts": receipts}


# ---------------------------
# Approve Receipt
# ---------------------------
@app.route("/approve/<int:receipt_id>", methods=["POST"])
def approve_receipt(receipt_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE receipt SET status=? WHERE receipt_id=?",
        ("APPROVED", receipt_id)
    )

    conn.commit()
    conn.close()

    return {"message": "Receipt approved"}


# ---------------------------
# Add Vendor
# ---------------------------
@app.route("/add-vendor/<int:receipt_id>", methods=["POST"])
def add_vendor(receipt_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT vendor_name FROM receipt WHERE receipt_id=?", (receipt_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return {"error": "Receipt not found"}, 404

    vendor_name = result[0]

    cursor.execute(
        "INSERT OR IGNORE INTO vendor (vendor_name, status) VALUES (?, ?)",
        (vendor_name, "APPROVED")
    )

    conn.commit()
    conn.close()

    return {"message": "Vendor added"}


# ---------------------------
# Delete Receipt
# ---------------------------
@app.route("/delete/<int:receipt_id>", methods=["DELETE"])
def delete_receipt(receipt_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT image_path FROM receipt WHERE receipt_id=?", (receipt_id,))
    result = cursor.fetchone()

    if result:
        image_path = result[0]

        cursor.execute("DELETE FROM receipt WHERE receipt_id=?", (receipt_id,))
        conn.commit()

        if os.path.exists(image_path):
            os.remove(image_path)

    conn.close()
    return {"message": "Deleted"}


# ---------------------------
# Serve Images
# ---------------------------
@app.route('/uploads/<filename>')
def view_image(filename):
    return send_from_directory('uploads', filename)


# ---------------------------
# Export Excel
# ---------------------------
@app.route("/export", methods=["GET"])
def export():
    import pandas as pd

    conn = get_db()
    df = pd.read_sql_query("""
        SELECT 
            receipt_id AS ID,
            user_id AS User,
            vendor_name AS Vendor,
            amount AS Amount,
            status AS Status,
            receipt_date AS Date
        FROM receipt
    """, conn)
    conn.close()

    file_path = "receipts_export.xlsx"
    df.to_excel(file_path, index=False)

    return send_from_directory(".", file_path, as_attachment=True)


# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)