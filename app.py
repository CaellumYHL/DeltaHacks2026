from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import streamlit.components.v1 as components
import os
import networkx as nx

# Import your modules
from src.data_pipeline import get_full_articles
from src.math_engine import vectorize_articles, calculate_similarity
from src.graph_logic import build_network_graph, save_graph_html
from src.ai_logic import query_moorcheh_and_gemini, moorcheh_upsert_articles

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
            # A. Scrape
            raw_articles = get_full_articles(topic=topic, limit=10, mock=use_mock)

            if raw_articles:
                # Store in session for graph
                st.session_state['articles'], vectors = vectorize_articles(raw_articles)
                st.session_state['matrix'] = calculate_similarity(vectors)

                # STORE IN MOORCHEH MEMORY (step 2)
                # namespace can just be the topic string (or topic + timestamp)
                moorcheh_upsert_articles(raw_articles, namespace=topic)

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
        
        # Save & Render
        html_file = save_graph_html(G, "galaxy.html")
        with open(html_file, 'r', encoding='utf-8') as f:
            html_data = f.read()
            
        # Display
        st.subheader(f"3D Map: {topic}")
        components.html(html_data, height=700)
    else:
        st.info("👈 Enter a topic and click 'Launch' to begin.")

# 3. RIGHT PANEL: AI Chat
with col2:
    st.subheader("🤖 AI Analyst")
    user_query = st.text_area("Ask the galaxy a question:", height=100)
    
    if st.button("Ask Analyst"):
        if user_query:
            with st.spinner("Analyzing..."):
                # Call Moorcheh + Gemini
                response = query_moorcheh_and_gemini(user_query, topic_namespace=topic)
                st.write(response)
        else:
            st.warning("Please type a question first.")