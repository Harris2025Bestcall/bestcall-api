import os
import json
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

from pathlib import Path

data_dir = Path("data/training_clients")
output_dir = Path("data/output_profiles")
output_dir.mkdir(parents=True, exist_ok=True)

def extract_profile_with_gpt(raw_text):
    prompt = f"""
You are an AI assistant helping extract structured client profile data from the following credit application and credit report snapshot:

---
{raw_text}
---

Return a JSON object with the following format:
{{
  "client_id": "client_XXX",
  "application": {{
    "name": "",
    "dob": "",
    "ssn": "",
    "phone": "",
    "email": "",
    "residence": {{
      "address": "",
      "type": "",
      "monthly_rent": "",
      "time_at_residence": ""
    }},
    "employment": {{
      "employer": "",
      "title": "",
      "status": "",
      "employer_phone": "",
      "time_at_job": ""
    }},
    "income": {{
      "gross_monthly": "",
      "other_income": ""
    }}
  }}
}}
"""

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{ "role": "user", "content": prompt }],
        temperature=0
    )
    return json.loads(response.choices[0].message.content)

for client_folder in data_dir.iterdir():
    if not client_folder.is_dir():
        continue

    credit_app_path = client_folder / "credit_app.json"
    credit_report_path = client_folder / "credit_report.html"
    bank_decision_path = client_folder / "bank_decision_summary.html"

    if not (credit_app_path.exists() or credit_report_path.exists()):
        print(f"⚠️ Skipping {client_folder.name}: missing required inputs")
        continue

    print(f"🔍 Processing: {client_folder.name}")

    combined_text = ""
    if credit_app_path.exists():
        with open(credit_app_path, "r", encoding="utf-8") as f:
            combined_text += f"\n\n[Credit Application]\n{f.read()}"

    if credit_report_path.exists():
        with open(credit_report_path, "r", encoding="utf-8") as f:
            combined_text += f"\n\n[Credit Report]\n{f.read()}"

    if bank_decision_path.exists():
        with open(bank_decision_path, "r", encoding="utf-8") as f:
            combined_text += f"\n\n[Bank Decisions]\n{f.read()}"

    try:
        structured = extract_profile_with_gpt(combined_text)
        structured["client_id"] = client_folder.name
        output_path = output_dir / f"{client_folder.name}.json"
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(structured, out, indent=2)
        print(f"✅ Saved: {output_path}")
    except Exception as e:
        print(f"❌ Error processing {client_folder.name}: {e}")
