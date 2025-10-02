# backend/hybrid_retrieval.py
import os, re, math, json, uuid
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field

from rank_bm25 import BM25Okapi

# Optional: if numpy is available we use it for cosine; otherwise pure python
try:
    import numpy as np
except Exception:
    np = None

# ---- Embeddings via Google Gemini ------------------------------------------------
_EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-004")

def _embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Returns a list of embeddings (lists of floats).
    Uses Google Generative AI embeddings (text-embedding-004 by default).
    """
    import google.generativeai as genai
    api = os.getenv("GEMINI_API_KEY")
    if not api:
        # graceful fallback: zero-vectors (still lets BM25 run)
        dim = 768
        return [[0.0] * dim for _ in texts]
    genai.configure(api_key=api)
    # batched embed to reduce calls
    out = genai.embed_content(model=_EMBED_MODEL, content=texts)
    # API returns either "embedding": {...} or a list; normalize both
    if isinstance(out, dict) and "embedding" in out:
        return [out["embedding"]["values"] or out["embedding"].get("value", [])]
    if isinstance(out, dict) and "data" in out:
        # legacy style
        return [d["embedding"] for d in out["data"]]
    if isinstance(out, list):
        # newer SDK may return a list of dicts
        res = []
        for item in out:
            emb = getattr(item, "embedding", None) or item.get("embedding") if isinstance(item, dict) else None
            if hasattr(emb, "values"): emb = emb.values
            res.append(list(emb or []))
        return res
    # newest SDK shape (as of 2025): dict with "embeddings": [{"values":[...]}]
    if isinstance(out, dict) and "embeddings" in out:
        return [e.get("values", []) for e in out["embeddings"]]
    # last resort
    return [[] for _ in texts]


def _tokenize(text: str) -> List[str]:
    # simple, fast tokenization
    return re.findall(r"[a-z0-9]+", text.lower())


def _cosine(a: List[float], b: List[float]) -> float:
    # robust cosine that works with or without numpy
    if not a or not b or len(a) != len(b):
        return 0.0
    if np is None:
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        if na == 0 or nb == 0: return 0.0
        return dot / (na * nb)
    va = np.array(a, dtype=np.float32); vb = np.array(b, dtype=np.float32)
    na = np.linalg.norm(va); nb = np.linalg.norm(vb)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(va, vb) / (na * nb))


@dataclass
class Doc:
    id: str
    file: str
    page: int
    text: str
    tokens: List[str] = field(default_factory=list)
    emb: List[float] = field(default_factory=list)


class HybridRetriever:
    """
    - Keeps an in-memory corpus of chunks (text + metadata).
    - For lexical search uses BM25.
    - For dense search uses Gemini embeddings + cosine.
    - Combines (weighted sum) and optionally reranks with Gemini.
    """
    def __init__(self, bm25_weight: float = None, rerank_engine: str = None, rerank_topk: int = None):
        self.bm25_weight = float(os.getenv("HYBRID_BM25_WEIGHT", bm25_weight or 0.45))
        self.rerank_engine = os.getenv("RERANK_ENGINE", rerank_engine or "gemini")  # "gemini" or "none"
        self.rerank_topk = int(os.getenv("RERANK_TOPK", rerank_topk or 24))

        self.docs: List[Doc] = []
        self._bm25: Optional[BM25Okapi] = None

    # ---- corpus management -------------------------------------------------

    def reset(self):
        self.docs = []
        self._bm25 = None

    def add_docs(self, chunks: List[Dict[str, Any]]):
        """
        chunks: [{ "text": str, "file": str, "page": int, "id": optional }]
        Embeds, tokenizes, appends to corpus, rebuilds BM25.
        """
        texts = [c["text"] for c in chunks]
        embs = _embed_texts(texts)

        for c, e in zip(chunks, embs):
            did = c.get("id") or str(uuid.uuid4())
            tokens = _tokenize(c["text"])
            self.docs.append(Doc(id=did, file=c["file"], page=int(c.get("page", -1)), text=c["text"], tokens=tokens, emb=e))

        self._rebuild_bm25()

    def _rebuild_bm25(self):
        if not self.docs:
            self._bm25 = None
            return
        corpus_tokens = [d.tokens for d in self.docs]
        self._bm25 = BM25Okapi(corpus_tokens)

    # ---- search ------------------------------------------------------------

    def _dense_scores(self, q_emb: List[float], scope: Optional[str]) -> List[float]:
        scores = []
        for d in self.docs:
            if scope and scope != "all" and d.file != scope:
                scores.append(float("-inf"))
            else:
                scores.append(_cosine(q_emb, d.emb) if d.emb else 0.0)
        return scores

    def _bm25_scores(self, q_tokens: List[str], scope: Optional[str]) -> List[float]:
        if not self._bm25:
            return [float("-inf")] * len(self.docs)
        raw = self._bm25.get_scores(q_tokens)
        scores = []
        for d, s in zip(self.docs, raw):
            if scope and scope != "all" and d.file != scope:
                scores.append(float("-inf"))
            else:
                scores.append(float(s))
        return scores

    @staticmethod
    def _minmax(x: List[float]) -> List[float]:
        xs = [v for v in x if v != float("-inf")]
        if not xs:
            return [0.0]*len(x)
        mn, mx = min(xs), max(xs)
        if mx <= mn:  # constant
            return [0.0 if v == float("-inf") else 1.0 for v in x]
        return [0.0 if v == float("-inf") else (v - mn)/(mx - mn) for v in x]

    def _combine(self, q_text: str, scope: Optional[str], top_k: int, bm25_weight: float) -> List[int]:
        q_tokens = _tokenize(q_text)
        q_emb = _embed_texts([q_text])[0]

        ds = self._dense_scores(q_emb, scope)
        ls = self._bm25_scores(q_tokens, scope)

        dsn = self._minmax(ds)
        lsn = self._minmax(ls)

        weight = bm25_weight if bm25_weight is not None else self.bm25_weight
        scores = [weight*lv + (1.0-weight)*dv for lv, dv in zip(lsn, dsn)]

        idxs = sorted(range(len(self.docs)), key=lambda i: scores[i], reverse=True)
        # take a generous pre-cut for reranker
        pre_k = max(top_k, self.rerank_topk)
        return [i for i in idxs[:pre_k] if scores[i] > 0.0]

    # ---- reranking ---------------------------------------------------------

    def _rerank_gemini(self, query: str, cand_ids: List[int]) -> List[int]:
        import google.generativeai as genai
        api = os.getenv("GEMINI_API_KEY")
        if not api:
            return cand_ids
        genai.configure(api_key=api)

        # Keep prompt small: cap text lengths
        def snip(t: str, n=600): 
            t = re.sub(r"\s+", " ", t).strip()
            return (t[: n-1] + "…") if len(t) > n else t

        items = []
        for i in cand_ids:
            d = self.docs[i]
            items.append({"id": i, "file": d.file, "page": d.page, "text": snip(d.text)})

        system = (
            "Rank the passages by relevance to the user's query. "
            "Return STRICT JSON: {\"order\":[ids...]} with ids from the input. "
            "Do not include any explanations."
        )
        user = "Query: " + query + "\n\nPassages:\n" + json.dumps(items, ensure_ascii=False)

        try:
            model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-pro"))
            out = model.generate_content([system, user])
            txt = getattr(out, "text", "") or ""
            # Extract JSON safely
            m = re.search(r"\{.*\}", txt, re.S)
            if not m:
                return cand_ids
            data = json.loads(m.group(0))
            order = data.get("order") or data.get("ids") or []
            # Filter to original set and preserve only ints
            order = [i for i in order if isinstance(i, int) and i in cand_ids]
            if order:
                return order
        except Exception:
            pass
        return cand_ids

    # ---- public API --------------------------------------------------------

    def search(self, query: str, *, scope: Optional[str] = "all",
               top_k: int = 8, bm25_weight: Optional[float] = None,
               use_reranker: bool = True) -> Dict[str, Any]:
        """
        Returns:
        {
          "contexts": [ {text, file, page}, ... up to top_k ],
          "citations": [ {source, page, score, preview}, ... ],
          "debug": {bm25_weight, reranked, candidates}
        }
        """
        cand = self._combine(query, scope, top_k, bm25_weight)
        reranked = False
        if use_reranker and self.rerank_engine.lower() == "gemini" and len(cand) > top_k:
            cand = self._rerank_gemini(query, cand)
            reranked = True

        take = cand[:top_k]
        out_ctx = []
        out_cites = []
        for i in take:
            d = self.docs[i]
            preview = d.text[:220].replace("\n", " ")
            out_ctx.append({"text": d.text, "file": d.file, "page": d.page})
            out_cites.append({"source": f"{d.file} (p.{d.page})", "page": d.page, "score": None, "preview": preview})

        return {
            "contexts": out_ctx,
            "citations": out_cites,
            "debug": {
                "bm25_weight": bm25_weight if bm25_weight is not None else self.bm25_weight,
                "reranked": reranked,
                "candidates": take
            }
        }
