import json
import os
from datetime import datetime

def train_from_actuals(client_id: str) -> dict:
    base_path = os.path.join("data", "training_clients", client_id)
    actual_path = os.path.join(base_path, "actual_bank_summary.json")
    prediction_path = os.path.join(base_path, "predicted_approval_summary.json")

    # Handle missing files
    if not os.path.exists(actual_path) or not os.path.exists(prediction_path):
        return {
            "error": "Missing required data",
            "missing_actual": not os.path.exists(actual_path),
            "missing_prediction": not os.path.exists(prediction_path)
        }

    with open(actual_path, "r") as f:
        actual = json.load(f)
    with open(prediction_path, "r") as f:
        predicted = json.load(f)

    # Convert to lookup dicts
    actual_banks = {entry["bank"].lower(): entry for entry in actual}
    predicted_banks = {entry["bank"].lower(): entry for entry in predicted.get("predictions", [])}

    # Compare
    matches = []
    match_count = 0
    total = 0

    for bank, prediction in predicted_banks.items():
        total += 1
        actual_entry = actual_banks.get(bank)
        if actual_entry:
            match = prediction.get("approved", True) == actual_entry.get("approved", False)
            matches.append({
                "bank": bank,
                "predicted": prediction.get("approved", True),
                "actual": actual_entry.get("approved", False),
                "match": match
            })
            if match:
                match_count += 1

    accuracy = round(match_count / total * 100, 2) if total else 0
    result = {
        "client_id": client_id,
        "timestamp": datetime.utcnow().isoformat(),
        "matched": match_count,
        "total": total,
        "accuracy": f"{accuracy}%",
        "details": matches
    }

    # ✅ Append to learning log
    log_path = os.path.join("data", "training_log.jsonl")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as log_file:
        log_file.write(json.dumps(result) + "\n")

    return result
