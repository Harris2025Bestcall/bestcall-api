import os
import json
import csv

def load_client_profile(client_id):
    profile_path = os.path.join("data", "training_clients", client_id, "client_profile.json")
    if not os.path.exists(profile_path):
        return None
    with open(profile_path, "r") as f:
        return json.load(f)

def build_training_dataset():
    log_path = "data/training_log.jsonl"
    output_csv = "data/training_dataset.csv"
    rows = []

    if not os.path.exists(log_path):
        print("❌ training_log.jsonl not found.")
        return

    with open(log_path, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                client_id = entry["client_id"]
                profile = load_client_profile(client_id)
                if not profile:
                    continue

                fico = profile.get("credit_report", {}).get("fico_score", "")
                income_str = profile.get("application", {}).get("income", {}).get("gross_monthly", "0")
                try:
                    income = float(income_str.replace("$", "").replace(",", "").strip())
                except:
                    income = 0.0

                for detail in entry.get("details", []):
                    rows.append({
                        "client_id": client_id,
                        "bank": detail["bank"],
                        "fico_score": fico,
                        "gross_monthly_income": income,
                        "predicted_approved": detail.get("predicted", ""),
                        "actual_approved": detail.get("actual", ""),
                        "match": detail.get("match", False)
                    })
            except Exception as e:
                print(f"⚠️ Failed to parse line: {e}")

    # Save to CSV
    os.makedirs("data", exist_ok=True)
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Training dataset saved to: {output_csv} ({len(rows)} rows)")

if __name__ == "__main__":
    build_training_dataset()
