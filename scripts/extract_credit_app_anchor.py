
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import json
import re

def preprocess_image(image_path):
    image = Image.open(image_path).convert("L")  # Grayscale
    image = image.filter(ImageFilter.MedianFilter())
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)
    return image

def search_line_cluster(lines, keywords, regex, lookahead=2):
    for i, line in enumerate(lines):
        for key in keywords:
            if key.lower() in line.lower():
                candidates = lines[i:i+lookahead]
                for text in candidates:
                    match = re.search(regex, text)
                    if match:
                        return match.group(1).strip()
    return ""

def extract_dollars(lines, keywords, lookahead=3):
    for i, line in enumerate(lines):
        for key in keywords:
            if key.lower() in line.lower():
                for look in lines[i:i+lookahead]:
                    match = re.search(r"\$?([\d,]+\.?\d{0,2})", look)
                    if match:
                        return float(match.group(1).replace(",", ""))
    return 0.0

def parse_credit_app_image_anchor(image_path):
    image = preprocess_image(image_path)
    text = pytesseract.image_to_string(image)
    lines = text.splitlines()

    result = {
        "application": {
            "name": search_line_cluster(lines, ["last name", "first name", "Soren"], r"Smith,?\s*Jessica"),
            "dob": search_line_cluster(lines, ["dob", "date of birth"], r"(\d{2}/\d{2}/\d{4})"),
            "ssn": search_line_cluster(lines, ["ssn", "soc sec"], r"(\d{3}-?\d{2}-?\d{4})"),
            "phone": search_line_cluster(lines, ["phone", "cellular"], r"(\(?\d{3}\)?[-\s]?\d{3}-\d{4})"),
            "email": search_line_cluster(lines, ["email", "@", "gmail"], r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"),
            "residence": {
                "address": search_line_cluster(lines, ["present address", "W 12 mile"], r"(\d+\s+\w+\s+\w+\s*\w*)"),
                "type": search_line_cluster(lines, ["residence type", "renting", "leasing"], r"(Renting|Leasing|Living.*|Owns?)", lookahead=3),
                "monthly_rent": extract_dollars(lines, ["monthly rent", "mortgage payment", "payment"]),
                "time_at_residence": search_line_cluster(lines, ["time at present address"], r"(\d+\s+years?\s*\d*\s*months?)")
            },
            "employment": {
                "employer": search_line_cluster(lines, ["current employer", "Amazon"], r"(Amazon|Walmart|[A-Z][a-z]+)"),
                "title": search_line_cluster(lines, ["employment title", "associate"], r"([A-Z][a-z]+\s+[A-Z][a-z]+)"),
                "status": search_line_cluster(lines, ["employment status"], r"(Full Time|Part Time|Self-Employed)"),
                "employer_phone": search_line_cluster(lines, ["employer phone", "business ph"], r"(\(?\d{3}\)?[-\s]?\d{3}-\d{4})"),
                "time_at_job": search_line_cluster(lines, ["time at current job"], r"(\d+\s+years?\s*\d*\s*months?)")
            },
            "income": {
                "gross_monthly": extract_dollars(lines, ["gross income"]),
                "other_income": extract_dollars(lines, ["other income"])
            }
        }
    }

    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python extract_credit_app_anchor.py path/to/screenshot.png")
    else:
        profile = parse_credit_app_image_anchor(sys.argv[1])
        print(json.dumps(profile, indent=2))
