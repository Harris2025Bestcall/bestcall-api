import json
import os
from openai import OpenAI
from datetime import datetime

def predict_approval(profile: dict, client_folder: str) -> dict:
    structure = profile.get("predicted_structure", {})
    vehicle_match = profile.get("vehicle_match", None)

    prompt = f"""You are a dealership finance assistant. Based on the predicted credit profile and structure, recommend the best course of action to submit the deal for approval.

📄 Approval Structure:
- Estimated Approval Amount: ${structure.get("predicted_approval_amount", "N/A")}
- Max LTV: {structure.get("max_ltv", "N/A")}
- Term: {structure.get("term_months", "N/A")} months
- Tier Suggestion: {structure.get("credit_tier", "N/A")}
"""

    if isinstance(vehicle_match, dict):
        prompt += f"""
🚗 Suggested Vehicle Match:
- {vehicle_match['year']} {vehicle_match['make']} {vehicle_match['model']}
- Retail Value: ${vehicle_match['retail_value']}
- Suggested LTV: {vehicle_match['suggested_LTV']}
- Estimated Gross Profit: ${vehicle_match['estimated_gross']:.2f}
"""
    else:
        prompt += "\n⚠️ No vehicle in current inventory meets the approval structure."

    prompt += "\n💡 Please summarize this deal recommendation in plain English for the dealership rep."

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful dealership finance assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    summary_text = response.choices[0].message.content.strip()

    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "approval_structure": structure,
        "vehicle_match": vehicle_match,
        "recommendation_summary": summary_text
    }

    # Save to file
    output_path = os.path.join(client_folder, "predicted_approval_summary.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print("✅ GPT approval summary created with vehicle match integration.")
    return result
