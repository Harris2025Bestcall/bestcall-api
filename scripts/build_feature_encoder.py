import os
import json
from pathlib import Path

INPUT_DIR = Path("data/output_profiles")
ENCODER_PATH = Path("models/feature_encoder.json")

CATEGORICAL_FIELDS = [
    "application.job_title",
    "application.employment_type",
    "application.residence_type",
    "credit_report.derogatories",
    "bank_decision.lender"
]

def flatten_json(nested_json, prefix=""):
    """Flattens nested dictionary keys (dot notation)."""
    out = {}
    for k, v in nested_json.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten_json(v, full_key))
        elif isinstance(v, list):
            out[full_key] = v
        else:
            out[full_key] = str(v)
    return out

def collect_field_values():
    """Collect unique values for each categorical field."""
    field_values = {field: set() for field in CATEGORICAL_FIELDS}

    for file in INPUT_DIR.glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)
            flat = flatten_json(data)
            for field in CATEGORICAL_FIELDS:
                val = flat.get(field)
                if isinstance(val, list):
                    field_values[field].update(val)
                elif val:
                    field_values[field].add(val)
    return field_values

def build_encoder_map(values_dict):
    """Convert sets of values to indexed dictionaries."""
    return {field: {val: idx for idx, val in enumerate(sorted(values))} for field, values in values_dict.items()}

if __name__ == "__main__":
    print("🔍 Scanning profiles to build encoder...")
    values = collect_field_values()
    encoder = build_encoder_map(values)
    
    with open(ENCODER_PATH, "w") as f:
        json.dump(encoder, f, indent=2)

    print(f"✅ Feature encoder saved to {ENCODER_PATH}")
