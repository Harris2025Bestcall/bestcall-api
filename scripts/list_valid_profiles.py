import os
import json

INPUT_DIR = "data/output_profiles"

def is_valid_profile(profile):
    required_sections = ["application", "credit_report", "bank_decision"]
    return all(section in profile and profile[section] for section in required_sections)

def list_valid_profiles():
    print("🔍 Checking for valid profiles...\n")
    count = 0
    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(INPUT_DIR, filename)
        with open(path, "r") as f:
            try:
                profile = json.load(f)
                if is_valid_profile(profile):
                    print(f"✅ Valid: {filename}")
                    count += 1
                else:
                    print(f"❌ Invalid: {filename} — missing sections")
            except json.JSONDecodeError:
                print(f"⚠️ Failed to parse: {filename}")
    print(f"\n📦 Total valid profiles: {count}")

if __name__ == "__main__":
    list_valid_profiles()
