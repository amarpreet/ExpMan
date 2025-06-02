import streamlit as st
import requests

st.title("Expense Tracker")

st.markdown("Upload your bank statement and (optionally) a historical categorization file.")

account_name = st.text_input("Account Name")
reconciled = st.text_input("Reconciled", value="Y")
bank_file = st.file_uploader("Bank Statement File (.csv, .xls, .xlsx)")
hist_file = st.file_uploader("Historical Categorization File (optional)")

if st.button("Upload and Process"):
    if not bank_file or not account_name:
        st.error("Please provide the required fields and upload a bank file.")
    else:
        files = {"bank_file": (bank_file.name, bank_file, bank_file.type)}
        if hist_file:
            files["hist_file"] = (hist_file.name, hist_file, hist_file.type)
        data = {"account_name": account_name, "reconciled": reconciled}
        response = requests.post("http://localhost:8000/upload/", files=files, data=data)
        if response.status_code == 200:
            st.success("File uploaded and processed.")
            st.json(response.json())
        else:
            st.error(f"Error: {response.text}")
