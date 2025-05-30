import json
import os
import pandas as pd
from openai import OpenAI

client = OpenAI()

# Load profile
with open("data/training_clients/client_001/full_client_profile.json", "r") as f:
    client_profile = json.load(f)

# Load CSV
df = pd.read_csv("data/bank_decisions_cleaned.csv")
df.fillna("", inplace=True)

# Group banks
banks = df["finance_source"].unique().tolist()
chunk_size = 3  # REDUCED for safe TPM usage

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_bank_summary(bank_name):
    group = df[df["finance_source"] == bank_name]
    return {
        "bank_name": bank_name,
        "apps": len(group),
        "approvals": int((group["decision_type"] == "approved").sum()),
        "approval_rate": round((group["decision_type"] == "approved").mean() * 100, 2),
        "credit_score_range": f"{int(group['credit_score'].min())}–{int(group['credit_score'].max())}",
        "advance_pct_range": f"{int(group['advance_pct'].min())}–{int(group['advance_pct'].max())}"
    }

predictions = []

for chunk in chunk_list(banks, chunk_size):
    bank_data = [get_bank_summary(bank) for bank in chunk]

    prompt = f"""
You are an expert automotive finance underwriter. Given this client profile and a summary of lender behavior, determine which banks are likely to approve the application, which to avoid, and give strategy tips.

Client:
{json.dumps(client_profile, indent=2)}

Lenders:
{json.dumps(bank_data, indent=2)}

Return your answer in JSON format like this:
{{
  "recommended_banks": [{{"bank_name": "...", "reason": "..."}}],
  "banks_to_avoid": [{{"bank_name": "...", "reason": "..."}}],
  "strategy_summary": "..."
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        predictions.append(json.loads(response.choices[0].message.content))
        print(f"✅ GPT response saved for: {', '.join(chunk)}")

    except Exception as e:
        print(f"❌ Error processing chunk {chunk}: {e}")

# Save output
output_path = "data/training_clients/client_001/predicted_approval_summary.json"
with open(output_path, "w") as f:
    json.dump(predictions, f, indent=2)

print(f"\n✅ Final predictions saved to: {output_path}")
