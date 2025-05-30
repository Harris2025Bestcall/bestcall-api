import os
from scripts.train_from_actuals import train_from_actuals

def batch_train():
    base_dir = "data/training_clients"
    client_folders = sorted(os.listdir(base_dir))

    for folder in client_folders:
        client_path = os.path.join(base_dir, folder)
        if os.path.isdir(client_path) and os.path.exists(os.path.join(client_path, "actual_bank_summary.json")):
            print(f"🔁 Training from: {folder}")
            result = train_from_actuals(folder)
            print(f"✅ {folder} result: {result.get('accuracy', 'N/A')}%")
        else:
            print(f"⏩ Skipped: {folder} (missing actual bank summary)")

if __name__ == "__main__":
    batch_train()
