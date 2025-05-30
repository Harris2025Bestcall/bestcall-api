import os
import json
from scripts.parse_credit_app_pdf import parse_credit_app_pdf
from scripts.parse_credit_report_html import parse_credit_report_html
from scripts.parse_bank_decision_html import parse_bank_decision_html

def process_all_clients():
    input_dir = "data/training_clients"
    output_dir = "data/output_profiles"
    os.makedirs(output_dir, exist_ok=True)

    for client_id in os.listdir(input_dir):
        client_path = os.path.join(input_dir, client_id)
        if not os.path.isdir(client_path):
            continue

        print(f"📂 Processing: {client_id}")

        credit_app_path = os.path.join(client_path, "credit_app.json")
        credit_report_path = os.path.join(client_path, "credit_report.html")
        bank_decision_path = os.path.join(client_path, "bank_decision_summary.html")

        application = {}
        credit_report = {}
        bank_decision = []

        if os.path.exists(credit_app_path):
            with open(credit_app_path, "r", encoding="utf-8") as f:
                application = json.load(f).get("application", {})
        else:
            print("⚠️ Missing credit_app.json")

        if os.path.exists(credit_report_path):
            print("🔍 Parsing credit_report.html...")
            credit_report = parse_credit_report_html(credit_report_path)
        else:
            print("⚠️ Missing credit_report.html")

        if os.path.exists(bank_decision_path):
            print("🔍 Parsing bank_decision_summary.html...")
            bank_decision = parse_bank_decision_html(bank_decision_path)
        else:
            print("⚠️ Missing bank_decision_summary.html")

        if not application or not credit_report:
            print(f"❌ Incomplete data — skipping save for {client_id}")
            continue

        profile = {
            "client_id": client_id,
            "application": application,
            "credit_report": credit_report,
            "bank_decision": bank_decision
        }

        output_path = os.path.join(output_dir, f"{client_id}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        print(f"✅ Saved structured profile: {output_path}")

def parse_client_folder(folder_path):
    credit_app_path = os.path.join(folder_path, "credit_app.json")
    credit_report_path = os.path.join(folder_path, "credit_report.html")
    bank_decision_path = os.path.join(folder_path, "bank_decision_summary.html")

    application = json.load(open(credit_app_path, "r", encoding="utf-8")) if os.path.exists(credit_app_path) else {}
    credit_report = parse_credit_report_html(credit_report_path) if os.path.exists(credit_report_path) else {}
    bank_decision = parse_bank_decision_html(bank_decision_path) if os.path.exists(bank_decision_path) else []

    return {
        "client_id": os.path.basename(folder_path),
        "application": application.get("application", {}),
        "credit_report": credit_report,
        "bank_decision": bank_decision
    }

if __name__ == "__main__":
    process_all_clients()
