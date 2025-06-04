import json
import os
from pathlib import Path

def generate_bank_summary(dealer_id: str) -> str:
    base_dir = Path("data") / "dealers" / dealer_id / "training_clients"
    output_file = Path("data") / "dealers" / dealer_id / "bank_patterns_summary.md"

    summary = {
        "approved_banks": [],
        "declined_banks": [],
        "conditioned_banks": []
    }

    if not base_dir.exists():
        raise FileNotFoundError(f"No training clients found for dealer '{dealer_id}'")

    for client_folder in base_dir.iterdir():
        decision_path = client_folder / "bank_decisions.json"
        if not decision_path.exists():
            continue

        try:
            with open(decision_path, "r") as f:
                data = json.load(f)

            for bank, info in data.items():
                if info.get("approved") is True:
                    summary["approved_banks"].append(bank.strip())
                elif "condition" in str(info).lower():
                    summary["conditioned_banks"].append(bank.strip())
                else:
                    summary["declined_banks"].append(bank.strip())
        except Exception as e:
            print(f"❌ Failed to parse {decision_path}: {e}")

    # Save to markdown
    with open(output_file, "w") as f:
        f.write("# Bank Pattern Summary\n\n")
        f.write("## ✅ Approved Banks\n")
        f.write("\n".join(set(summary["approved_banks"])) + "\n\n")
        f.write("## ⚠️ Conditioned Banks\n")
        f.write("\n".join(set(summary["conditioned_banks"])) + "\n\n")
        f.write("## ❌ Declined Banks\n")
        f.write("\n".join(set(summary["declined_banks"])) + "\n")

    print(f"✅ Bank summary generated for dealer {dealer_id}")
    return str(output_file)
