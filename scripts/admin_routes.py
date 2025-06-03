import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form
from pathlib import Path

router = APIRouter()
BASE_DIR = Path("data")


def save_upload_file(upload_file: UploadFile, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as buffer:
        buffer.write(upload_file.file.read())


@router.post("/upload-bank-summary")
async def upload_bank_summary(dealer_id: str = Form(...), bank_summary: UploadFile = File(...)):
    dealer_path = BASE_DIR / dealer_id / "bank_summary.csv"
    save_upload_file(bank_summary, dealer_path)
    return {"status": "Bank summary uploaded successfully"}


@router.post("/upload-inventory")
async def upload_inventory(dealer_id: str = Form(...), inventory: UploadFile = File(...)):
    dealer_path = BASE_DIR / dealer_id / "inventory.csv"
    save_upload_file(inventory, dealer_path)
    return {"status": "Inventory uploaded successfully"}


@router.post("/upload-training-example")
async def upload_training_example(
    dealer_id: str = Form(...),
    credit_report: UploadFile = File(...),
    credit_app: UploadFile = File(...)
):
    client_id = f"client_{uuid.uuid4().hex[:6]}"
    client_path = BASE_DIR / dealer_id / "training_clients" / client_id
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
    client_path = BASE_DIR / dealer_id / "training_clients" / client_id
    for idx, f in enumerate(files, start=1):
        if f is not None:
            save_upload_file(f, client_path / f"actual_result_{idx}.pdf")
    return {"status": "Actual results uploaded successfully", "client_id": client_id}
