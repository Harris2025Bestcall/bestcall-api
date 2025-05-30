import os
import pdfplumber
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load OpenAI API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Extract raw text from a PDF
def extract_pdf_text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

# Analyze one PDF's text with GPT-4
def analyze_with_ai(bank_name, text):
    prompt = f"""
You are an expert in auto loan underwriting.

A dealership submitted a client’s credit application to multiple banks. Below is the full decision response from one bank. Extract whether the deal was approved, declined, or conditioned. List all conditions or stipulations if present. Use your best judgment to identify the outcome, even if it's not clearly labeled. Be concise.

Bank: {bank_name}
Decision Text:
{text}

Return JSON like:
{{
  "approved": true/false,
  "conditions": [list of keywords or reasons],
  "raw_text_snippet": "short snippet of decision"
}}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    result = response.choices[0].message.content
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {
            "approved": None,
            "conditions": [],
            "raw_text_snippet": text[:500]
        }

# Process bank decision PDFs in a given folder for a client
def process_all_bank_decisions(client_id: str):
    pdf_dir = f"data/training_clients/{client_id}/actual_bank_decisions"
    output_path = f"data/training_clients/{client_id}/actual_bank_summary.json"

    results = {}
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            bank = filename.replace(".pdf", "").replace("- Copy", "").replace("_", " ").replace("-", " ").title()
            path = os.path.join(pdf_dir, filename)
            text = extract_pdf_text(path)
            print(f"\U0001f9e0 Analyzing: {bank}")
            results[bank] = analyze_with_ai(bank, text)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\u2705 AI-enhanced bank decisions saved to: {output_path}")
    return output_path

# If running standalone
if __name__ == "__main__":
    process_all_bank_decisions("client_001")
