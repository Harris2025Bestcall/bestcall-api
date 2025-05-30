from bs4 import BeautifulSoup

def load_html(filepath: str) -> BeautifulSoup:
    """Load and parse HTML file with BeautifulSoup."""
    with open(filepath, "r", encoding="utf-8") as f:
        html_content = f.read()
    return BeautifulSoup(html_content, "html.parser")

def find_text_near_label(soup: BeautifulSoup, label: str, max_distance=5) -> str:
    """
    Look for the value near a label by scanning nearby text elements.
    Useful when labels and values are close together in flat HTML.
    """
    all_text = soup.get_text(separator='\n').splitlines()
    for i, line in enumerate(all_text):
        if label.lower() in line.lower():
            for j in range(1, max_distance + 1):
                if i + j < len(all_text):
                    candidate = all_text[i + j].strip()
                    if candidate and not label.lower() in candidate.lower():
                        return candidate
    return ""

def extract_table_data(soup: BeautifulSoup, table_id: str = None) -> list:
    """
    Extract table data into a list of dicts from a table with optional ID.
    Each row becomes a dict with column headers as keys.
    """
    table = soup.find("table", {"id": table_id}) if table_id else soup.find("table")
    if not table:
        return []

    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    rows = []
    for tr in table.find_all("tr")[1:]:  # Skip header row
        cells = tr.find_all(["td", "th"])
        row = {headers[i]: cells[i].get_text(strip=True) for i in range(min(len(headers), len(cells)))}
        rows.append(row)
    return rows

def extract_all_text_blocks(soup: BeautifulSoup) -> list:
    """Return all non-empty lines of text from the HTML."""
    return [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
