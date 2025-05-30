import os
import json
import pandas as pd

def match_vehicle_to_profile(client_folder: str):
    profile_path = os.path.join(client_folder, "client_profile.json")
    inventory_path = "data/inventory/cleaned vehicle inventory.csv"

    # Load client profile
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Client profile not found at {profile_path}")
    
    with open(profile_path, "r") as f:
        profile = json.load(f)

    # Load inventory
    if not os.path.exists(inventory_path):
        raise FileNotFoundError("Inventory file not found.")
    
    inventory = pd.read_csv(inventory_path)

    # Extract prediction structure
    predicted = profile.get("predicted_structure", {})
    if not predicted:
        return None

    approval_amount = predicted.get("predicted_approval_amount", 0)
    max_ltv = predicted.get("max_ltv", 0)
    term = predicted.get("term_months", 0)

    # Filter inventory within approval limits
    matches = []
    for _, row in inventory.iterrows():
        retail_value = row.get("retail_value", 0)
        dealer_cost = row.get("dealer_cost", 0)

        if retail_value <= approval_amount:
            ltv = (retail_value / approval_amount) * 100
            estimated_gross = retail_value - dealer_cost
            matches.append({
                "year": row.get("year"),
                "make": row.get("make"),
                "model": row.get("model"),
                "retail_value": retail_value,
                "dealer_cost": dealer_cost,
                "suggested_LTV": f"{ltv:.1f}%",
                "estimated_gross": estimated_gross
            })

    if not matches:
        return None

    # Sort by estimated profit descending
    matches.sort(key=lambda x: x["estimated_gross"], reverse=True)

    best_match = matches[0]
    return best_match
