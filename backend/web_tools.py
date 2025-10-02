# backend/web_tools.py
import os
from typing import List, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

# ---------- SEARCH ----------
def search_web(query: str, k: int = 5) -> List[Dict]:
    """
    Returns: [{url,title,snippet}, ...]
    Tries Tavily first (if TAVILY_API_KEY is set), then DuckDuckGo (no key).
    """
    out: List[Dict] = []
    key = os.getenv("TAVILY_API_KEY", "")

    # Tavily first
    if key:
        try:
            from tavily import TavilyClient
            tc = TavilyClient(api_key=key)
            res = tc.search(query=query, max_results=k)
            for r in res.get("results", []):
                out.append({
                    "url": r.get("url", "") or "",
                    "title": r.get("title", "") or "",
                    "snippet": (r.get("content", "") or "")[:400],
                })
        except Exception:
            pass

    if out:
        return out

    # DuckDuckGo fallback
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=k):
                out.append({
                    "url": r.get("href", "") or "",
                    "title": r.get("title", "") or "",
                    "snippet": (r.get("body", "") or "")[:400],
                })
    except Exception:
        pass

    return out

# ---------- FETCH / CLEAN ----------
def fetch_clean_text(url: str) -> str:
    """
    Robust fetch:
      1) requests.get(...) HTML -> trafilatura.extract()
      2) fallback: trafilatura.fetch_url()
    """
    import trafilatura, requests

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0 Safari/537.36"
    }

    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.ok and r.text:
            text = trafilatura.extract(
                r.text,
                include_comments=False,
                include_tables=False
            )
            if text:
                return text.strip()
    except Exception:
        pass

    # fallback to trafilatura.fetch_url (no timeout kwarg for compatibility)
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False
            )
            if text:
                return text.strip()
    except Exception:
        pass

    return ""  # caller will handle snippet fallback

def gather_web_context(query: str, k: int = 4, max_chars: int = 2400) -> Tuple[str, List[Dict]]:
    """
    Search, fetch top pages, return concatenated context + list of sources.
    If fetch fails, fall back to search snippets so the model still gets signal.
    """
    results = search_web(query, k=k)
    sources: List[Dict] = []
    chunks: List[str] = []
    total = 0

    for r in results[:k]:
        url = r.get("url", "")
        if not url:
            continue

        body = fetch_clean_text(url)
        if not body:
            # fallback: use search snippet if available
            snippet = (r.get("snippet") or "").strip()
            if not snippet:
                continue
            body = f"(snippet) {snippet}"

        # cap per-source contribution
        piece = body[:1200]
        chunks.append(piece)
        sources.append({"title": r.get("title", "") or url, "url": url})

        total += len(piece)
        if total >= max_chars:
            break

    context = "\n\n---\n".join(chunks)
    return context, sources
