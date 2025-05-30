import json
import os

def merge_client_profile(app_data: dict, credit_report: dict, client_id: str = "") -> dict:
    """
    Combines credit app data, credit report data, and optionally actual outcomes
    into a unified profile dictionary. Automatically flattens nested 'application'
    field to prevent prediction issues.

    Args:
        app_data (dict): Parsed credit application, should contain 'application'
        credit_report (dict): Parsed credit report
        client_id (str): Client folder name (e.g., client_001)

    Returns:
        dict: Full merged profile
    """
    # ✅ Flatten the application block so it's not nested under another 'application' key
    merged_profile = {
        "client_id": client_id,
        "application": app_data.get("application", {}),
        "credit_report": credit_report,
        "bank_summary": {},
        "bank_decisions": {}
    }

    if client_id:
        base_path = os.path.join("data", "training_clients", client_id)
        files_to_load = {
            "bank_summary": "actual_bank_summary.json",   # matches UI uploads
            "bank_decisions": "bank_decisions.json"       # optional extended info
        }

        for key, filename in files_to_load.items():
            try:
                file_path = os.path.join(base_path, filename)
                with open(file_path, "r") as f:
                    merged_profile[key] = json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to load {key} from {filename}: {e}")
                merged_profile[key] = {}

    return merged_profile
