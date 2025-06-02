from fastapi import FastAPI, UploadFile, File, Form, Depends, Request, Response, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, shutil, uuid, json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from typing import Optional
import hashlib

# Core scripts
from scripts.parse_credit_app_pdf_ai import extract_from_credit_app
from scripts.parse_credit_report_pdf_ai import extract_from_credit_report
from scripts.predict_approval_gpt import predict_approval
from scripts.predict_approval_from_json import predict_approval as predict_ml
from scripts.train_from_actuals import train_from_actuals
from scripts.analyze_approval_history_ai import summarize_training_log
from scripts.predict_vehicle_match import match_vehicle_to_profile

# Load secrets
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🔧 Initialize FastAPI app
app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# === Auth and session ===
SESSION_COOKIE_NAME = "bestcall_session"
USERS_FILE = "data/users.json"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_current_user(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    users = load_users()
    for user in users:
        if hash_password(user["email"]) == session_id:
            return user
    raise HTTPException(status_code=401, detail="Invalid session")

@app.post("/auth/login")
async def login(response: Response, email: str = Form(...), password: str = Form(...)):
    users = load_users()
    input_hash = hash_password(password)

    print("🔐 Attempting login for:", email)
    print("🔑 Hashed input password:", input_hash)

    for user in users:
        print("📂 Stored user:", user["email"], "| Password hash:", user["password"])
        if user["email"] == email and user["password"] == input_hash:
            print("✅ Match found! Logging in:", email)
            session_id = hash_password(email)
            res = RedirectResponse(url="/client/dashboard", status_code=302)
            res.set_cookie(SESSION_COOKIE_NAME, session_id, httponly=True, max_age=3600)
            return res

    print("❌ Login failed for:", email)
    raise HTTPException(status_code=401, detail="Invalid login")

@app.post("/create_user")
def create_user(email: str = Form(...), password: str = Form(...), name: str = Form(...)):
    users = load_users()
    if any(u["email"] == email for u in users):
        raise HTTPException(status_code=400, detail="User already exists")
    users.append({
        "email": email,
        "password": hash_password(password),
        "name": name,
        "role": "dealer"
    })
    save_users(users)
    return {"status": "User created"}

@app.get("/logout")
def logout():
    res = RedirectResponse("/client/login", status_code=302)
    res.delete_cookie(SESSION_COOKIE_NAME)
    return res

# === Client pages ===
@app.get("/", response_class=HTMLResponse)
def root():
    return {"message": "BestCall AI is live."}

@app.get("/client/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/client/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/client/history", response_class=HTMLResponse)
def history_ui(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/client/inventory", response_class=HTMLResponse)
def inventory_ui(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("inventory.html", {"request": request})

@app.get("/client/results", response_class=HTMLResponse)
def show_results(request: Request, client_id: str, user: dict = Depends(get_current_user)):
    try:
        base = f"data/training_clients/{client_id}"
        with open(f"{base}/predicted_approval_summary.json") as f:
            gpt = json.load(f)
        with open(f"{base}/client_profile.json") as f:
            profile = json.load(f)
        ml = predict_ml(client_id)
        return templates.TemplateResponse("results.html", {
            "request": request,
            "client_id": client_id,
            "gpt_prediction": gpt,
            "ml_prediction": ml,
            "vehicle_match": profile.get("vehicle_match")
        })
    except Exception as e:
        return templates.TemplateResponse("results.html", {
            "request": request,
            "client_id": client_id,
            "gpt_prediction": {"error": str(e)},
            "ml_prediction": {},
            "vehicle_match": None
        })

# === API Routes ===
@app.get("/inventory")
def get_inventory():
    try:
        df = pd.read_csv("data/inventory/cleaned vehicle inventory.csv")
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

@app.get("/history")
def get_history():
    base = "data/training_clients"
    results = []
    for cid in os.listdir(base):
        try:
            with open(f"{base}/{cid}/client_profile.json") as f:
                profile = json.load(f)
            with open(f"{base}/{cid}/predicted_approval_summary.json") as f:
                gpt = json.load(f)
            ml = predict_ml(cid)
            timestamp = datetime.fromtimestamp(os.path.getctime(f"{base}/{cid}/client_profile.json"))
            results.append({
                "client_id": cid,
                "vehicle_match": profile.get("vehicle_match"),
                "gpt_prediction": gpt,
                "ml_prediction": ml,
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M")
            })
        except:
            continue
    return sorted(results, key=lambda x: x["timestamp"], reverse=True)

@app.post("/upload/")
async def upload(
    credit_app: UploadFile = File(...),
    credit_report: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    cid = f"client_{uuid.uuid4().hex[:8]}"
    base = f"data/training_clients/{cid}"
    os.makedirs(base, exist_ok=True)

    with open(os.path.join(base, "credit_app.pdf"), "wb") as f:
        shutil.copyfileobj(credit_app.file, f)
    with open(os.path.join(base, "credit_report.pdf"), "wb") as f:
        shutil.copyfileobj(credit_report.file, f)

    app_data = extract_from_credit_app(os.path.join(base, "credit_app.pdf"), cid)
    report_data = extract_from_credit_report(os.path.join(base, "credit_report.pdf"), cid)
    merged = {"client_id": cid, "application": app_data, "credit_report": report_data}

    try:
        merged["vehicle_match"] = match_vehicle_to_profile(base, supabase)
    except:
        merged["vehicle_match"] = None

    with open(os.path.join(base, "client_profile.json"), "w") as f:
        json.dump(merged, f, indent=2)

    gpt = predict_approval(merged, base)
    with open(os.path.join(base, "predicted_approval_summary.json"), "w") as f:
        json.dump(gpt, f, indent=2)

    return {
        "client_id": cid,
        "gpt_prediction": gpt,
        "ml_prediction": predict_ml(cid),
        "vehicle_match": merged["vehicle_match"],
        "approval_structure": gpt.get("approval_structure", {})
    }

@app.post("/train/")
async def upload_actuals(
    client_id: str = Form(...),
    files: list[UploadFile] = File(...),
    user: dict = Depends(get_current_user)
):
    base = f"data/training_clients/{client_id}/actual_bank_decisions"
    os.makedirs(base, exist_ok=True)
    for i, file in enumerate(files):
        with open(os.path.join(base, f"decision_{i}.pdf"), "wb") as f:
            shutil.copyfileobj(file.file, f)
    return train_from_actuals(client_id)

@app.get("/metrics")
def get_metrics():
    return summarize_training_log()
