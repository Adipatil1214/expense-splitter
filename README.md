# Expense Receipt Scanner

This project scans receipts using OCR, extracts expense details, checks the database, and allows the admin to approve or reject the expense.

## Requirements

* Python 3.x
* Tesseract OCR installed

## Install Required Packages

```bash
pip install flask
pip install pytesseract
pip install pillow
pip install opencv-python
pip install mysql-connector-python
```

Or install all together:

```bash
pip install flask pytesseract pillow opencv-python mysql-connector-python
```

## Install Tesseract OCR

Download and install **Tesseract OCR** from the official installer.

Example path after installation (Windows):

```
C:\Program Files\Tesseract-OCR\tesseract.exe
```

## Add Tesseract Path in Python 

Add this line in your Python code(Backend>app.py):

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## Run the Project

```bash
python app.py
```
and run Frontend

```bash
cd frontend
npm run dev
```
The server will start and the receipt scanner will be available locally.
