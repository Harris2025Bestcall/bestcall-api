from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from all pages of a PDF using PyPDF2.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: The extracted text.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"[ERROR extracting PDF text: {e}]"
