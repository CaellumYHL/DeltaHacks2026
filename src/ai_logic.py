import os
import streamlit as st
from src.chatbot import chat_with_constellation

def query_moorcheh_and_gemini(user_question, chat_history=None):
    """
    Query the chatbot using articles and graph data from session state.
    Uses the vector embeddings from math_engine to find relevant articles through semantic search,
    then queries Gemini API to generate responses with direct quotes from the articles.
    
    Parameters:
    - user_question (str): The user's question
    - chat_history (list, optional): Previous conversation messages for context
    """
    # Get articles and graph from session state (populated by app.py)
    articles = st.session_state.get('articles', [])
    graph = st.session_state.get('graph', None)
    
    if not articles:
        return "⚠️ No articles available. Please generate a galaxy first by clicking '🚀 Launch Galaxy'."
    
    # Use the chatbot to get response
    # Use Gemini to get responses with direct quotes from articles
    result = chat_with_constellation(
        user_query=user_question,
        articles=articles,
        graph=graph,
        chat_history=chat_history,  # Pass conversation history for context
        top_k=5,
        similarity_threshold=0.3,
        use_gemini=True,  # Use Gemini to get direct quotes from articles
        moorcheh_namespace=None  # Optional: specify Moorcheh namespace if using remote vectors
    )
    
    return result.get('response', 'No response generated.')