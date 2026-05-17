# Marine Biotech Vision App Starter

This folder contains a lightweight starter for a React + FastAPI app tailored to your marine biotechnology / vision pipeline.

## Structure

- `backend/` - FastAPI inference API
- `frontend/` - React/Vite UI with a marine-inspired landing page

## Run locally

### One-command launcher from the repo root

```powershell
Set-Location "d:\04_L1_Python_Programming\Data_Science_Ammar\HPLC_GCMS_Fingerprint"
.\run_webapp.bat
```

If you prefer PowerShell, run `./run_webapp.ps1` instead.

### Backend

PowerShell from the repository root:

```powershell
Set-Location "d:\04_L1_Python_Programming\Data_Science_Ammar\HPLC_GCMS_Fingerprint\webapp\backend"
python -m pip install -r requirements.txt
$env:MODEL_PATH = ""
uvicorn main:app --reload --port 8000
```

If you have a serialized model artifact, set `MODEL_PATH` before starting the backend.
The backend root (`http://localhost:8000/`) now redirects to the frontend when it is running.

### Frontend

PowerShell from the repository root:

```powershell
Set-Location "d:\04_L1_Python_Programming\Data_Science_Ammar\HPLC_GCMS_Fingerprint\webapp\frontend"
npm install
npm run dev
```

Set `VITE_API_BASE_URL=http://localhost:8000` if your frontend is not using the default API address.

### Quick start order

1. Start the backend on port `8000`.
2. Start the frontend on the default Vite port `5173`.
3. Open the frontend URL shown in the terminal.

## Notes

- The backend is intentionally lightweight so it can stay low-resource.
- The backend will use a serialized model from `MODEL_PATH` when available, otherwise it falls back to demo predictions.
- The UI is designed for a marine-biotech / research demo and can be extended with charts, upload controls, and model outputs.

## Current UX

- Landing page with marine + vision styling
- Prediction form for quick demo calls
- CSV upload inspector for basic file quality checks
- FastAPI endpoint structure that can later be wired to your trained model
