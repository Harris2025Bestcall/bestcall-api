import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client with API key
client = OpenAI(api_key=api_key)

# Input: Raw OCR text file path
OCR_TEXT_PATH = "ocr_output.txt"
# Output: Parsed JSON structure
OUTPUT_PATH = "data/training_clients/client_001/credit_app.json"

# Read OCR'd text
with open(OCR_TEXT_PATH, "r", encoding="utf-8") as file:
    ocr_text = file.read()

# GPT-4 Prompt Template
prompt = f"""
You are an intelligent OCR assistant. Extract the following structured fields from the messy text input provided below.

Correct common OCR mistakes like missing '@' in email addresses, numbers misread as letters, and reversed names. Ensure the name is properly ordered as First Last. Validate that date of birth is reasonable (e.g. no one born in 1902 is applying for credit). Verify gross monthly income is realistic and distinct from other income.

Extract and format the result into this JSON structure:
{{
  "full_name": "",
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
---
OCR TEXT:
{ocr_text}
"""

# Use the OpenAI client to call the ChatCompletion endpoint
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You extract structured data from OCR documents."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.2
)

# Extract content and save to file
parsed_json = response.choices[0].message.content.strip()

try:
    parsed_data = json.loads(parsed_json)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as out_file:
        json.dump(parsed_data, out_file, indent=2)
    print("✅ Parsed data saved to:", OUTPUT_PATH)
except json.JSONDecodeError as e:
    print("❌ Failed to parse GPT output as JSON:", e)
    print(parsed_json)
