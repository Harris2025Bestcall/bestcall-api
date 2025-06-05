from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os, shutil, uuid, json, hashlib
from datetime import datetime, timedelta
from jose import JWTError, jwt
from scripts.parse_credit_app_pdf_ai import extract_from_credit_app
from scripts.parse_credit_report_pdf_ai import extract_from_credit_report
from scripts.predict_approval_gpt import predict_approval
from scripts.predict_approval_from_json import predict_approval as predict_ml
from scripts.train_from_actuals import train_from_actuals
from scripts.analyze_approval_history_ai import summarize_training_log, summarize_metrics, summarize_progress

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXP_MINUTES = 60
USERS_FILE = "data/users.json"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Auth utils
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

def get_current_user(authorization: str = Depends(lambda: "Bearer dev-token")):
    # Dev bypass: replace with JWT auth if re-scaling later
    return {"email": "admin@dealer.com"}

# Root + Auth
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

@app.get("/system-operations", response_class=HTMLResponse)
def serve_system_ops(request: Request):
    return templates.TemplateResponse("admin/system_ops.html", {"request": request})

# Upload endpoints (no dealer_id)
@app.post("/upload-inventory")
def upload_inventory(file: UploadFile = File(...)):
    os.makedirs("data/inventory", exist_ok=True)
    with open("data/inventory/cleaned vehicle inventory.csv", "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "Inventory uploaded"}

@app.post("/upload-bank-summary")
def upload_bank_summary(file: UploadFile = File(...)):
    with open("data/bank_decisions_cleaned.csv", "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "Bank summary uploaded"}

@app.post("/upload-training-example")
def upload_training_example(credit_app: UploadFile = File(...), credit_report: UploadFile = File(...)):
    client_id = f"client_{uuid.uuid4().hex[:6]}"
    folder = os.path.join("data/training_clients", client_id)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "credit_app.pdf"), "wb") as f:
        shutil.copyfileobj(credit_app.file, f)
    with open(os.path.join(folder, "credit_report.pdf"), "wb") as f:
        shutil.copyfileobj(credit_report.file, f)
    return {"status": "Training example uploaded", "client_id": client_id}

@app.post("/upload-actual-results")
def upload_actual_results(client_id: str = Form(...), files: list[UploadFile] = File(...)):
    folder = os.path.join("data/training_clients", client_id)
    for i, file in enumerate(files):
        with open(os.path.join(folder, f"bank_result_{i+1}.pdf"), "wb") as f:
            shutil.copyfileobj(file.file, f)
    return {"status": "Bank results uploaded"}

# Trigger Training + Summary
@app.post("/generate-summary")
def generate_summary():
    result = summarize_training_log("data")
    return {"status": "Summary generated", "result": result}

@app.get("/summary-preview")
def get_summary():
    path = "data/lender_profiles/bank_patterns_summary.md"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Summary not found")
    with open(path, "r") as f:
        return HTMLResponse(f.read())

@app.get("/metrics")
def get_metrics():
    return summarize_metrics("data")

@app.get("/progress")
def get_progress():
    return summarize_progress("data")
