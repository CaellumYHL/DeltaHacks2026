import streamlit as st
import streamlit.components.v1 as components
import os

# --- IMPORTS ---
from src.data_pipeline import get_full_articles
from src.math_engine import vectorize_articles, calculate_similarity
from src.graph_logic import build_network_graph, save_graph_html 
from src.ai_logic import query_moorcheh_and_gemini
# Import the updated Neutralizer logic
from src.literacy_logic import neutralize_content, classify_political_leaning

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="News Constellation Suite")

st.title("🌌 News Constellation Suite")

# --- TABS SETUP ---
tab_galaxy, tab_neutralizer = st.tabs(["🚀 The Galaxy Graph", "⚖️ The Bias Neutralizer"])

# ==========================================
# TAB 1: THE GALAXY (Graph App)
# ==========================================
with tab_galaxy:
    with st.container():
        col_controls, col_display = st.columns([1, 3])
        
        with col_controls:
            st.subheader("🔭 Telescope Controls")
            topic = st.text_input("Search Topic", "Artificial Intelligence")
            
            mode = st.radio("Data Source", ["Mock Data (Fast)", "Live NewsAPI (Real)"])
            use_mock = (mode == "Mock Data (Fast)")
            
            if st.button("🚀 Launch Galaxy", type="primary"):
                with st.spinner(f"Scanning the cosmos for '{topic}'..."):
                    raw_articles = get_full_articles(topic=topic, limit=30, mock=use_mock)
                    
                    if raw_articles:
                        st.session_state['articles'], vectors = vectorize_articles(raw_articles)
                        st.session_state['matrix'] = calculate_similarity(vectors)
                        st.success(f"Found {len(raw_articles)} stars!")
                    else:
                        st.error("No articles found. Try a different topic.")

            if 'articles' in st.session_state:
                threshold = st.slider("Gravity (Similarity Threshold)", 0.0, 1.0, 0.4, 0.05)

        with col_display:
            if 'articles' in st.session_state:
                G = build_network_graph(st.session_state['articles'], st.session_state['matrix'], threshold=threshold)
                html_file = save_graph_html(G, "galaxy.html")
                
                if html_file:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        html_data = f.read()
                    components.html(html_data, height=700)
                
                st.markdown("---")
                st.subheader("🤖 AI Analyst")
                user_query = st.text_input("Ask the galaxy a question about these articles:")
                if st.button("Analyze"):
                    if user_query:
                        with st.spinner("Analyzing..."):
                            response = query_moorcheh_and_gemini(user_query)
                            st.write(response)
            else:
                st.info("👈 Use the controls on the left to generate your galaxy.")

# ==========================================
# TAB 2: THE NEUTRALIZER (URL & Full Text)
# ==========================================
with tab_neutralizer:
    st.header("⚖️ The Bias Neutralizer")
    st.markdown("""
    **Media Literacy Tool:** Paste a URL below. Our system will read the **entire article**, 
    strip away the emotional manipulation, and rewrite it as pure facts.
    """)
    
    # Input Selection
    input_method = st.radio("Input Source:", ["Paste URL", "Paste Text"], horizontal=True)
    
    user_content = ""
    if input_method == "Paste URL":
        user_content = st.text_input("🔗 Article URL", placeholder="https://www.cnn.com/2024/...")
    else:
        user_content = st.text_area("📝 Article Text", height=200, placeholder="Paste the full article text here...")

    if st.button("Neutralize It ✨", type="primary"):
        if user_content:
            with st.spinner("Reading article and removing bias..."):
                
                # Check if we are sending a URL or raw text
                is_url_mode = (input_method == "Paste URL")
                
                # Call the logic
                # It returns 4 things: The Title, The Original Text (for display), The Neutral Text, and the political leaning
                title, original_text, neutral_text = neutralize_content(user_content, is_url=is_url_mode)
                leaning_result = classify_political_leaning(user_content, is_url=is_url_mode)


                if title == "Error":
                    st.error(neutral_text) # Display the error message
                else:
                    st.subheader(f"📄 Analysis: {title}")
                    
                    # Create a Side-by-Side Comparison
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        st.markdown("### 😡 Original (Biased)")
                        st.caption("Contains spin, opinions, and emotional triggers.")
                        # Use a text area so user can scroll through long articles
                        st.text_area("Original", original_text, height=600, disabled=True)
                    
                    with c2:
                        st.markdown("### 😐 Neutralized (Facts Only)")
                        st.caption("Rewritten by AI to be objective and factual.")
                        st.text_area("Neutralized", neutral_text, height=600, disabled=True)
                    
                    st.markdown("### 🧭 Political Framing Indicator")
                    if "Left" in leaning_result:
                        st.markdown("### 🔵 Left-Leaning Framing")
                    elif "Right" in leaning_result:
                        st.markdown("### 🔴 Right-Leaning Framing")
                    else:
                        st.markdown("### ⚪ Neutral Framing")
                    st.info(leaning_result)
                    st.caption("This classification reflects narrative framing, not factual accuracy or intent.")
        else:
            st.warning("Please provide a URL or Text first.")