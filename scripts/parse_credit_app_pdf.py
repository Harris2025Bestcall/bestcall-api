import os
import re
import json
import pdfplumber


def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text


def extract_field(pattern, text, default=None):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else default


def parse_credit_app_pdf(pdf_path):
    text = extract_text_from_pdf(pdf_path)

    data = {
        "name": extract_field(r"Last Name\s+([A-Za-z]+).*?First\s+([A-Za-z]+)", text),
        "dob": extract_field(r"Date of Birth\s*[:\-]*\s*(\d{2}/\d{2}/\d{4})", text),
        "ssn": extract_field(r"Soc\. Sec\. #\s*[:\-]*\s*([\d\-Xx]+)", text),
        "phone": extract_field(r"Cellular Phone\s*[:\-]*\s*(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4})", text),
        "email": extract_field(r"Email\s*[:\-]*\s*([\w\.\-]+@[\w\.\-]+)", text),
        "residence": {
            "address": extract_field(r"Present Address Line 1\s*[:\-]*\s*(.*)\n", text),
            "type": extract_field(r"Residence Type\s*[:\-]*\s*(.*)\n", text),
            "monthly_rent": extract_field(r"Monthly Rent / Mortgage Payment\s*[:\-]*\s*\$(\d+[,.]?\d*)", text),
            "time_at_residence": extract_field(r"Time at Present Address\s*[:\-]*\s*(.*)\n", text)
        },
        "employment": {
            "employer": extract_field(r"Current Employer\s*[:\-]*\s*(.*)\n", text),
            "title": extract_field(r"Employment Title\s*[:\-]*\s*(.*)\n", text),
            "status": extract_field(r"Employment Status\s*[:\-]*\s*(.*)\n", text),
            "time_at_job": extract_field(r"Time at Current Job\s*[:\-]*\s*(.*)\n", text),
            "employer_phone": extract_field(r"Employer Phone Number\s*[:\-]*\s*(.*)\n", text)
        },
        "income": {
            "gross_monthly": extract_field(r"Gross Income\s*[:\-]*\s*\$(\d+[,.]?\d*)", text),
            "other": extract_field(r"Other Income\s*[:\-]*\s*\$(\d+[,.]?\d*)", text)
        }
    }

    return data


if __name__ == "__main__":
    input_path = "../data/training_clients/client_001/credit_app.pdf"
    output_path = "../data/output_profiles/credit_app_parsed.json"

    if os.path.exists(input_path):
        parsed = parse_credit_app_pdf(input_path)
        with open(output_path, "w") as f:
            json.dump(parsed, f, indent=2)
        print(f"✅ Parsed credit application saved to {output_path}")
    else:
        print("❌ Input file not found:", input_path)
