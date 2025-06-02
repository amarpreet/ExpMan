from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import os
from tempfile import NamedTemporaryFile

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
    # TODO: Parse, map fields, categorize, and output CSV
    # For now, just return file info
    return {"bank_file": bank_file.filename, "hist_file": hist_file.filename if hist_file else None, "account_name": account_name, "reconciled": reconciled}

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type='text/csv', filename=filename)
