import os
import io
import shutil
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List

# Lazy imports so the app can still run without OCR dependencies
try:
    import pytesseract  # type: ignore
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    pytesseract = None  # type: ignore
    Image = None  # type: ignore

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None  # type: ignore

@dataclass
class OCRConfig:
    cmd: Optional[str]
    tessdata_prefix: Optional[str]
    lang: str = "eng"

def _detect_tesseract() -> OCRConfig:
    # Respect explicit env first
    cmd = os.environ.get("TESSERACT_CMD")
    if cmd and os.path.exists(cmd):
        pass
    else:
        # Try to find on PATH
        cmd = shutil.which("tesseract")
    tessdata = os.environ.get("TESSDATA_PREFIX")
    return OCRConfig(cmd=cmd, tessdata_prefix=tessdata)

def ocr_available() -> Tuple[bool, OCRConfig, Optional[str]]:
    if pytesseract is None or Image is None:
        return False, _detect_tesseract(), "pytesseract/Pillow not installed"
    cfg = _detect_tesseract()
    if not cfg.cmd:
        return False, cfg, "tesseract binary not found on PATH or TESSERACT_CMD"
    # Wire pytesseract to the discovered location
    pytesseract.pytesseract.tesseract_cmd = cfg.cmd
    if cfg.tessdata_prefix:
        os.environ["TESSDATA_PREFIX"] = cfg.tessdata_prefix
    return True, cfg, None

def pdf_page_to_image_bytes(pdf: "fitz.Document", page_index: int, zoom: float = 2.0) -> bytes:
    """Render a PDF page to PNG bytes using PyMuPDF."""
    page = pdf.load_page(page_index)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")

def ocr_page_png(png_bytes: bytes, lang: str) -> str:
    if Image is None or pytesseract is None:
        return ""
    img = Image.open(io.BytesIO(png_bytes))
    text = pytesseract.image_to_string(img, lang=lang)
    return text or ""

def extract_text_from_pdf(path: str, use_ocr: bool = True, lang: str = "eng") -> Dict[str, Any]:
    """
    Returns:
      {
        "pages": int,
        "text_by_page": [str, ...],
        "ocr_attempted": int
      }
    Uses PyMuPDF text by default, falls back to OCR per page if no text found and use_ocr=True.
    """
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is not installed")
    ok, cfg, _err = ocr_available()
    doc = fitz.open(path)
    text_by_page: List[str] = []
    ocr_attempted = 0
    for i in range(doc.page_count):
        t = ""
        try:
            # Try real text first (much faster, more accurate if present)
            page = doc.load_page(i)
            t = page.get_text("text") or ""
        except Exception:
            t = ""
        if (not t) and use_ocr and ok:
            try:
                png = pdf_page_to_image_bytes(doc, i, zoom=2.0)
                t = ocr_page_png(png, lang=lang) or ""
                ocr_attempted += 1
            except Exception:
                # ignore, keep page empty
                pass
        text_by_page.append(t)
    return {
        "pages": doc.page_count,
        "text_by_page": text_by_page,
        "ocr_attempted": ocr_attempted,
    }

def get_ocr_info() -> Dict[str, Any]:
    ok, cfg, err = ocr_available()
    return {
        "ocr_available": bool(ok),
        "tesseract": bool(cfg.cmd),
        "renderer": "pymupdf",
        "pdf_text": True,
        "error": err,
    }
