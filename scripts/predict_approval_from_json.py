import os
import json
import joblib
import pandas as pd

def predict_approval(client_id: str) -> dict:
    model_path = "models/approval_predictor.pkl"
    profile_path = os.path.join("data", "training_clients", client_id, "client_profile.json")
    
    if not os.path.exists(model_path):
        return {"error": "Trained model not found."}
    if not os.path.exists(profile_path):
        return {"error": f"Client profile not found for {client_id}"}

    with open(profile_path, "r") as f:
        profile = json.load(f)

    # Load model
    model = joblib.load(model_path)

    # Get list of known banks used during training
    bank_codes = pd.read_csv("data/training_dataset.csv")["bank"].astype("category")
    bank_mapping = dict(zip(bank_codes.cat.categories, range(len(bank_codes.cat.categories))))

    # Extract features
    fico = profile.get("credit_report", {}).get("fico_score", 0)
    income_str = profile.get("application", {}).get("income", {}).get("gross_monthly", "0")
    try:
        income = float(income_str.replace("$", "").replace(",", "").strip())
    except:
        income = 0.0

    predictions = []
    for bank, code in bank_mapping.items():
        X = pd.DataFrame([{
            "fico_score": fico,
            "gross_monthly_income": income,
            "bank": code
        }])
        approved = model.predict(X)[0]
        confidence = model.predict_proba(X)[0][1]  # prob of 'True'

        predictions.append({
            "bank": bank,
            "predicted_approval": bool(approved),
            "confidence": round(confidence * 100, 2)
        })

    return {
        "client_id": client_id,
        "predictions": predictions
    }

if __name__ == "__main__":
    result = predict_approval("client_012")  # or any ID you've trained
    print(json.dumps(result, indent=2))
