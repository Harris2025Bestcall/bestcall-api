
import pytesseract
from PIL import Image, ImageOps, ImageEnhance
import json

# Updated bounding boxes (manually tuned to new PNG)
FIELD_REGIONS = {
    "name": (140, 60, 430, 90),
    "dob": (680, 60, 850, 90),
    "ssn": (860, 60, 1030, 90),
    "address": (140, 120, 550, 150),
    "apt": (140, 150, 240, 180),
    "city_state_zip": (250, 150, 680, 180),
    "time_at_address": (550, 120, 850, 150),
    "prev_address": (140, 210, 550, 240),
    "prev_city_state_zip": (250, 240, 600, 270),
    "phone": (140, 300, 550, 330),
    "email": (300, 350, 880, 380),
    "employer": (140, 410, 500, 440),
    "job_title": (140, 380, 400, 410),
    "employment_status": (400, 380, 700, 410),
    "employer_phone": (140, 470, 500, 500),
    "time_at_job": (500, 470, 880, 500),
    "gross_income": (140, 560, 300, 590),
    "other_income": (520, 560, 720, 590),
    "residence_type": (140, 600, 400, 630),
    "monthly_rent": (700, 600, 900, 630)
}

def preprocess_image_region(image):
    # Convert to grayscale
    image = ImageOps.grayscale(image)
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    return image

def extract_text_from_region(image, region):
    cropped = image.crop(region)
    cropped = preprocess_image_region(cropped)
    text = pytesseract.image_to_string(cropped, config="--psm 6")
    return text.strip()

def safe_float(value):
    try:
        return float(value.replace("$", "").replace(",", "").strip())
    except:
        return 0.0

def parse_credit_app_image(image_path):
    img = Image.open(image_path)
    data = {}

    extracted = {key: extract_text_from_region(img, box) for key, box in FIELD_REGIONS.items()}

    gross_income = safe_float(extracted["gross_income"])
    other_income = safe_float(extracted["other_income"])
    monthly_rent = safe_float(extracted["monthly_rent"])

    data["application"] = {
        "name": extracted["name"],
        "dob": extracted["dob"],
        "ssn": extracted["ssn"],
        "phone": extracted["phone"],
        "email": extracted["email"],
        "residence": {
            "address": f"{extracted['address']} {extracted['apt']}, {extracted['city_state_zip']}",
            "type": extracted["residence_type"],
            "monthly_rent": monthly_rent,
            "time_at_residence": extracted["time_at_address"]
        },
        "employment": {
            "employer": extracted["employer"],
            "title": extracted["job_title"],
            "status": extracted["employment_status"],
            "employer_phone": extracted["employer_phone"],
            "time_at_job": extracted["time_at_job"]
        },
        "income": {
            "gross_monthly": gross_income,
            "other_income": other_income
        }
    }

    return data

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python extract_from_credit_app_image.py path/to/screenshot.png")
    else:
        output = parse_credit_app_image(sys.argv[1])
        print(json.dumps(output, indent=2))
