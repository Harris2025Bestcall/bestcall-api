import os
import json
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def extract_from_credit_report(pdf_path: str, client_id: str) -> dict:
    base_path = f"data/training_clients/{client_id}"
    output_path = os.path.join(base_path, "credit_report.json")

    # Extract text
    print("📄 Extracting text from PDF...")
    raw_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            raw_text += page.extract_text() + "\n"

    # Prepare GPT prompt
    print("🧠 Sending to GPT-4 for structuring...")
    prompt = f"""
You are a data extraction assistant. Read the following TransUnion credit report text and return structured JSON like this:

{{
  "fico_score": 574,
  "utilization": null,
  "inquiries": [
    {{"date": "5/27/25", "subcode": "ALA04242956", "subname": "WESTBORNCDJR"}}
  ],
  "tradelines": [
    {{"creditor": "FNWSE/OPPLNS", "opened": "1/20", "high_credit": "$1200", "balance": "$261", "mop": "I09", "remarks": "Unpaid balance charged"}}
  ],
  "collections": [
    {{"creditor": "CREDIT COLL", "opened": "10/23", "amount": "$201", "remarks": "Paid collection", "mop": "O9P"}}
  ],
  "public_records": []
}}

Credit Report Text:
{raw_text[:12000]}
"""

    # Call GPT
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You extract structured data from credit reports in PDF format."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    # Parse output
    try:
        structured = json.loads(response.choices[0].message.content)
    except Exception:
        structured = {"error": "Failed to parse GPT output", "raw_output": response.choices[0].message.content}

    # Save result
    os.makedirs(base_path, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(structured, f, indent=2)

    print(f"✅ Credit report saved to: {output_path}")
    return structured
