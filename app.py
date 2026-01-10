import streamlit as st
import streamlit.components.v1 as components
import os
import networkx as nx

# --- FIXED IMPORTS ---
from src.data_pipeline import get_full_articles  # Use this, NOT fetch_news_urls
from src.math_engine import vectorize_articles, calculate_similarity
from src.graph_logic import build_network_graph, save_graph_html 
from src.ai_logic import query_moorcheh_and_gemini

# Page Config
st.set_page_config(layout="wide", page_title="News Constellation")

# 1. SIDEBAR: Controls
with st.sidebar:
    st.title("🌌 Constellation")
    topic = st.text_input("Search Topic", "Artificial Intelligence")
    
    # Simple "Mode" Toggle
    mode = st.radio("Data Source", ["Mock Data (Fast)", "Live NewsAPI (Real)"])
    use_mock = (mode == "Mock Data (Fast)")
    
    if st.button("🚀 Launch Galaxy", type="primary"):
        with st.spinner(f"Scanning the cosmos for '{topic}'..."):
            # A. Scrape (We must use get_full_articles, NOT fetch_news_urls)
            raw_articles = get_full_articles(topic=topic, limit=30, mock=use_mock)
            
            if raw_articles:
                # B. Math
                st.session_state['articles'], vectors = vectorize_articles(raw_articles)
                st.session_state['matrix'] = calculate_similarity(vectors)
                st.success(f"Found {len(raw_articles)} stars!")
            else:
                st.error("No articles found. Try a different topic.")

# 2. MAIN PANEL: The 3D Graph
col1, col2 = st.columns([3, 1])

with col1:
    if 'articles' in st.session_state:
        # User controls the "Gravity" (Threshold)
        threshold = st.slider("Connection Strength (Similarity Threshold)", 0.0, 1.0, 0.4, 0.05)
        
        # Build Graph
        G = build_network_graph(st.session_state['articles'], st.session_state['matrix'], threshold=threshold)
        st.session_state['graph'] = G  # Store graph for chatbot access
        
        # Save & Render
        html_file = save_graph_html(G, "galaxy.html")
        if html_file:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_data = f.read()
            st.subheader(f"3D Map: {topic}")
            components.html(html_data, height=700)
    else:
        st.info("👈 Enter a topic and click 'Launch' to begin.")

# 3. RIGHT PANEL: AI Chat
with col2:
    st.subheader("🤖 AI Analyst Chat")
    
    # Initialize conversation history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history in a scrollable container
    # Show welcome message if no history
    if len(st.session_state.chat_history) == 0:
        st.info("💬 Ask me anything about the articles in your constellation!")
    
    # Display all messages in the chat
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            with st.chat_message("user"):
                st.write(message['content'])
        elif message['role'] == 'assistant':
            with st.chat_message("assistant"):
                st.write(message['content'])
    
    # Chat input - handle new messages
    user_query = st.chat_input("Ask about the articles...")
    
    if user_query:
        # Add user message to history immediately
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_query
        })
        
        # Get response from chatbot - pass full history for context (including the current message)
        with st.spinner("Analyzing articles..."):
            response = query_moorcheh_and_gemini(user_query, st.session_state.chat_history)
        
        # Add assistant response to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response
        })
        
        # Rerun to display the new messages
        st.rerun()
    
    # Clear chat button (outside the chat input handler)
    if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()