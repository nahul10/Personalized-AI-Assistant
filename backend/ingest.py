# backend/ingest.py
import os
from datetime import datetime
from typing import List, Tuple
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import text as sqltext  # << wrap raw SQL for SA 2.0
from .schemas import File, Chunk
from .gemini_client import embed_texts
import pdfplumber
from docx import Document
import pytesseract
from PIL import Image, ImageFilter, ImageOps
import numpy as np

# honor TESSERACT_CMD env var if set
if os.getenv("TESSERACT_CMD"):
    pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- helpers ----------
def _normalize_text(t: str) -> str:
    t = (t or "").replace("\x0c", " ").strip()
    t = " ".join(t.split())
    return t

def _split(text: str, max_tokens=350, overlap=60) -> List[str]:
    words = text.split()
    out = []; i = 0
    while i < len(words):
        j = min(i + max_tokens, len(words))
        chunk = " ".join(words[i:j]).strip()
        if chunk and len(chunk) > 20:
            out.append(chunk)
        if j >= len(words): break
        i = max(0, j - overlap)
    return out

def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    g = ImageOps.grayscale(img)
    g = ImageOps.autocontrast(g)
    g = g.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=3))
    g = g.point(lambda p: 255 if p > 180 else 0)
    return g

def _ocr_image(img: Image.Image) -> str:
    pre = _preprocess_for_ocr(img)
    txt = pytesseract.image_to_string(pre, config="--psm 6")
    return _normalize_text(txt)

# ---------- extractors ----------
def _pdf_to_text_and_ocr_count(path: str) -> Tuple[int, int, List[Tuple[int, str]]]:
    out = []
    ocr_pages = 0
    with pdfplumber.open(path) as pdf:
        pages = len(pdf.pages)
        for i, p in enumerate(pdf.pages, start=1):
            txt = (p.extract_text() or "").strip()
            txt = _normalize_text(txt)
            if not txt or len(txt) < 20:
                img = p.to_image(resolution=260).original
                txt = _ocr_image(img)
                if txt:
                    ocr_pages += 1
            out.append((i, txt))
    return pages, ocr_pages, out

def _docx_to_text(path: str) -> Tuple[int, List[Tuple[int, str]]]:
    d = Document(path)
    txt = "\n".join([p.text for p in d.paragraphs])
    return 1, [(1, _normalize_text(txt))]

def _image_to_text(path: str) -> Tuple[int, List[Tuple[int, str]]]:
    img = Image.open(path).convert("RGB")
    txt = _ocr_image(img)
    return 1, [(1, txt)]

# ---------- main ingest ----------
def ingest_file(db: Session, up: UploadFile) -> dict:
    filename = up.filename
    ext = os.path.splitext(filename)[1].lower()
    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(up.file.read())

    # create file row early
    frow = File(
        name=filename,
        filename=filename,
        source_path=save_path,
        file_type=ext.lstrip("."),
        uploaded_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        pages=0, chunks=0, ocr_pages=0,
    )
    db.add(frow); db.commit(); db.refresh(frow)

    # extract
    ocr_pages = 0
    if ext == ".pdf":
        pages, ocr_pages, page_texts = _pdf_to_text_and_ocr_count(save_path)
    elif ext == ".docx":
        pages, page_texts = _docx_to_text(save_path)
    elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
        pages, page_texts = _image_to_text(save_path)
        ocr_pages = 1 if page_texts and page_texts[0][1] else 0
    else:
        try:
            with open(save_path, "r", encoding="utf-8") as rf:
                text = rf.read()
        except Exception:
            text = ""
        pages, page_texts = 1, [(1, _normalize_text(text))]

    # chunk & insert non-empty content
    seq = 0
    non_empty_chunk_count = 0
    for page_no, txt in page_texts:
        txt = _normalize_text(txt)
        if txt and len(txt) > 20:
            for piece in _split(txt):
                if piece and len(piece) > 20:
                    db.add(Chunk(
                        file_id=frow.id, page_no=page_no, seq_no=seq, content=piece,
                        emb_dim=0, embedding=None
                    ))
                    seq += 1
                    non_empty_chunk_count += 1

    frow.pages = pages
    frow.chunks = non_empty_chunk_count
    frow.ocr_pages = ocr_pages
    db.commit()

    # embeddings only if we have meaningful text
    if non_empty_chunk_count > 0:
        rows = db.execute(
            sqltext("SELECT id, content FROM chunks WHERE file_id = :fid ORDER BY seq_no ASC"),
            {"fid": frow.id}
        ).fetchall()
        texts = [r[1] for r in rows]
        try:
            vectors = embed_texts(texts)
            print(f"Embedding vectors generated: {len(vectors)}")
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            vectors = None

        if vectors is not None and len(vectors) == len(rows):
            for (row_id, _), vec in zip(rows, vectors):
                arr = np.asarray(vec, dtype=np.float32)
                db.execute(
                    sqltext("UPDATE chunks SET emb_dim=:d, embedding=:e WHERE id=:rid"),
                    {"d": int(arr.shape[0]), "e": arr.tobytes(), "rid": row_id}
                )
            db.commit()

    return {
        "file_id": frow.id,
        "filename": frow.filename or frow.name,
        "file_type": frow.file_type,
        "pages": frow.pages,
        "chunks": frow.chunks,
        "ocr_pages": frow.ocr_pages,
        "source_path": frow.source_path,
    }
