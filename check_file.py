import os

path = "data/training_clients/client_001/credit_app.pdf"
print(f"Exists: {os.path.exists(path)}")
print(f"Full path: {os.path.abspath(path)}")
