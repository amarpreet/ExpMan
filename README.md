# Expense Tracker Project Structure

- requirements.txt  # Python dependencies
- main.py           # FastAPI backend for file upload, processing, and download
- app.py            # Streamlit frontend for user interaction
- uploads/          # Directory for uploaded files (auto-created)
- outputs/          # Directory for output CSV files (auto-created)
- Requirments.txt   # Project requirements and documentation

## How to Run

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Start the FastAPI backend:
   ```
   uvicorn main:app --reload
   ```
3. In a new terminal, start the Streamlit frontend:
   ```
   streamlit run app.py
   ```
4. Open the Streamlit UI in your browser (usually http://localhost:8501)

## Next Steps
- Implement file parsing, field mapping, and categorization logic in `main.py`.
- Enhance the Streamlit UI for field mapping and output download.
- Add error handling and validation as per requirements.
