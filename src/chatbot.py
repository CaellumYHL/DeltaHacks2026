"""
Chatbot module for News Constellation.
Uses vector embeddings from articles to provide intelligent responses via RAG.
"""
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Reuse the same model from math_engine for consistency
# This ensures query vectors are in the same embedding space as article vectors
print("🤖 Loading Chatbot Model... (Reusing same embedding model)")
_model = SentenceTransformer('all-MiniLM-L6-v2')

# API Keys
MOORCHEH_API_KEY = os.getenv("MOORCHEH_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def vectorize_query(query):
    """
    Convert a text query to a vector using the same model as articles.
    
    Parameters:
    - query (str): Text query
    
    Returns:
    - numpy array of the query vector (384-dimensional for all-MiniLM-L6-v2)
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    # Use the same model and encoding approach as articles
    query_vector = _model.encode([query])[0]
    return query_vector


def find_similar_articles(query_vector, articles, top_k=5, similarity_threshold=0.3):
    """
    Find articles similar to a query vector using cosine similarity.
    
    Parameters:
    - query_vector (np.ndarray): Vector representation of the query
    - articles (List[Dict]): List of articles, each must have a 'vector' key
    - top_k (int): Number of results to return
    - similarity_threshold (float): Minimum similarity score (0-1)
    
    Returns:
    - List of (article_dict, similarity_score) tuples, sorted by similarity (highest first)
    """
    if not articles:
        return []
    
    # Check that articles have vectors
    articles_with_vectors = [art for art in articles if 'vector' in art and art['vector'] is not None]
    if not articles_with_vectors:
        return []
    
    # Extract vectors as numpy array
    article_vectors = np.array([art['vector'] for art in articles_with_vectors])
    
    # Reshape query_vector to 2D for cosine_similarity
    query_vector_2d = query_vector.reshape(1, -1)
    
    # Calculate cosine similarity
    similarities = cosine_similarity(query_vector_2d, article_vectors)[0]
    
    # Create tuples of (article, similarity_score)
    results = [
        (articles_with_vectors[i], float(similarities[i]))
        for i in range(len(articles_with_vectors))
        if similarities[i] >= similarity_threshold
    ]
    
    # Sort by similarity (highest first) and return top_k
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def _query_moorcheh_api(query, context_text, namespace=None):
    """
    Query Moorcheh API with context from similar articles.
    
    Parameters:
    - query (str): User's question
    - context_text (str): Formatted context from similar articles
    - namespace (str, optional): Moorcheh namespace if using remote vectors
    
    Returns:
    - str: Generated response
    """
    try:
        # Try different import patterns for Moorcheh SDK
        try:
            from moorcheh_sdk import MoorchehClient
            client = MoorchehClient(api_key=MOORCHEH_API_KEY)
        except ImportError:
            try:
                from moorcheh.client import Moorcheh
                client = Moorcheh(api_key=MOORCHEH_API_KEY)
            except ImportError:
                raise ImportError("moorcheh-sdk not installed. Run: pip install moorcheh-sdk")
        
        if not MOORCHEH_API_KEY:
            raise ValueError("MOORCHEH_API_KEY not found in environment variables")
        
        # System prompt for news analysis
        system_prompt = """You are an AI news analyst for the News Constellation project. 
        You analyze articles and provide insightful, accurate summaries and answers based on the provided context.
        Always cite specific articles when possible and highlight different perspectives."""
        
        # Build the full prompt with context
        full_prompt = f"""Context from relevant articles:
{context_text}

User Question: {query}

Based on the context above, provide a comprehensive and insightful answer. If the context doesn't contain relevant information, say so clearly."""
        
        # Try different API patterns based on SDK version
        try:
            # If namespace is provided, use Moorcheh's RAG search
            if namespace:
                # Use Moorcheh's built-in RAG with the namespace
                if hasattr(client, 'query'):
                    response = client.query(
                        query=query,
                        namespaces=[namespace],
                        system_prompt=system_prompt,
                        top_k=5
                    )
                elif hasattr(client, 'search'):
                    results = client.search(
                        namespaces=[namespace],
                        query=query,
                        top_k=5
                    )
                    response = f"Found relevant articles in namespace. {full_prompt}"
                else:
                    response = full_prompt  # Fallback to context-only
            else:
                # Use direct chat completion with context
                if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                    response = client.chat.completions.create(
                        model="default",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": full_prompt}
                        ]
                    )
                    if hasattr(response, 'choices') and len(response.choices) > 0:
                        response = response.choices[0].message.content
                    elif isinstance(response, str):
                        response = response
                    else:
                        response = str(response)
                elif hasattr(client, 'generate'):
                    response = client.generate(
                        prompt=full_prompt,
                        system_prompt=system_prompt
                    )
                else:
                    # Fallback: return context with a note
                    response = f"{system_prompt}\n\n{full_prompt}\n\nNote: Moorcheh API structure not recognized. Using context directly."
            
            # Ensure response is a string
            if not isinstance(response, str):
                response = str(response)
            
            return response
            
        except AttributeError as e:
            # If API methods don't match expected structure, provide helpful error
            raise Exception(f"Moorcheh API method not found. SDK structure may have changed. Error: {str(e)}")
        
    except ImportError as e:
        raise ImportError(f"moorcheh-sdk not installed or import failed. Run: pip install moorcheh-sdk. Error: {str(e)}")
    except Exception as e:
        raise Exception(f"Moorcheh API error: {str(e)}")


