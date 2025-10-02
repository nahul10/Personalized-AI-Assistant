# backend/vectorstore.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class Record:
    text: str
    meta: Dict[str, Any]
    emb: np.ndarray

class LocalVectorStore:
    """
    Tiny in-memory vector store compatible with the UI.
    """
    def __init__(self, dim: int):
        self._dim = dim
        self._recs: List[Record] = []

    def clear(self) -> None:
        self._recs.clear()

    def add_texts(self, texts: List[str], metas: List[Dict[str, Any]], embs: np.ndarray) -> None:
        for t, m, e in zip(texts, metas, embs):
            self._recs.append(Record(t, m, e.astype(np.float32)))

    @property
    def size(self) -> int:
        return len(self._recs)

    @property
    def texts_metas(self) -> Tuple[List[str], List[Dict[str, Any]]]:
        texts = [r.text for r in self._recs]
        metas = [r.meta for r in self._recs]
        return texts, metas

    def search(self, query_emb: np.ndarray, top_k: int = 5) -> List[Tuple[float, Dict[str, Any], str]]:
        if not self._recs:
            return []
        A = np.stack([r.emb for r in self._recs], axis=0)
        sims = cosine_similarity(query_emb.reshape(1, -1), A).ravel()
        idx = np.argsort(-sims)[:top_k]
        out = []
        for i in idx:
            out.append((float(sims[i]), self._recs[i].meta, self._recs[i].text))
        return out
