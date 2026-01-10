import os
from typing import List, Dict

import google.generativeai as genai

# Moorcheh SDK (the import name might differ slightly depending on their package)
from moorcheh import MoorchehClient  # <-- if this import errors, tell me the error


def _get_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing {name}. Put it in your .env and restart Streamlit.")
    return val


def _get_moorcheh_client() -> "MoorchehClient":
    api_key = _get_env("MOORCHEH_API_KEY")
    return MoorchehClient(api_key=api_key)


def _get_gemini_model():
    genai.configure(api_key=_get_env("GOOGLE_API_KEY"))
    return genai.GenerativeModel("gemini-1.5-flash")


def moorcheh_upsert_articles(articles: List[Dict], namespace: str) -> None:
    """
    Store articles in Moorcheh so we can retrieve them later.
    We store title/url/topic as metadata.
    """
    client = _get_moorcheh_client()

    # Prepare docs for Moorcheh
    docs = []
    for i, a in enumerate(articles):
        docs.append({
            "id": f"{namespace}-{i}",              # unique id
            "text": a.get("text", ""),             # searchable content
            "metadata": {
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "topic": namespace,
            }
        })

    # ---- IMPORTANT: this is the ONLY part that may vary by SDK ----
    # Common patterns: client.upsert(), client.ingest(), client.documents.upsert()
    client.upsert(namespace=namespace, documents=docs)
    # --------------------------------------------------------------


def moorcheh_search(question: str, namespace: str, top_k: int = 5) -> List[Dict]:
    """
    Retrieve relevant docs/chunks from Moorcheh for a question.
    """
    client = _get_moorcheh_client()

    # ---- IMPORTANT: this may vary by SDK ----
    results = client.search(namespace=namespace, query=question, top_k=top_k)
    # --------------------------------------------------------------

    # Normalize results to a list of dicts we can prompt with
    normalized = []
    for r in results:
        # adapt fields based on whatever the SDK returns
        normalized.append({
            "text": r.get("text", ""),
            "score": r.get("score", None),
            "metadata": r.get("metadata", {}),
        })
    return normalized


def query_moorcheh_and_gemini(user_question: str, topic_namespace: str) -> str:
    """
    1) Search Moorcheh for relevant context
    2) Ask Gemini to answer using ONLY that context
    """
    if not user_question.strip():
        return "Please type a question first."

    model = _get_gemini_model()
    hits = moorcheh_search(user_question, namespace=topic_namespace, top_k=6)

    if not hits:
        return "I couldn't find relevant context in memory. Try launching the galaxy again."

    # Build prompt context with citations
    context_blocks = []
    for i, h in enumerate(hits, start=1):
        md = h.get("metadata", {})
        title = md.get("title", "Untitled")
        url = md.get("url", "")
        excerpt = (h.get("text") or "")[:1200]
        context_blocks.append(f"[{i}] {title}\nURL: {url}\nExcerpt:\n{excerpt}\n")

    system = (
        "You are an AI analyst. Use ONLY the provided excerpts to answer. "
        "Do not invent facts. If not enough information, say so. "
        "Cite sources like [1], [2]."
    )

    prompt = f"""
QUESTION:
{user_question}

CONTEXT EXCERPTS:
{chr(10).join(context_blocks)}

FORMAT:
- Direct answer (2-4 sentences)
- Bullet key points
- Sources used: [#]
- What I'm least confident about: one sentence
"""

    resp = model.generate_content([system, prompt])
    return resp.text or "Gemini returned an empty response."
