import pandas as pd
import os

def summarize_training_log(dealer_id: str) -> str:
    """
    Reads the dealer's cleaned bank decision CSV, summarizes approval patterns,
    and writes a markdown summary file. Returns the path to the summary file.
    """
    input_path = f"data/{dealer_id}/bank_decisions_cleaned.csv"
    output_path = f"data/{dealer_id}/bank_patterns_summary.md"

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No cleaned bank decisions found at {input_path}")

    df = pd.read_csv(input_path)

    # Count decisions by type
    decision_counts = df["decision_type"].value_counts().to_dict()
    top_banks = df["finance_source"].value_counts().head(5).to_dict()
    avg_credit_score = round(df["credit_score"].dropna().astype(float).mean(), 1)

    lines = [
        f"# Bank Pattern Summary for Dealer `{dealer_id}`\n",
        f"**Total Applications:** {len(df)}",
        f"**Average Credit Score:** {avg_credit_score}\n",
        "## Decision Breakdown:",
    ]
    for decision, count in decision_counts.items():
        lines.append(f"- {decision}: {count}")

    lines.append("\n## Top 5 Lenders by Volume:")
    for lender, count in top_banks.items():
        lines.append(f"- {lender}: {count} apps")

    # Save to Markdown file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path