def _query_gemini_api(query, context_text, similar_articles=None, chat_history=None):
    """
    Query Gemini 3 Flash Preview ONLY.
    No legacy SDK, no fallbacks.
    """

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Article references
    article_refs = ""
    if similar_articles:
        article_refs = "\n\nArticles:\n"
        for i, (a, _) in enumerate(similar_articles, 1):
            article_refs += f"{i}. {a.get('title')} ({a.get('url')})\n"

    # Conversation history (last 6 messages)
    history_block = ""
    if chat_history:
        history_block = "\n\nConversation history:\n"
        for msg in chat_history[-6:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_block += f"{role}: {msg.get('content')}\n"

    full_prompt = f"""
{context_text}
{article_refs}
{history_block}

USER QUESTION:
{query}

INSTRUCTIONS:
- Answer ONLY using the article text above
- Quote directly using quotation marks
- Cite article titles after quotes
"""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=full_prompt
    )

    return response.text


def _format_context_for_llm(similar_articles, graph=None):
    """
    Format similar articles into a context string for the LLM.
    Includes full article text so Gemini can quote directly from it.
    
    Parameters:
    - similar_articles (List[Tuple]): List of (article_dict, similarity_score) tuples
    - graph (NetworkX Graph, optional): Graph object for cluster information
    
    Returns:
    - str: Formatted context text with clear article identifiers
    """
    if not similar_articles:
        return "No relevant articles found in the constellation."
    
    context_parts = []
    context_parts.append(f"Below are {len(similar_articles)} relevant article(s) found through semantic search:\n")
    
    for idx, (article, similarity) in enumerate(similar_articles, 1):
        cluster_info = ""
        if graph:
            # Try to find the node in the graph by matching title or index
            for node_id in graph.nodes():
                if graph.nodes[node_id].get('label') == article.get('title'):
                    cluster_id = graph.nodes[node_id].get('group', 'unknown')
                    cluster_info = f" [Cluster: {cluster_id}]"
                    break
        
        # Create a clear article identifier for referencing
        article_title = article.get('title', 'Unknown')
        article_url = article.get('url', 'N/A')
        
        context_parts.append(f"\n{'='*80}")
        context_parts.append(f"ARTICLE {idx}: \"{article_title}\"")
        context_parts.append(f"URL: {article_url}")
        context_parts.append(f"Similarity Score: {similarity:.1%}{cluster_info}")
        context_parts.append(f"{'='*80}")
        
        # Include more article text so Gemini can quote from it
        # Increase from 800 to 1500 characters for better context
        text = article.get('text', '')
        if len(text) > 1500:
            text_preview = text[:1500] + "\n[... article continues ...]"
        else:
            text_preview = text
        
        context_parts.append(f"FULL ARTICLE TEXT:\n{text_preview}\n")
    
    context_parts.append(f"\n{'='*80}")
    context_parts.append("INSTRUCTIONS: When answering, you MUST quote directly from the article text above.")
    context_parts.append("Cite articles by their title (e.g., 'According to \"[Article Title]\"...')")
    context_parts.append(f"{'='*80}")
    
    return "\n".join(context_parts)


