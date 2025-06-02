from fastapi import FastAPI, UploadFile, File, Form, Depends, Request, Response, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, shutil, uuid, json, hashlib
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
from jose import JWTError, jwt
from typing import Optional

from scripts.parse_credit_app_pdf_ai import extract_from_credit_app
from scripts.parse_credit_report_pdf_ai import extract_from_credit_report
from scripts.predict_approval_gpt import predict_approval
from scripts.predict_approval_from_json import predict_approval as predict_ml
from scripts.train_from_actuals import train_from_actuals
from scripts.analyze_approval_history_ai import summarize_training_log
from scripts.predict_vehicle_match import match_vehicle_to_profile

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "your-very-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXP_MINUTES = 60

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

USERS_FILE = "data/users.json"

# -------------------- AUTH HELPERS --------------------
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

def create_token(data: dict):
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(authorization: str = Header(...)):
    try:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=403, detail="Invalid auth scheme")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        users = load_users()
        for user in users:
            if user["email"] == email:
                return user
        raise HTTPException(status_code=401, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# -------------------- ROUTES --------------------

@app.get("/")
def root():
    return JSONResponse(content={"message": "BestCall AI is live."})

@app.post("/auth/login")
async def login(email: str = Form(...), password: str = Form(...)):
    users = load_users()
    hashed = hash_password(password)
    for user in users:
        if user["email"] == email and user["password"] == hashed:
            token = create_token({"sub": email})
            return {"access_token": token, "token_type": "bearer"}
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

@app.get("/client/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/client/dashboard", response_class=HTMLResponse)
def serve_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/client/history", response_class=HTMLResponse)
def serve_history(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/client/inventory", response_class=HTMLResponse)
def serve_inventory(request: Request):
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
async def upload(credit_app: UploadFile = File(...), credit_report: UploadFile = File(...), user: dict = Depends(get_current_user)):
    cid = f"client_{uuid.uuid4().hex[:8]}"
    base = f"data/training_clients/{cid}"
    os.makedirs(base, exist_ok=True)
    app_path = os.path.join(base, "credit_app.pdf")
    rep_path = os.path.join(base, "credit_report.pdf")
    with open(app_path, "wb") as f: shutil.copyfileobj(credit_app.file, f)
    with open(rep_path, "wb") as f: shutil.copyfileobj(credit_report.file, f)
    app_data = extract_from_credit_app(app_path, cid)
    report_data = extract_from_credit_report(rep_path, cid)
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
async def upload_actuals(client_id: str = Form(...), files: list[UploadFile] = File(...), user: dict = Depends(get_current_user)):
    base = f"data/training_clients/{client_id}/actual_bank_decisions"
    os.makedirs(base, exist_ok=True)
    for i, file in enumerate(files):
        with open(os.path.join(base, f"decision_{i}.pdf"), "wb") as f:
            shutil.copyfileobj(file.file, f)
    return train_from_actuals(client_id)

@app.get("/metrics")
def get_metrics():
    return summarize_training_log()

# ---- Admin System Ops ----
@app.get("/system-operations", response_class=HTMLResponse)
def system_ops_home(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("admin/system_ops.html", {"request": request})

@app.get("/system-operations/performance", response_class=HTMLResponse)
def system_ops_performance(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("admin/ai_performance.html", {"request": request})

@app.get("/system-operations/team", response_class=HTMLResponse)
def system_ops_team(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("admin/team_management.html", {"request": request})

@app.get("/system-operations/security", response_class=HTMLResponse)
def system_ops_security(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("admin/security_access.html", {"request": request})

@app.get("/system-operations/dealers", response_class=HTMLResponse)
def system_ops_dealers(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("admin/dealership_portals.html", {"request": request})

@app.get("/system-operations/settings", response_class=HTMLResponse)
def system_ops_settings(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("admin/system_settings.html", {"request": request})

@app.get("/admin/performance/data")
def get_ai_performance_logs(user: dict = Depends(get_current_user)):
    log_path = "data/training_log.jsonl"
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r") as f:
        lines = f.readlines()
    return [json.loads(line.strip()) for line in lines]
