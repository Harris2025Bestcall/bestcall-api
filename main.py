from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, uuid, json
import pandas as pd

from dotenv import load_dotenv
from supabase import create_client

# Core logic modules
from scripts.parse_credit_app_pdf_ai import extract_from_credit_app
from scripts.parse_credit_report_pdf_ai import extract_from_credit_report
from scripts.predict_approval_gpt import predict_approval
from scripts.predict_approval_from_json import predict_approval as predict_ml
from scripts.train_from_actuals import train_from_actuals
from scripts.analyze_approval_history_ai import summarize_training_log
from scripts.predict_vehicle_match import match_vehicle_to_profile
from utils.security import verify_key  # 🔐 API Key protection

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize FastAPI app with global security
app = FastAPI(dependencies=[Depends(verify_key)])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Health check
@app.get("/")
def root():
    return {"message": "BestCall AI backend is live and secured."}

# ✅ Admin portal UI
@app.get("/admin", response_class=HTMLResponse)
def admin_portal():
    with open("frontend/upload_portal.html", "r") as f:
        return f.read()

# ✅ Client portal UI (NEW)
@app.get("/client", response_class=HTMLResponse)
def client_portal():
    with open("frontend/client.html", "r") as f:
        return f.read()

# ✅ Return inventory from Supabase/CSV
@app.get("/inventory")
def get_inventory():
    try:
        df = pd.read_csv("data/inventory/cleaned vehicle inventory.csv")
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

# ✅ Upload and predict (credit app + report)
@app.post("/upload/")
async def upload_files(
    credit_app: UploadFile = File(...),
    credit_report: UploadFile = File(...),
    bank_summary: UploadFile = File(None),
    bank_detail: UploadFile = File(None),
):
    client_id = f"client_{str(uuid.uuid4())[:8]}"
    base_path = f"data/training_clients/{client_id}"
    os.makedirs(base_path, exist_ok=True)

    # Save PDFs
    app_path = os.path.join(base_path, "credit_app.pdf")
    report_path = os.path.join(base_path, "credit_report.pdf")
    with open(app_path, "wb") as f:
        shutil.copyfileobj(credit_app.file, f)
    with open(report_path, "wb") as f:
        shutil.copyfileobj(credit_report.file, f)

    # Parse content
    app_data = extract_from_credit_app(app_path, client_id)
    report_data = extract_from_credit_report(report_path, client_id)

    merged = {
        "client_id": client_id,
        "application": app_data,
        "credit_report": report_data,
    }

    # Try vehicle match
    try:
        vehicle_match = match_vehicle_to_profile(base_path, supabase)
    except Exception as e:
        print("❌ Vehicle match failed:", e)
        vehicle_match = None

    merged["vehicle_match"] = vehicle_match

    # Save profile
    profile_path = os.path.join(base_path, "client_profile.json")
    with open(profile_path, "w") as f:
        json.dump(merged, f, indent=2)

    # Predict
    gpt_result = predict_approval(merged, base_path)
    with open(os.path.join(base_path, "predicted_approval_summary.json"), "w") as f:
        json.dump(gpt_result, f, indent=2)

    ml_result = predict_ml(client_id)

    return {
        "client_id": client_id,
        "gpt_prediction": gpt_result,
        "ml_prediction": ml_result,
        "vehicle_match": vehicle_match,
        "approval_structure": gpt_result.get("approval_structure", {})
    }

# ✅ Upload actual bank funding decision PDFs
@app.post("/train/")
async def upload_actuals(
    client_id: str = Form(...),
    files: list[UploadFile] = File(...)
):
    base_path = f"data/training_clients/{client_id}/actual_bank_decisions"
    os.makedirs(base_path, exist_ok=True)

    for i, file in enumerate(files):
        save_path = os.path.join(base_path, f"decision_{i}.pdf")
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

    return train_from_actuals(client_id)

# ✅ View current model performance
@app.get("/metrics")
def get_metrics():
    return summarize_training_log()
