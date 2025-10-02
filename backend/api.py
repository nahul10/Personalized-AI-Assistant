# backend/api.py
import os
import shutil
from typing import Optional
from fastapi import FastAPI, Depends, UploadFile, File as FFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .state import init_db, get_db
from .schemas import QAHistory, File

app = FastAPI(title="Personalized AI Assistant", version="0.3.2")

# Dev CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True, "service": "personal-coach", "version": "0.3.2"}

# ---------- Upload & Index ----------
@app.post("/upload")
def upload_endpoint(file: UploadFile = FFile(...), db: Session = Depends(get_db)):
    try:
        from .ingest import ingest_file
        meta = ingest_file(db, file)
        return {"status": "ok", "detail": meta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

# ---------- RAG ----------
class AskBody(BaseModel):
    question: str
    output_mode: Optional[str] = "text"   # "text" | "json" | "chart"

@app.post("/ask")
def ask_rag(body: AskBody, db: Session = Depends(get_db)):
    try:
        from .retriever import top_k_chunks, answer_with_context
        print(f"Received question: {body.question}")
        
        # Retrieve context
        ctx = top_k_chunks(db, body.question, k=6)
        print(f"Retrieved context: {ctx}")
        
        # Generate answer
        ans = (
            answer_with_context(body.question, ctx, output_mode=body.output_mode or "text")
            if ctx else "No relevant context found."
        )
        print(f"Generated answer: {ans}")
        
        # Save history
        hist = QAHistory(mode="RAG", question=body.question, answer=ans)
        db.add(hist); db.commit()
        return {"answer": ans, "contexts": ctx}
    except Exception as e:
        print(f"Error in /ask endpoint: {e}")
        return {"answer": f"Error: {str(e)}", "contexts": []}

# ---------- SQL ----------
class SQLGenBody(BaseModel):
    question: str
    table_schema_markdown: Optional[str] = None

@app.post("/sql/generate")
def sql_generate(body: SQLGenBody):
    from .gemini_client import model
    md = model()
    system = "You convert natural language into safe, read-only SQLite SQL. Never modify data."
    prompt = f"""NL: {body.question}

Rules:
- Only SELECT queries.
- If ambiguous, assume tables: files(id, name, filename, source_path, file_type, pages, chunks, ocr_pages, uploaded_at, created_at),
  chunks(id, file_id, page_no, seq_no, content, emb_dim, embedding),
  history(id, mode, question, answer, created_at).
- Return ONLY SQL in one line.
"""
    txt = md.generate_content([system, prompt]).text.strip().strip("`")
    return {"sql": txt}

class SQLRunBody(BaseModel):
    sql: str

@app.post("/sql/run")
def sql_run(body: SQLRunBody, db: Session = Depends(get_db)):
    sql = body.sql.strip().lower()
    if any(x in sql for x in ["update ", "insert ", "delete ", "drop ", "alter ", "create "]):
        raise HTTPException(400, "Only SELECT is allowed")
    rows = db.execute(text(body.sql)).fetchall()
    cols = list(rows[0]._mapping.keys()) if rows else []
    data = [list(r) for r in rows]
    hist = QAHistory(mode="SQL", question=body.sql, answer=f"{len(data)} rows")
    db.add(hist); db.commit()
    return {"columns": cols, "rows": data}

# ---------- Translate ----------
class TranslateBody(BaseModel):
    text: str
    target_lang: str

@app.post("/translate")
def translate(body: TranslateBody):
    from .gemini_client import model
    m = model()
    sys = "You are a translator. Keep meaning; return only the translated text."
    out = m.generate_content([sys, f"Translate to {body.target_lang}:\n{body.text}"]).text.strip()
    from .state import SessionLocal
    db = SessionLocal(); db.add(QAHistory(mode="TRANSLATE",
        question=f"to {body.target_lang}: {body.text[:120]}", answer=out)); db.commit(); db.close()
    return {"translation": out}

# ---------- Reset Index ----------
class ResetBody(BaseModel):
    delete_history: Optional[bool] = False

@app.post("/reset_index")
def reset_index(body: ResetBody, db: Session = Depends(get_db)):
    """
    Deletes all files and chunks. If delete_history=True, also deletes history.
    Also clears backend/uploads directory.
    """
    # 1) Delete DB rows
    db.execute(text("DELETE FROM chunks"))
    db.execute(text("DELETE FROM files"))
    if body.delete_history:
        db.execute(text("DELETE FROM history"))
    db.commit()

    # 2) Clear uploads dir
    uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
    if os.path.isdir(uploads_dir):
        for name in os.listdir(uploads_dir):
            p = os.path.join(uploads_dir, name)
            try:
                if os.path.isdir(p): shutil.rmtree(p)
                else: os.remove(p)
            except Exception:
                pass

    return {"status": "ok", "deleted_history": bool(body.delete_history)}

# ---------- Lists ----------
@app.get("/files")
def list_files(db: Session = Depends(get_db)):
    rows = db.execute(select(File).order_by(File.id.desc())).scalars().all()
    return [
        {"id": f.id, "filename": f.filename or f.name, "type": f.file_type,
         "pages": f.pages, "chunks": f.chunks, "ocr_pages": getattr(f, "ocr_pages", 0),
         "source_path": f.source_path, "created_at": f.created_at.isoformat()}
        for f in rows
    ]

@app.get("/history")
def list_history(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, mode, question, answer, created_at FROM history ORDER BY id DESC LIMIT :k"
    ), {"k": limit}).fetchall()
    return [{"id": r[0], "mode": r[1], "question": r[2], "answer": r[3], "created_at": r[4]} for r in rows]
