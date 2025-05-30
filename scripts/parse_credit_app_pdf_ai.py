import os
import json
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def extract_from_credit_app(pdf_path: str, client_id: str) -> dict:
    base_path = f"data/training_clients/{client_id}"
    output_path = os.path.join(base_path, "credit_app.json")

    print("📄 Extracting text from Credit App PDF...")
    raw_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            raw_text += page.extract_text() + "\n"

    prompt = f"""
You are an assistant that extracts dealership credit applications. Parse the following credit app into structured JSON format:

{{
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

Credit Application:
--- START ---
{raw_text[:12000]}
--- END ---
"""

    print("🧠 Sending credit app to GPT-4...")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You extract dealership credit app data into JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    try:
        structured = json.loads(response.choices[0].message.content)
    except Exception:
        structured = {
            "error": "Failed to parse GPT output",
            "raw_output": response.choices[0].message.content
        }

    os.makedirs(base_path, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(structured, f, indent=2)

    print(f"✅ Credit application saved to: {output_path}")
    return structured
