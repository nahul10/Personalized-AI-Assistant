# backend/generator.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Optional: OpenAI; falls back to a no-LLM heuristic if not configured
try:
    from openai import OpenAI  # openai>=1.0.0
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


def _short_source(meta: Dict[str, Any]) -> str:
    """
    Build a short human-readable source label WITHOUT creating backslashes
    inside f-string expressions (Windows-safe).
    """
    raw_path = (
        str(meta.get("path"))
        or str(meta.get("source", ""))  # some pipelines use "source"
        or ""
    )

    # Sanitize Windows backslashes *before* putting into an f-string
    safe_path = raw_path.replace("\\", "/")
    name = Path(safe_path).name or "file"
    page = meta.get("page") or meta.get("page_num") or meta.get("pageNumber")
    return f"{name}{f' p.{page}' if page else ''}"


def _format_context(chunks: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    """
    Turn retrieved chunks into a compact context block and a parallel
    list of source labels. We purposely keep it short and deterministic.
    """
    lines: List[str] = []
    sources: List[str] = []

    for i, ch in enumerate(chunks, start=1):
        text = str(ch.get("text") or ch.get("content") or "").strip()
        meta = ch.get("meta", {}) or {}
        src = _short_source(meta)
        sources.append(src)
        # Bound each chunk length to keep prompts small
        snippet = text[:2000]
        lines.append(f"[{i}] ({src}) {snippet}")

    return "\n".join(lines), sources


SYSTEM_RULES = (
    "You answer ONLY using the provided context. "
    "If the exact answer is present, quote it concisely. "
    "If the answer is a small number, date, name, or phrase, return ONLY that. "
    "Do not add extra commentary, disclaimers, or speculation. "
    "If the answer truly is not in the context, reply exactly: NOT_FOUND_IN_FILES."
)


def _build_prompt(question: str, chunks: List[Dict[str, Any]]) -> str:
    ctx, _ = _format_context(chunks)
    return (
        f"{SYSTEM_RULES}\n\n"
        f"# Context\n{ctx}\n\n"
        f"# Question\n{question}\n\n"
        f"# Answer"
    )


def _call_openai(prompt: str) -> str:
    """
    Calls OpenAI if OPENAI_API_KEY is available; returns stripped text.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        raise RuntimeError("OPENAI_API_KEY missing or openai client not installed")

    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=256,
    )
    text = (resp.choices[0].message.content or "").strip()
    return text


def _fallback_answer(question: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Heuristic, LLM-free fallback: return a concise snippet from the most
    relevant chunk (longest chunk that contains a keyword).
    This guarantees we never return an empty answer.
    """
    q = question.lower()
    keywords = [w for w in q.replace("?", " ").split() if len(w) > 2]
    scored: List[Tuple[int, Dict[str, Any]]] = []

    for ch in chunks:
        txt = str(ch.get("text") or ch.get("content") or "")
        score = sum(txt.lower().count(k) for k in keywords)
        scored.append((score, ch))

    # Pick the most keyword-overlapping chunk; fallback to longest
    scored.sort(key=lambda t: (t[0], len(str(t[1].get("text") or ""))), reverse=True)
    best = (scored[0][1] if scored else (chunks[0] if chunks else None))

    if not best:
        return "NOT_FOUND_IN_FILES"

    snippet = str(best.get("text") or best.get("content") or "").strip()
    snippet = " ".join(snippet.split())  # collapse whitespace
    # Keep it short
    return snippet[:280] if snippet else "NOT_FOUND_IN_FILES"


def _postprocess(answer: str) -> str:
    """
    Ensure we return a non-empty, concise string with no filler.
    """
    if not answer:
        return "NOT_FOUND_IN_FILES"
    cleaned = answer.strip()
    # Keep a hard cap just in case a model tries to over-explain
    if len(cleaned) > 600:
        cleaned = cleaned[:600].rstrip() + "…"
    return cleaned


def generate_answer(question: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point used by the API.

    Parameters
    ----------
    question : str
    chunks   : list of dicts, each like {"text": "...", "meta": {"path": "...", "page": 3}}

    Returns
    -------
    dict with:
      - "answer": str
      - "sources": List[str] (short file/page labels used)
    """
    # Build prompt
    prompt = _build_prompt(question, chunks)

    # Try OpenAI first (if configured)
    answer_text: str
    try:
        answer_text = _call_openai(prompt)
    except Exception:
        # Fall back to deterministic heuristic
        answer_text = _fallback_answer(question, chunks)

    final = _postprocess(answer_text)

    # Never return empty: if still NOT_FOUND and we have chunks, show best snippet
    if final == "NOT_FOUND_IN_FILES" and chunks:
        final = _fallback_answer(question, chunks)

    # Sources for UI
    _, srcs = _format_context(chunks)
    return {"answer": final, "sources": srcs}
