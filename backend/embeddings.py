# embeddings.py
from __future__ import annotations
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL = None
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(_MODEL_NAME)
    return _MODEL

def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Returns L2-normalized float32 embeddings (n, d).
    """
    if not texts:
        return np.zeros((0, 384), dtype="float32")
    model = get_model()
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vecs, dtype="float32")