def chat_with_constellation(user_query, articles, graph=None, chat_history=None, top_k=5, similarity_threshold=0.3, 
                           use_gemini=False, moorcheh_namespace=None):
    """
    Main function that orchestrates the entire RAG pipeline.
    
    This function:
    1. Vectorizes the user query
    2. Finds similar articles using cosine similarity
    3. Formats context from similar articles
    4. Queries Moorcheh API (or Gemini) to generate a response
    
    Parameters:
    - user_query (str): The user's question
    - articles (List[Dict]): List of article dictionaries, each must have a 'vector' key
    - graph (NetworkX Graph, optional): The graph object for cluster context
    - chat_history (list, optional): Previous conversation messages for context
    - top_k (int): Number of similar articles to retrieve (default: 5)
    - similarity_threshold (float): Minimum similarity score (default: 0.3)
    - use_gemini (bool): If True, use Gemini API instead of Moorcheh (default: False)
    - moorcheh_namespace (str, optional): Moorcheh namespace if using remote vectors
    
    Returns:
    - Dictionary with:
      - 'response' (str): The AI-generated response
      - 'similar_articles' (List[Tuple]): List of (article_dict, similarity_score) tuples
      - 'context_used' (str): The formatted context sent to the LLM
    """
    if not user_query or not user_query.strip():
        return {
            "response": "Please provide a valid question.",
            "similar_articles": [],
            "context_used": ""
        }
    
    if not articles:
        return {
            "response": "No articles available in the constellation. Please generate a galaxy first.",
            "similar_articles": [],
            "context_used": ""
        }
    
    try:
        # Step 1: Vectorize the query
        query_vector = vectorize_query(user_query)
        
        # Step 2: Find similar articles
        similar_articles = find_similar_articles(
            query_vector, 
            articles, 
            top_k=top_k, 
            similarity_threshold=similarity_threshold
        )
        
        if not similar_articles:
            return {
                "response": f"No relevant articles found for your query (similarity threshold: {similarity_threshold:.0%}). Try rephrasing your question or lowering the threshold.",
                "similar_articles": [],
                "context_used": ""
            }
        
        # Step 3: Format context
        context_text = _format_context_for_llm(similar_articles, graph)
        
        # Step 4: Generate response using LLM
        # Based on semantic search results, we know which articles are relevant
        # Pass this info to Gemini so it can quote from the correct articles
        if use_gemini:
            if not GEMINI_API_KEY:
                response = "⚠️ Gemini API key not configured. Please set GEMINI_API_KEY in your .env file."
            else:
                # Pass similar_articles and chat_history so Gemini knows which articles to quote from and maintains context
                response = _query_gemini_api(user_query, context_text, similar_articles=similar_articles, chat_history=chat_history)
        else:
            # Try Moorcheh first, fallback to Gemini if available
            if MOORCHEH_API_KEY:
                try:
                    response = _query_moorcheh_api(user_query, context_text, namespace=moorcheh_namespace)
                except Exception as e:
                    # Fallback to Gemini if Moorcheh fails
                    if GEMINI_API_KEY:
                        print(f"⚠️ Moorcheh API error: {e}. Falling back to Gemini...")
                        # Pass similar_articles and chat_history so Gemini knows which articles to quote from and maintains context
                        response = _query_gemini_api(user_query, context_text, similar_articles=similar_articles, chat_history=chat_history)
                    else:
                        response = f"⚠️ API error: {str(e)}. Please check your API keys."
            elif GEMINI_API_KEY:
                print("⚠️ Moorcheh API key not found. Using Gemini as fallback...")
                # Pass similar_articles and chat_history so Gemini knows which articles to quote from and maintains context
                response = _query_gemini_api(user_query, context_text, similar_articles=similar_articles, chat_history=chat_history)
            else:
                # No API keys available - provide a response based on context alone
                response = f"""Based on the articles in the constellation, I found {len(similar_articles)} relevant article(s).

Here's what I found:
{context_text}

Note: To get AI-generated summaries and analysis with direct quotes, please configure either MOORCHEH_API_KEY or GEMINI_API_KEY in your .env file."""
        
        return {
            "response": response,
            "similar_articles": similar_articles,
            "context_used": context_text
        }
        
    except Exception as e:
        return {
            "response": f"❌ Error processing query: {str(e)}",
            "similar_articles": [],
            "context_used": ""
        }