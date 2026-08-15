# FacilityOps AI Dashboard

Streamlit app for predictive maintenance, work orders, and preventive schedules.

## Documentation

For the complete technical report, see [Project Documentation](PROJECT_DOCUMENTATION.md) and the [PDF report](FacilityOps_Project_Documentation_Final.pdf).

## Run in VS Code

1. Open this folder in VS Code: **File → Open Folder**
2. Open a terminal in VS Code (`Ctrl + `` `)
3. Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

5. Start the app:

```powershell
streamlit run app.py
```

6. Open the URL shown in the terminal (usually http://localhost:8501)

## Notes

- Python 3.10+ recommended
- Data is stored locally in the `data/` folder
- Ollama is optional (only for AI briefing features)
