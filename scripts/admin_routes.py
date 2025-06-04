import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from pathlib import Path
from scripts.generate_bank_summary_from_decisions import generate_bank_summary

router = APIRouter()
BASE_DIR = Path("data")


def save_upload_file(upload_file: UploadFile, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as buffer:
        buffer.write(upload_file.file.read())


# ========== UPLOAD ROUTES ==========

@router.post("/upload-bank-summary")
async def upload_bank_summary(dealer_id: str = Form(...), bank_summary: UploadFile = File(...)):
    print(f"[DEBUG] Upload Bank Summary HIT → dealer_id: {dealer_id}, file: {bank_summary.filename}")
    dealer_path = BASE_DIR / "dealers" / dealer_id / "bank_summary.csv"
    save_upload_file(bank_summary, dealer_path)
    return {"status": "Bank summary uploaded successfully"}


@router.post("/upload-inventory")
async def upload_inventory(dealer_id: str = Form(...), inventory: UploadFile = File(...)):
    print(f"[DEBUG] Upload Inventory HIT → dealer_id: {dealer_id}, file: {inventory.filename}")
    dealer_path = BASE_DIR / "dealers" / dealer_id / "inventory.csv"
    save_upload_file(inventory, dealer_path)
    return {"status": "Inventory uploaded successfully"}


@router.post("/upload-training-example")
async def upload_training_example(
    dealer_id: str = Form(...),
    credit_report: UploadFile = File(...),
    credit_app: UploadFile = File(...)
):
    client_id = f"client_{uuid.uuid4().hex[:6]}"
    client_path = BASE_DIR / "dealers" / dealer_id / "training_clients" / client_id
    save_upload_file(credit_report, client_path / "credit_report.pdf")
    save_upload_file(credit_app, client_path / "credit_app.pdf")
    return {"status": "Training example uploaded", "client_id": client_id}


@router.post("/upload-actual-results")
async def upload_actual_results(
    dealer_id: str = Form(...),
    client_id: str = Form(...),
    actual_result_1: UploadFile = File(None),
    actual_result_2: UploadFile = File(None),
    actual_result_3: UploadFile = File(None),
    actual_result_4: UploadFile = File(None),
    actual_result_5: UploadFile = File(None),
    actual_result_6: UploadFile = File(None),
    actual_result_7: UploadFile = File(None),
    actual_result_8: UploadFile = File(None)
):
    files = [
        actual_result_1, actual_result_2, actual_result_3, actual_result_4,
        actual_result_5, actual_result_6, actual_result_7, actual_result_8
    ]
    client_path = BASE_DIR / "dealers" / dealer_id / "training_clients" / client_id
    for idx, f in enumerate(files, start=1):
        if f is not None:
            save_upload_file(f, client_path / f"actual_result_{idx}.pdf")
    return {"status": "Actual results uploaded successfully", "client_id": client_id}


# ========== SUMMARY GENERATION ROUTES ==========

@router.get("/system-operations/train/{dealer_id}/summary")
async def generate_summary(dealer_id: str):
    try:
        output_path = generate_bank_summary(dealer_id)
        if not output_path or not os.path.exists(output_path):
            raise HTTPException(status_code=404, detail="Summary generation failed.")
        return {"message": "Summary generated successfully", "path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-operations/train/{dealer_id}/summary/preview")
async def preview_summary(dealer_id: str):
    path = f"data/dealers/{dealer_id}/bank_patterns_summary.md"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Summary file not found.")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return Response(content, media_type="text/plain")


# ========== TRAINING PROGRESS ROUTE ==========

@router.get("/system-operations/train/{dealer_id}/progress")
async def get_training_progress(dealer_id: str):
    dealer_path = BASE_DIR / "dealers" / dealer_id / "training_clients"
    if not dealer_path.exists():
        return {"progress": 0, "trained": 0, "target": 50}

    trained_clients = len([d for d in dealer_path.iterdir() if d.is_dir()])
    target = 50  # Customize threshold here
    progress = min(100, int((trained_clients / target) * 100))

    return {
        "progress": progress,
        "trained": trained_clients,
        "target": target
    }
import json

@router.get("/system-operations/train/{dealer_id}/metrics")
async def get_dealer_metrics(dealer_id: str):
    log_path = Path(f"data/dealers/{dealer_id}/training_log.jsonl")

    if not log_path.exists():
        return {
            "total_clients": 0,
            "average_fico": 0,
            "approval_rate": 0
        }

    total_clients = 0
    fico_sum = 0
    approved_count = 0

    with open(log_path, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                fico = entry.get("credit_score", 0)
                approved = entry.get("approved", False)

                total_clients += 1
                fico_sum += fico
                if approved:
                    approved_count += 1
            except Exception:
                continue

    average_fico = int(fico_sum / total_clients) if total_clients > 0 else 0
    approval_rate = int((approved_count / total_clients) * 100) if total_clients > 0 else 0

    return {
        "total_clients": total_clients,
        "average_fico": average_fico,
        "approval_rate": approval_rate
    }
