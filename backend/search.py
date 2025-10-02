# backend/search.py
import os
from typing import List, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

def search_web(query: str, k: int = 5) -> List[Dict]:
    out: List[Dict] = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=k):
                out.append({
                    "url": r.get("href","") or "",
                    "title": r.get("title","") or "",
                    "snippet": (r.get("body","") or "")[:400],
                })
    except Exception:
        pass
    return out

def fetch_clean_text(url: str) -> str:
    import requests, trafilatura
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.ok and r.text:
            t = trafilatura.extract(r.text, include_comments=False, include_tables=False)
            if t: return t.strip()
    except Exception:
        pass
    try:
        dl = trafilatura.fetch_url(url)
        if dl:
            t = trafilatura.extract(dl, include_comments=False, include_tables=False)
            if t: return t.strip()
    except Exception:
        pass
    return ""

def gather_web_context(query: str, k: int = 4, max_chars: int = 2400) -> Tuple[str, List[Dict]]:
    results = search_web(query, k=k)
    chunks: List[str] = []
    sources: List[Dict] = []
    total = 0
    for r in results[:k]:
        url = r.get("url","")
        if not url:
            continue
        body = fetch_clean_text(url)
        if not body:
            body = "(snippet) " + (r.get("snippet") or "")
        piece = body[:1200]
        chunks.append(piece)
        sources.append({"title": r.get("title") or url, "url": url})
        total += len(piece)
        if total >= max_chars:
            break
    return "\n\n---\n".join(chunks), sources
