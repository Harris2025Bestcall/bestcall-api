import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_model():
    csv_path = "data/training_dataset.csv"
    model_path = "models/approval_predictor.pkl"
    os.makedirs("models", exist_ok=True)

    # Load dataset
    df = pd.read_csv(csv_path)

    # Drop rows with missing target
    df = df[df["actual_approved"].notnull()]

    # Convert booleans if stored as strings
    df["actual_approved"] = df["actual_approved"].astype(bool)

    # Feature engineering
    df["bank"] = df["bank"].astype("category").cat.codes  # Encode bank names
    df["match"] = df["match"].astype(bool)

    X = df[["fico_score", "gross_monthly_income", "bank"]]
    y = df["actual_approved"]

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"✅ Model Accuracy: {round(acc * 100, 2)}%")
    print("📊 Classification Report:")
    print(classification_report(y_test, y_pred))

    # Save model
    joblib.dump(clf, model_path)
    print(f"💾 Model saved to: {model_path}")

if __name__ == "__main__":
    train_model()
