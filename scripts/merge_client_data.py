import json
import os

def merge_client_profile(client_id: str):
    base_path = f"data/training_clients/{client_id}"
    app_path = os.path.join(base_path, "credit_app.json")
    report_path = os.path.join(base_path, "credit_report.json")
    output_path = os.path.join(base_path, "client_profile.json")

    try:
        with open(app_path, "r") as f:
            app_data = json.load(f)
    except FileNotFoundError:
        app_data = {}

    try:
        with open(report_path, "r") as f:
            report_data = json.load(f)
    except FileNotFoundError:
        report_data = {}

    merged = {
        "client_id": client_id,
        "application": app_data.get("application", {}),
        "credit_report": report_data
    }

    os.makedirs(base_path, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(merged, f, indent=2)

    print(f"✅ Merged client profile saved to: {output_path}")
    return merged
