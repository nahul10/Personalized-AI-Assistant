# backend/pdf_utils.py
from __future__ import annotations
from typing import List, Dict, Any, Tuple
import io
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
from .ocr_utils import ocr_image

def extract_pdf(path: str, dpi: int = 200) -> Tuple[List[str], Dict[str, Any]]:
    """
    Extracts text per page; if a page has little/no selectable text, OCR it.
    Returns (texts, stats).
    """
    texts: List[str] = []
    total_pages = 0
    ocr_pages = 0
    empty_pages = 0

    # First try native text
    with pdfplumber.open(path) as pdf:
        total_pages = len(pdf.pages)
        native_texts = []
        for i, page in enumerate(pdf.pages):
            t = (page.extract_text() or "").strip()
            native_texts.append(t)

    # If any page looks empty, OCR that page from raster
    for i, t in enumerate(native_texts):
        if t:
            texts.append(t)
            continue

        # OCR this page
        ocr_pages += 1
        with fitz.open(path) as doc:
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
        t_ocr = (ocr_image(img) or "").strip()
        texts.append(t_ocr)

        if not t_ocr:
            empty_pages += 1

    stats = {
        "pages": total_pages,
        "ocr_pages": ocr_pages,
        "empty_pages": empty_pages,
        "type": ".pdf",
    }
    return texts, stats
