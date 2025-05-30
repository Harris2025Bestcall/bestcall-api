import os
import json
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Load HTML
HTML_PATH = "data/training_clients/client_001/bank_decision_summary.html"
OUTPUT_PATH = "data/training_clients/client_001/bank_decision_summary.json"
with open(HTML_PATH, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# Extract only visible text
report_text = soup.get_text("\n")

# Prompt for GPT
system_prompt = """
You are a data extraction assistant for automotive finance. Based on a RouteOne bank decision summary, extract a list of all lender decisions in this format:
[
  {
    "bank": "Bank Name",
    "decision": "Approved/Declined/Conditional",
    "amount": 27000,  # if shown
    "term": 72         # if shown
  },
  ...
]
Return ONLY valid JSON. Do not include explanations.
"""

# Call GPT
from openai import OpenAI
client = OpenAI(api_key=api_key)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": report_text}
    ],
    temperature=0.2
)

# Save output
parsed_json = response.choices[0].message.content.strip()
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(parsed_json)

print(f"✅ AI-powered bank decision summary saved to: {OUTPUT_PATH}")
