# backend/coach_pipeline.py
from __future__ import annotations
from typing import List, Tuple

def answer_with_rules(question: str, context: str, max_tokens: int = 600) -> Tuple[str, List[str]]:
    """
    Very small, dependency-free answerer:
    - If we have context, echo a focused answer using that context.
    - If we don't have context, say so and suggest what to try.
    Returns (answer_text, suggestions_list).
    """
    q = (question or "").strip()
    ctx = (context or "").strip()

    if not q:
        return ("Please ask a question.", ["Try: \"Summarize the uploaded file\""])

    if not ctx:
        return (
            "I couldn’t find anything relevant in the uploaded files for that question.",
            [
                "Try a more specific query (e.g., exact field names).",
                "Ask me to summarize the document first.",
                "Re-upload the file to ensure it was indexed correctly.",
            ],
        )

    # Keep the answer within a size bound so the UI never explodes.
    # (You can replace this with a real LLM call later.)
    preview = ctx[: max(512, min(len(ctx), max_tokens * 2))]

    answer = (
        "Using your uploaded docs, here’s what’s relevant:\n\n"
        f"{preview}\n\n"
        "If you want me to extract specific fields, ask me explicitly "
        "(e.g., “What is the PNR?”, “What is the passenger name?”, “What is the fare?”)."
    )

    suggestions = [
        "Summarize the key fields (name/PNR/status/fare/dates).",
        "Translate the answer into another language.",
        "Show the exact lines that mention the field I asked about.",
    ]

    return answer, suggestions
