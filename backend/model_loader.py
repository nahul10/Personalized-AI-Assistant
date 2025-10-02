from __future__ import annotations
import os
from typing import Optional, Dict, Any

# Optional clients (import lazily)
_openai_client = None
_gemini_client = None

def which_provider() -> Optional[str]:
    prov = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if prov in {"openai", "gemini"}:
        return prov
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    return None

def get_llm_clients() -> Dict[str, Any]:
    """
    Returns {"provider":..., "client":..., "model":...} or {} if no keys.
    """
    provider = which_provider()
    if not provider:
        return {}

    model = os.environ.get("LLM_MODEL", "").strip()
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {}
        try:
            from openai import OpenAI
            global _openai_client
            _openai_client = _openai_client or OpenAI(api_key=api_key)
            if not model:
                model = "gpt-4o-mini"
            return {"provider": "openai", "client": _openai_client, "model": model}
        except Exception:
            return {}

    if provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return {}
        try:
            import google.generativeai as genai
            global _gemini_client
            if _gemini_client is None:
                genai.configure(api_key=api_key)
                _gemini_client = genai
            if not model:
                model = "gemini-1.5-flash"
            return {"provider": "gemini", "client": _gemini_client, "model": model}
        except Exception:
            return {}

    return {}
