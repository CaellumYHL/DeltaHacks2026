import streamlit as st
import streamlit.components.v1 as components
from src.data_pipeline import fetch_news_urls
from src.graph_logic import build_graph, save_pyvis_html
from src.ai_logic import query_moorcheh_and_gemini

st.set_page_config(layout="wide", page_title="News Constellation")

st.title("🌌 News Constellation")

# Sidebar
with st.sidebar:
    topic = st.text_input("Topic", "Artificial Intelligence")
    if st.button("Generate Galaxy"):
        st.session_state['articles'] = fetch_news_urls(topic)
        # In real version, we would generate vectors here too

# Main Area
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 3D Knowledge Graph")
    if 'articles' in st.session_state:
        # Build and display graph
        G = build_graph(st.session_state['articles'], [])
        html_file = save_pyvis_html(G)
        
        # Read the HTML file
        with open(html_file, 'r', encoding='utf-8') as f:
            html_data = f.read()
        components.html(html_data, height=600)
    else:
        st.info("Enter a topic and click Generate to see the galaxy.")

with col2:
    st.markdown("###  Analyst Chat")
    user_query = st.text_input("Ask the galaxy a question:")
    if user_query:
        response = query_moorcheh_and_gemini(user_query)
        st.write(response)