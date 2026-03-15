from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import pytesseract
from pytesseract import Output
from PIL import Image
import os
import cv2
import re

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:/Users/padit/appdata/local/programs/Tesseract-OCR/tesseract.exe"


# ---------------------------
# Fallback Amount Detection
# ---------------------------
import re

def extract_amount(text):

    amounts = re.findall(r"\d+\.\d{2}", text)

    if not amounts:
        return None

    # return largest value (usually total)
    amounts = [float(a) for a in amounts]

    return str(max(amounts))



def extract_bottom_total(data):

    n_boxes = len(data["text"])
    candidates = []

    for i in range(n_boxes):

        txt = data["text"][i].strip()
        txt_clean = txt.replace("$", "").replace("₹", "")

        if txt_clean.replace(".", "", 1).isdigit():

            y = data["top"][i]

            candidates.append((float(txt_clean), y))

    if not candidates:
        return None

    # pick value lowest on receipt
    candidates.sort(key=lambda x: x[1], reverse=True)

    return str(candidates[0][0])
# ---------------------------
# Detect Amount aligned with TOTAL
# ---------------------------
def extract_total_aligned(data):
    n_boxes = len(data["text"])

    keywords = [
        "GRAND TOTAL",
        "TOTAL",
        "AMOUNT",
        "BALANCE",
        "DUE",
        "SUBTOTAL",
        "SUB TOTAL"
    ]

    for keyword in keywords:
        for i in range(n_boxes):
            word = data["text"][i].strip().upper()

            if keyword in word:
                total_y = data["top"][i]
                total_x = data["left"][i]

                candidates = []

                for j in range(n_boxes):
                    txt = data["text"][j].strip()

                    txt_clean = txt.replace("$", "").replace("₹", "")

                    if txt_clean.replace(".", "", 1).isdigit():
                        y = data["top"][j]
                        x = data["left"][j]

                        # same horizontal row
                        if abs(y - total_y) < 20 and x > total_x:
                            candidates.append(txt_clean)

                if candidates:
                    return candidates[-1]

    return None

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

    # Image preprocessing
    img = cv2.imread(filepath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    # OCR text
    text = pytesseract.image_to_string(gray)

    # OCR word position data
    data = pytesseract.image_to_data(gray, output_type=Output.DICT)

    # Vendor detection
    vendor_name = text.split("\n")[0].strip().upper()

    amount = extract_total_aligned(data)

    if not amount:
        amount = extract_amount(text)

    if not amount:
        amount = extract_bottom_total(data)

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # check vendor
    c.execute("SELECT * FROM vendor WHERE UPPER(vendor_name)=?", (vendor_name,))
    result = c.fetchone()

    status = "APPROVED" if result else "PENDING"

    # insert receipt
    c.execute(
        "INSERT INTO receipt (vendor_name, image_path, status, user_id, amount) VALUES (?, ?, ?, ?, ?)",
        (vendor_name, filepath, status, user_id, amount)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "vendor": vendor_name,
        "amount": amount,
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

    cursor.execute("SELECT receipt_id, vendor_name, status, user_id, image_path, amount FROM receipt")
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
            "amount": row[5]
        })

    return {"receipts": receipts}


# ---------------------------
# Approve Receipt
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

    cursor.execute(
        "SELECT vendor_name FROM receipt WHERE receipt_id = ?",
        (receipt_id,)
    )

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

    return {"message": "Vendor added to database"}

# ---------------------------
# Delete Receipt
# ---------------------------
@app.route("/delete/<int:receipt_id>", methods=["DELETE"])
def delete_receipt(receipt_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # get image path before deleting
    cursor.execute("SELECT image_path FROM receipt WHERE receipt_id=?", (receipt_id,))
    result = cursor.fetchone()

    if result:
        image_path = result[0]

        # delete database row
        cursor.execute("DELETE FROM receipt WHERE receipt_id=?", (receipt_id,))
        conn.commit()

        # delete image file
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except:
            pass

    conn.close()

    return {"message": "Receipt deleted"}
# ---------------------------
# Serve Uploaded Images
# ---------------------------
@app.route('/uploads/<filename>')
def view_image(filename):
    return send_from_directory('uploads', filename)
# ---------------------------
# Export Receipts to Excel
# ---------------------------
@app.route("/export", methods=["GET"])
def export_receipts():

    import pandas as pd

    conn = sqlite3.connect("database.db")

    df = pd.read_sql_query("SELECT * FROM receipt", conn)

    conn.close()

    file_path = "receipts_export.xlsx"

    df.to_excel(file_path, index=False)

    return send_from_directory(".", file_path, as_attachment=True)

# ---------------------------
# Run Server
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)