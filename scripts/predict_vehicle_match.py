import os
import json
import pandas as pd

def match_vehicle_to_profile(client_path: str, supabase=None, dealer_id: str = "dealer1") -> dict:
    profile_path = os.path.join(client_path, "client_profile.json")
    if not os.path.exists(profile_path):
        return {"error": "Client profile not found."}

    with open(profile_path, "r") as f:
        profile = json.load(f)

    fico = profile.get("credit_report", {}).get("fico_score", 0)
    income_str = profile.get("application", {}).get("income", {}).get("gross_monthly", "0")
    try:
        income = float(income_str.replace("$", "").replace(",", "").strip())
    except:
        income = 0.0

    # Load inventory
    inventory_path = os.path.join("data", "dealers", dealer_id, "inventory.csv")
    if not os.path.exists(inventory_path):
        return {"error": f"Inventory not found for dealer '{dealer_id}'."}

    try:
        df = pd.read_csv(inventory_path)
    except Exception as e:
        return {"error": f"Failed to read inventory: {str(e)}"}

    # Optional: Filter based on FICO or income range (this is basic logic)
    filtered = df[
        (df.get("min_fico", 0) <= fico) & 
        (df.get("min_income", 0) <= income)
    ].copy()

    if filtered.empty:
        return {"match": None, "reason": "No vehicles met credit/income criteria."}

    # Return best match — could use price, year, or priority score
    best_match = filtered.sort_values(by="price", ascending=True).iloc[0].to_dict()

    return {
        "match": best_match,
        "fico": fico,
        "income": income,
        "inventory_considered": len(filtered)
    }

if __name__ == "__main__":
    result = match_vehicle_to_profile("data/training_clients/client_001", dealer_id="dealer1")
    print(json.dumps(result, indent=2))
