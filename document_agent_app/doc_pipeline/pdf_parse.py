from typing import List, Dict
from pypdf import PdfReader

def parse_pdf_to_pages(pdf_file) -> List[Dict]:
    """
    Returns: [{"page": 1, "text": "..."} ...]
    """
    reader = PdfReader(pdf_file)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        # light cleanup
        text = "\n".join([ln.strip() for ln in text.splitlines() if ln.strip()])
        pages.append({"page": i + 1, "text": text})
    return pages
