from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import pandas as pd
import csv
import openpyxl
import pyexcel as pe
from tempfile import NamedTemporaryFile
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/upload/")
def upload_file(
    bank_file: UploadFile = File(...),
    hist_file: UploadFile = File(None),
    account_name: str = Form(...),
    reconciled: str = Form("Y")
):
    # Save uploaded files
    bank_path = os.path.join(UPLOAD_DIR, bank_file.filename)
    with open(bank_path, "wb") as f:
        f.write(bank_file.file.read())
    hist_path = None
    if hist_file:
        hist_path = os.path.join(UPLOAD_DIR, hist_file.filename)
        with open(hist_path, "wb") as f:
            f.write(hist_file.file.read())

    # --- Step 1: Parse the uploaded bank file and detect columns ---
    try:
        def find_header_row(data, max_scan=10):
            # Find the first row with mostly non-empty, unique values
            for i, row in enumerate(data[:max_scan]):
                non_empty = [cell for cell in row if str(cell).strip() != '']
                if len(non_empty) >= max(3, len(row)//2) and len(set(non_empty)) == len(non_empty):
                    return i
            return 0  # fallback to first row

        if bank_file.filename.lower().endswith(".csv"):
            with open(bank_path, newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            header_row = find_header_row(reader)
            df = pd.DataFrame(reader[header_row+1:], columns=reader[header_row])
        elif bank_file.filename.lower().endswith(".xlsx"):
            wb = openpyxl.load_workbook(bank_path, read_only=True)
            ws = wb.active
            data = list(ws.iter_rows(values_only=True))
            header_row = find_header_row(data)
            df = pd.DataFrame(data[header_row+1:], columns=data[header_row])
        elif bank_file.filename.lower().endswith(".xls"):
            sheet = pe.get_sheet(file_name=bank_path)
            data = sheet.to_array()
            header_row = find_header_row(data)
            df = pd.DataFrame(data[header_row+1:], columns=data[header_row])
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a CSV, XLS, or XLSX file.")
    except Exception as e:
        print(f"Error reading file: {e}")  # Print error to server log
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    # Get column names and a preview (first 5 rows)
    columns = list(df.columns)
    preview = df.head(5).to_dict(orient="records")

    return {
        "bank_file": bank_file.filename,
        "hist_file": hist_file.filename if hist_file else None,
        "account_name": account_name,
        "reconciled": reconciled,
        "columns": columns,
        "preview": preview
    }

class OutputRequest(BaseModel):
    bank_file: str
    account_name: str
    reconciled: str
    date_col: str
    desc_col: str
    amt_col: str

@app.post("/generate_output/")
def generate_output(req: OutputRequest):
    bank_path = os.path.join(UPLOAD_DIR, req.bank_file)
    # Re-read the file using the same logic as before
    try:
        def find_header_row(data, max_scan=10):
            for i, row in enumerate(data[:max_scan]):
                non_empty = [cell for cell in row if str(cell).strip() != '']
                if len(non_empty) >= max(3, len(row)//2) and len(set(non_empty)) == len(non_empty):
                    return i
            return 0
        if req.bank_file.lower().endswith(".csv"):
            with open(bank_path, newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            header_row = find_header_row(reader)
            df = pd.DataFrame(reader[header_row+1:], columns=reader[header_row])
        elif req.bank_file.lower().endswith(".xlsx"):
            wb = openpyxl.load_workbook(bank_path, read_only=True)
            ws = wb.active
            data = list(ws.iter_rows(values_only=True))
            header_row = find_header_row(data)
            df = pd.DataFrame(data[header_row+1:], columns=data[header_row])
        elif req.bank_file.lower().endswith(".xls"):
            sheet = pe.get_sheet(file_name=bank_path)
            data = sheet.to_array()
            header_row = find_header_row(data)
            df = pd.DataFrame(data[header_row+1:], columns=data[header_row])
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a CSV, XLS, or XLSX file.")
    except Exception as e:
        print(f"Error reading file: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    # Prepare output DataFrame
    output = pd.DataFrame()
    # 1. Account Name: fill with the input field value for all rows
    output["Account Name"] = [req.account_name] * len(df)
    # 2. Date: try to parse and format as dd/mm/yyyy
    output["Date"] = pd.to_datetime(df[req.date_col], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
    # 3. Details: leave blank for now (to be filled by categorization later)
    output["Details"] = ""
    # 4. Category: leave blank for now (to be filled by categorization later)
    output["Category"] = ""
    # 5. Notes: description field
    output["Notes"] = df[req.desc_col]
    # 6. Cheque/Check Number: blank
    output["Cheque/Check Number"] = ""
    # 7. Amount: convert to numeric, forcing errors to NaN
    output["Amount"] = pd.to_numeric(df[req.amt_col], errors='coerce')
    # 8. Reconciled: fill with the input field value for all rows
    output["Reconciled"] = [req.reconciled] * len(df)

    # Sort by date ascending
    output = output.sort_values(by="Date")

    # Save the output file as CSV (no header)
    output_file = f"output_{req.account_name}.csv"
    output_file_path = os.path.join(OUTPUT_DIR, output_file)
    output.to_csv(output_file_path, index=False, header=False)

    return {"output_file": output_file}

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, media_type='text/csv', filename=filename)
