# backend/retriever.py
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text as sqltext
from .gemini_client import model, embed_texts, GEMINI_MODEL

def _cos_sim(a, b):
    a = np.asarray(a, dtype=np.float32); b = np.asarray(b, dtype=np.float32)
    na = np.linalg.norm(a) + 1e-8; nb = np.linalg.norm(b) + 1e-8
    return float(np.dot(a, b) / (na * nb))

def _keyword_fallback(db: Session, question: str, k: int = 6):
    # allow even 2-letter tokens; also search ANY word with OR
    raw = [w.lower() for w in question.split()]
    keywords = [w for w in raw if w.isalpha()]
    if not keywords:
        keywords = [question.lower()]
    like = " OR ".join([f"LOWER(content) LIKE :p{i}" for i in range(len(keywords))])
    params = {f"p{i}": f"%{w}%" for i, w in enumerate(keywords)}
    params["k"] = k
    sql = f"SELECT id, file_id, page_no, seq_no, content FROM chunks WHERE {like} LIMIT :k"
    rows = db.execute(sqltext(sql), params).fetchall()
    return [{"id": r[0], "file_id": r[1], "page_no": r[2], "seq_no": r[3], "content": r[4], "score": 0.0} for r in rows]

def top_k_chunks(db: Session, question: str, k: int = 6):
    try:
        rows = db.execute(sqltext("SELECT id, file_id, page_no, seq_no, content, emb_dim, embedding FROM chunks")).fetchall()
        print(f"Retrieved rows from DB: {rows}")
        
        any_vec = any(r[6] for r in rows)
        if not any_vec:
            print("No embeddings found, falling back to keyword search.")
            return _keyword_fallback(db, question, k)
        
        qvec = embed_texts(question)
        print(f"Query embedding: {qvec}")
        
        scored = []
        for r in rows:
            if not r[6]:  # no embedding
                continue
            vec = np.frombuffer(r[6], dtype=np.float32)
            score = _cos_sim(qvec, vec)
            scored.append((score, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        
        out = []
        for score, r in scored[:k]:
            out.append({
                "id": r[0], "file_id": r[1], "page_no": r[2], "seq_no": r[3],
                "content": r[4], "score": score
            })
        print(f"Top chunks: {out}")
        return out or _keyword_fallback(db, question, k)
    except Exception as e:
        print(f"Error in top_k_chunks: {e}")
        raise RuntimeError(f"Chunk retrieval failed: {e}")

def answer_with_context(question: str, contexts: list, output_mode: str = "text"):
    try:
        m = model()
        print("Using model in answer_with_context:", GEMINI_MODEL)  # Debugging statement
        sys = (
            "You are a precise assistant. Use ONLY the provided context. "
            "If info is insufficient, say so clearly."
        )
        ctx = "\n\n---\n\n".join([c["content"] for c in contexts])
        prompt = f"""OUTPUT_MODE={output_mode}

        CONTEXT:
        {ctx}

        QUESTION:
        {question}

        If OUTPUT_MODE=json, output a single JSON with:
        - answer (string)
        - key_points (string[])
        - citations (array of objects {{page_no, seq_no}})
        No backticks."""
        print(f"Generated prompt: {prompt}")
        
        resp = m.generate_content([sys, prompt])
        print(f"Response from Gemini: {resp.text.strip()}")
        return resp.text.strip()
    except Exception as e:
        print(f"Error in answer_with_context: {e}")
        return "Unable to generate an answer due to model or API issues."
