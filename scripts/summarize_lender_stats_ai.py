import os
import pandas as pd
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load the cleaned CSV file
csv_path = "data/lender_profiles/bank_decisions_cleaned.csv"
df = pd.read_csv(csv_path)

# Convert and clean relevant columns
df["credit_score"] = pd.to_numeric(df["credit_score"], errors="coerce")
df["advance_pct"] = pd.to_numeric(df["advance_pct"], errors="coerce")

# Group by finance source
grouped = df.groupby("finance_source")

summary_text = "# Lender Performance Summary\n\n"

# For each lender, summarize stats
for lender, group in grouped:
    approvals = group[group["decision_type"].str.lower() == "approved"].copy()
    declines = group[group["decision_type"].str.lower() == "declined"].copy()

    # Drop NaN values before min/max
    approval_scores = approvals["credit_score"].dropna()
    decline_scores = declines["credit_score"].dropna()
    approval_advance = approvals["advance_pct"].dropna()
    decline_advance = declines["advance_pct"].dropna()

    prompt = f"""
    Lender: {lender}

    Total applications: {len(group)}
    Approvals: {len(approvals)}
    Declines: {len(declines)}

    Approval Credit Score Range: {approval_scores.min()} - {approval_scores.max()}
    Decline Credit Score Range: {decline_scores.min()} - {decline_scores.max()}

    Approval Advance % Range: {approval_advance.min()} - {approval_advance.max()}
    Decline Advance % Range: {decline_advance.min()} - {decline_advance.max()}

    Based on this, summarize approval trends, decline patterns, and any risk insights.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data analyst summarizing lender decision patterns."},
                {"role": "user", "content": prompt.strip()}
            ],
            temperature=0.3
        )
        summary_text += f"## {lender}\n\n" + response.choices[0].message.content.strip() + "\n\n"
    except Exception as e:
        print(f"❌ Failed to process {lender}: {e}")

# Save the summary
output_path = "data/lender_profiles/bank_patterns_summary.md"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    f.write(summary_text)

print(f"✅ Lender AI summary saved to: {output_path}")
