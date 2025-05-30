import json
import os

client_id = "client_001"
base_path = f"data/training_clients/{client_id}"
decision_file = os.path.join(base_path, "bank_decisions.json")
summary_file = os.path.join(base_path, "bank_decision_summary.json")

try:
    with open(decision_file, "r") as f:
        data = json.load(f)

    summary = {
        "approved_banks": [],
        "declined_banks": [],
        "conditioned_banks": []
    }

    for bank, info in data.items():
        if info.get("approved") is True:
            summary["approved_banks"].append(bank.strip())
        elif "condition" in bank.lower() or "condition" in str(info).lower():
            summary["conditioned_banks"].append(bank.strip())
        else:
            summary["declined_banks"].append(bank.strip())

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Repaired summary saved to: {summary_file}")
except Exception as e:
    print(f"❌ Failed to generate summary: {e}")
