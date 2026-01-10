"""
Chatbot module for News Constellation.
Uses vector embeddings from articles to provide intelligent responses via RAG.
Uses Gemini 3 Flash Preview exclusively.
"""

import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import dotenv

# Load environment variables
dotenv.load_dotenv()

print("🤖 Loading Chatbot Model... (Reusing same embedding model)")
_model = SentenceTransformer("all-MiniLM-L6-v2")

# API Keys
MOORCHEH_API_KEY = os.getenv("MOORCHEH_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# -----------------------------
# Embedding + Retrieval
# -----------------------------

def vectorize_query(query: str) -> np.ndarray:
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    return _model.encode([query])[0]


def find_similar_articles(
    query_vector: np.ndarray,
    articles: list,
    top_k: int = 5,
    similarity_threshold: float = 0.3,
):
    if not articles:
        return []

    articles_with_vectors = [
        a for a in articles if "vector" in a and a["vector"] is not None
    ]
    if not articles_with_vectors:
        return []

    article_vectors = np.array([a["vector"] for a in articles_with_vectors])
    similarities = cosine_similarity(
        query_vector.reshape(1, -1), article_vectors
    )[0]

    results = [
        (articles_with_vectors[i], float(similarities[i]))
        for i in range(len(similarities))
        if similarities[i] >= similarity_threshold
    ]

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


# -----------------------------
# Context Formatting
# -----------------------------

def _format_context_for_llm(similar_articles, graph=None) -> str:
    if not similar_articles:
        return "No relevant articles found."

    parts = []
    parts.append(
        f"Below are {len(similar_articles)} semantically relevant articles:\n"
    )

    for idx, (article, similarity) in enumerate(similar_articles, 1):
        title = article.get("title", "Unknown")
        url = article.get("url", "N/A")
        text = article.get("text", "")

        if len(text) > 1500:
            text = text[:1500] + "\n[... article continues ...]"

        parts.append("=" * 80)
        parts.append(f'ARTICLE {idx}: "{title}"')
        parts.append(f"URL: {url}")
        parts.append(f"Similarity: {similarity:.1%}")
        parts.append("=" * 80)
        parts.append("FULL ARTICLE TEXT:")
        parts.append(text)
        parts.append("")

    parts.append("=" * 80)
    parts.append(
        "INSTRUCTIONS: Answer ONLY using direct quotes from the article text above. "
        "Use quotation marks and cite the article title after each quote."
    )
    parts.append("=" * 80)

    return "\n".join(parts)


# -----------------------------
# Gemini 3 Flash Preview (ONLY)
# -----------------------------

def _query_gemini_api(
    query: str,
    context_text: str,
    similar_articles=None,
    chat_history=None,
) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)

    article_refs = ""
    if similar_articles:
        article_refs = "\n\nArticles found:\n"
        for i, (a, _) in enumerate(similar_articles, 1):
            article_refs += f'{i}. "{a.get("title", "Unknown")}" - {a.get("url", "N/A")}\n'

    conversation_context = ""
    if chat_history:
        recent = chat_history[-6:]
        conversation_context = "\n\nPrevious conversation:\n"
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "Assistant"
            conversation_context += f"{role}: {msg.get('content','')}\n"

    full_prompt = f"""
{context_text}
{article_refs}
{conversation_context}

Current User Question:
{query}

INSTRUCTIONS:
- Answer by DIRECTLY QUOTING the article text
- Use quotation marks for all quotes
- Cite the article title after each quote
- Use multiple quotes if multiple articles are relevant
- If information is missing, say so clearly
"""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=full_prompt,
    )

    return response.text


# -----------------------------
# Main RAG Orchestrator
# -----------------------------

def chat_with_constellation(
    user_query: str,
    articles: list,
    graph=None,
    chat_history=None,
    top_k: int = 5,
    similarity_threshold: float = 0.3,
    use_gemini: bool = True,
):
    if not user_query or not user_query.strip():
        return {
            "response": "Please provide a valid question.",
            "similar_articles": [],
            "context_used": "",
        }

    if not articles:
        return {
            "response": "No articles available in the constellation.",
            "similar_articles": [],
            "context_used": "",
        }

    try:
        query_vector = vectorize_query(user_query)

        similar_articles = find_similar_articles(
            query_vector,
            articles,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        if not similar_articles:
            return {
                "response": (
                    f"No relevant articles found "
                    f"(threshold: {similarity_threshold:.0%})."
                ),
                "similar_articles": [],
                "context_used": "",
            }

        context_text = _format_context_for_llm(similar_articles, graph)

        response = _query_gemini_api(
            user_query,
            context_text,
            similar_articles=similar_articles,
            chat_history=chat_history,
        )

        return {
            "response": response,
            "similar_articles": similar_articles,
            "context_used": context_text,
        }

    except Exception as e:
        return {
            "response": f"❌ Error processing query: {str(e)}",
            "similar_articles": [],
            "context_used": "",
        }
