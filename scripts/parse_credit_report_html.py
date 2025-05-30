import os
import json
import openai
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Input and output paths
HTML_PATH = "data/training_clients/client_001/credit_report.html"
OUTPUT_PATH = "data/training_clients/client_001/credit_report.json"

# Load and parse HTML
with open(HTML_PATH, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file.read(), "html.parser")

# Extract <pre> blocks only (main report content)
pre_texts = [tag.get_text() for tag in soup.find_all("pre")]
credit_report_text = "\n".join(pre_texts)

# GPT system prompt
system_prompt = """
You are a data extraction engine trained on credit reports. Based on the raw TransUnion credit report text input (from <pre> blocks), extract this JSON format:
{
  "fico_score": (integer),
  "utilization": (percentage or null),
  "inquiries": [
    {"date": "MM/DD/YY", "subcode": "XXX...", "subname": "Company Name"},
    ...
  ],
  "tradelines": [
    {"creditor": "Name", "opened": "MM/YY", "high_credit": "$X", "balance": "$Y", "mop": "M01", "remarks": "text"},
    ...
  ],
  "derogatories": ["collection", "bankruptcy", ...],
  "collections": [
    {"creditor": "Name", "opened": "MM/YY", "amount": "$X", "remarks": "text", "mop": "O9B"},
    ...
  ],
  "public_records": ["civil judgment", "chapter 7", ...]
}
Return ONLY the JSON. Do not explain anything.
"""

# Call OpenAI
from openai import OpenAI
client = OpenAI(api_key=api_key)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": credit_report_text}
    ],
    temperature=0.2
)

# Extract JSON
parsed_json = response.choices[0].message.content.strip()
with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
    out.write(parsed_json)

print(f"✅ AI-powered credit report parsed and saved to: {OUTPUT_PATH}")
