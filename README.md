# BestCall AI v3.0

BestCall AI is a dealership underwriting assistant that predicts lender approvals and optimal vehicle matches using customer-provided data (credit application, credit report, and lender decision summaries). It is trained on dealership-specific lender history and current inventory to make intelligent, real-time recommendations.

---

## 📁 Folder Structure

bestcall-ai-v3/
│
├── data/
│ ├── inventory/ # Vehicle inventory CSVs
│ ├── lender_profiles/ # Cleaned historical bank decisions (CSV)
│ ├── training_clients/ # Per-client folders w/ 3 files: credit_app.pdf, credit_report.html, bank_decision.html
│ └── output_profiles/ # Merged and structured client JSON files
│
├── scripts/
│ ├── parse_credit_app_pdf.py
│ ├── parse_credit_report_html.py
│ ├── parse_bank_decision_html.py
│ ├── build_training_profiles.py
│ ├── batch_parse_all_clients.py
│ ├── predict_vehicle_match.py
│ └── utils/
│ ├── text_cleaning.py
│ ├── html_helpers.py
│ └── pdf_utils.py
│
├── models/
│ ├── approval_predictor.pkl # Trained model
│ └── feature_encoder.json # Mapping of encoded features
│
├── notebooks/
│ └── model_training.ipynb # Used to train the model on dealership history
│
├── frontend/
│ └── upload_portal.html # File upload form (HTML only - backend not included)
│
├── requirements.txt
└── README.md

markdown
Copy
Edit

---

## ✅ How It Works

1. **Onboarding Phase**
   - Upload historical lender data (`bank_decisions_cleaned.csv`) to `/data/lender_profiles/`
   - Upload current inventory CSV to `/data/inventory/`
   - Use `model_training.ipynb` to train the model → outputs `.pkl` and `.json` in `/models/`

2. **Client Upload (Prediction Phase)**
   - Add new folder in `/data/training_clients/` named `client_001`, `client_002`, etc.
   - Each folder must contain:
     - `credit_app.pdf`
     - `credit_report.html`
     - `bank_decision.html`

   - Run:
     ```bash
     python scripts/batch_parse_all_clients.py
     python scripts/predict_vehicle_match.py
     ```

3. **Results**
   - Structured JSON profiles saved in `/data/output_profiles/`
   - Predictions for best-fit lender + vehicle based on trained model

---

## 📦 Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
📄 Future Enhancements
Flask/FastAPI backend to connect with upload_portal.html

RouteOne API integration

Admin dashboard for inventory sync + analytics

🧠 Powered By
Python 3.10+

Scikit-learn

PyPDF2

BeautifulSoup4

Tesseract OCR (optional for PDF parsing)

Pandas / NumPy

📬 Questions?
This tool is designed for internal use by dealerships to increase finance approval rates, reduce submission errors, and match clients to the best-fit financing structures.