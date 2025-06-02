import streamlit as st
import requests
import urllib.parse

# Helper to show field mapping and output generation UI after upload
def show_field_mapping_and_output(columns, bank_file, account_name, reconciled, form_key, show_mapping, show_output):
    if show_mapping:
        st.write("### Map Required Fields")
        with st.form(form_key):
            date_col = st.selectbox("Select Date Column", columns, key=f"date_col_{form_key}")
            desc_col = st.selectbox("Select Description Column", columns, key=f"desc_col_{form_key}")
            amt_col = st.selectbox("Select Amount Column", columns, key=f"amt_col_{form_key}")
            submitted = st.form_submit_button("Confirm Field Mapping")
            if submitted:
                st.session_state['date_col'] = date_col
                st.session_state['desc_col'] = desc_col
                st.session_state['amt_col'] = amt_col
                st.session_state['mapping_confirmed'] = True
                st.session_state['show_mapping'] = False  # Immediately hide mapping form
                st.session_state['show_output'] = True   # Immediately show output button
                st.rerun()  # Force rerun so the output button appears immediately
                st.success(f"Mapped: Date='{date_col}', Description='{desc_col}', Amount='{amt_col}'")
    if show_output:
        if st.button("Generate Output CSV", key=f"generate_output_{form_key}"):
            payload = {
                "bank_file": bank_file,
                "account_name": account_name,
                "reconciled": reconciled,
                "date_col": st.session_state['date_col'],
                "desc_col": st.session_state['desc_col'],
                "amt_col": st.session_state['amt_col']
            }
            response = requests.post("http://localhost:8000/generate_output/", json=payload)
            if response.status_code == 200:
                output_file = response.json().get("output_file")
                st.success("Output CSV generated!")
                encoded_file = urllib.parse.quote(output_file)
                download_url = f"http://localhost:8000/download/{encoded_file}"
                st.markdown(f"[Download Output CSV]({download_url})")
            else:
                st.error(f"Error generating output: {response.text}")

# Main UI logic
st.title("Expense Tracker")
st.markdown("Upload your bank statement and (optionally) a historical categorization file.")

account_name = st.text_input("Account Name")
reconciled = st.text_input("Reconciled", value="Y")
bank_file = st.file_uploader("Bank Statement File (.csv, .xls, .xlsx)")
hist_file = st.file_uploader("Historical Categorization File (optional)")

# Upload and process button
if st.button("Upload and Process", key="upload_and_process_btn"):
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
            result = response.json()
            st.session_state['bank_file'] = bank_file.name
            st.session_state['account_name'] = account_name
            st.session_state['reconciled'] = reconciled
            st.session_state['columns'] = result.get("columns", [])
            st.session_state['mapping_confirmed'] = False
            st.session_state['show_mapping'] = True
            st.session_state['show_output'] = False
            st.write("### Detected Columns:")
            st.write(result.get("columns", []))
            st.write("### Data Preview:")
            st.dataframe(result.get("preview", []))
        else:
            st.error(f"Error: {response.text}")

# Show mapping form only if needed
if st.session_state.get('columns'):
    # Always get the latest state for show_mapping and show_output
    show_mapping = st.session_state.get('show_mapping', not st.session_state.get('mapping_confirmed', False))
    show_output = st.session_state.get('show_output', st.session_state.get('mapping_confirmed', False))
    show_field_mapping_and_output(
        st.session_state['columns'],
        st.session_state.get('bank_file', ''),
        st.session_state.get('account_name', ''),
        st.session_state.get('reconciled', 'Y'),
        form_key="main_mapping_form",
        show_mapping=show_mapping,
        show_output=show_output
    )
