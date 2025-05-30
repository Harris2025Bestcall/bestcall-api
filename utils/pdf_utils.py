import fitz  # PyMuPDF

def extract_pdf_text_lines(pdf_path):
    """
    Extracts all lines of text from a PDF file.
    Returns a list of strings with page and line prefix.
    """
    lines = []
    try:
        with fitz.open(pdf_path) as doc:
            for page_number, page in enumerate(doc, start=1):
                text = page.get_text("text")
                for line in text.split("\n"):
                    line_cleaned = line.strip()
                    if line_cleaned:
                        lines.append(f"[Page {page_number}] {line_cleaned}")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return lines


def extract_text_blob(pdf_path):
    """
    Extracts all raw text from a PDF file as a single string blob.
    """
    try:
        with fitz.open(pdf_path) as doc:
            full_text = ""
            for page in doc:
                full_text += page.get_text("text") + "\n"
            return full_text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
