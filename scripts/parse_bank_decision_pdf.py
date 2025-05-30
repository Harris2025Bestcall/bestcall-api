import os
import pdfplumber
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load OpenAI API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths
client_folder = Path("data/training_clients/client_001")
output_file = client_folder / "bank_decisions.json"

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

# Initialize dictionary
bank_decisions = {}

# GPT system prompt
system_prompt = """
You are a loan underwriting assistant. Read each auto loan decision summary below and extract:
{
  "bank": "Bank name",
  "decision": "Approved / Declined / Conditioned / Counteroffer",
  "amount": (number or null),
  "term": (in months, or null),
  "tier": (e.g. "A", "B", "C", or number like 9),
  "rate": (APR percentage if available),
  "stipulations": [list of conditions],
  "reasoning": "One-sentence explanation for the decision."
}
Return only valid JSON. No commentary.
"""

# Loop through all decision PDFs
for file in client_folder.iterdir():
    if file.suffix == ".pdf" and "decision" in file.stem.lower():
        bank_name = (
            file.stem.replace("_decision", "")
            .replace("- Copy", "")
            .replace("_", " ")
            .replace("-", " ")
            .title()
        )
        pdf_text = extract_text_from_pdf(file)

        # Send to GPT
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": pdf_text}
                ],
                temperature=0.2
            )
            decision_json = response.choices[0].message.content.strip()
            bank_decisions[bank_name] = json.loads(decision_json)
        except Exception as e:
            print(f"❌ Error parsing {bank_name}: {e}")
            continue

# Save result
with open(output_file, "w") as f:
    json.dump(bank_decisions, f, indent=2)

print(f"✅ AI-powered bank decisions saved to: {output_file}")
