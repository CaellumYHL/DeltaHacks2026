import streamlit as st
import streamlit.components.v1 as components
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv



# --- PAGE CONFIG (Must be first) ---
st.set_page_config(layout="wide", page_title="CLARE.io")

# Load env immediately so keys are ready
load_dotenv()

# --- CSS INJECTION ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Load the external CSS file (Make sure the path matches your project structure)
load_css("assets/styles.css")

# --- CACHED FUNCTIONS ---
@st.cache_data(show_spinner=False)
def cached_tts(text: str, voice_id: str) -> bytes:
    return elevenlabs_tts_bytes(text, voice_id=voice_id)


# Create two columns: one narrow for the logo, one wide for the text
col1, col2 = st.columns([1, 15]) # Adjust the ratio (1:15) based on logo size

with col1:
    # Replace "assets/logo.png" with your actual file path
    st.image("assets/logo-design.jpg", width=60) 

with col2:
    st.title("CLARE.io")

# --- TABS SETUP ---
tab_galaxy, tab_neutralizer = st.tabs(["News Constellation", "Bias Neutralizer"])

# ==========================================
# TAB 1: THE GALAXY (Graph App)
# ==========================================
with tab_galaxy:
    with st.container():
        col_controls, col_display = st.columns([1, 3])
        
        with col_controls:
            st.subheader("Telescope Controls")
            topic = st.text_input("Search Topic", "Artificial Intelligence")

            # Date Logic (Fast, keep at top level)
            months_back = st.slider("Months back", 0, 12, 0)
            label_month = (datetime.now() - relativedelta(months=months_back)).strftime("%B %Y")
            st.caption(f"Showing articles from: **{label_month}**")
            
            mode = st.radio("Data Source", ["Mock Data (Fast)", "Live NewsAPI (Real)"])
            use_mock = (mode == "Mock Data (Fast)")
            
            if st.button("🚀 Launch Galaxy", type="primary"):
                with st.spinner(f"Scanning the cosmos for '{topic}'..."):
                    # --- LAZY IMPORTS 1: The Data Pipeline & Math Engine ---
                    from src.data_pipeline import get_full_articles
                    from src.math_engine import vectorize_articles, calculate_similarity 
                    
                    raw_articles = get_full_articles(topic=topic, limit=30, mock=use_mock, months_back=months_back)
                    
                    if raw_articles:
                        st.session_state['articles'], vectors = vectorize_articles(raw_articles)
                        st.session_state['matrix'] = calculate_similarity(vectors)
                        st.success(f"Found {len(raw_articles)} stars!")
                    else:
                        st.error("No articles found. Try a different topic.")

            # --- VIEW CONTROLS ---
            if 'articles' in st.session_state:
                st.markdown("---")
                st.subheader("View Mode")
                view_mode = st.radio("Select Visualization:", ["🕸️ Network Graph", "🌍 Global Map"])

                if view_mode == "🕸️ Network Graph":
                    threshold = st.slider("Gravity", 0.0, 1.0, 0.4, 0.05)
                    st.subheader("Truth Filters")
                    color_option = st.radio("Color Stars By:", 
                                            ["Topic Clusters", "Sentiment", "Political Bias"])
                    
                    if "Sentiment" in color_option: selected_mode = "Sentiment"
                    elif "Political" in color_option: selected_mode = "Politics"
                    else: selected_mode = "Cluster"
                else:
                    st.info("Visualizing article locations on a 3D Earth.")

        with col_display:
            if 'articles' in st.session_state:
                
                # --- VISUALIZATION LOGIC ---
                if view_mode == "🕸️ Network Graph":
                    from src.graph_logic import build_network_graph, save_graph_html
                    
                    G = build_network_graph(
                        st.session_state['articles'], 
                        st.session_state['matrix'], 
                        threshold=threshold,
                        color_mode=selected_mode
                    )
                    html_file = save_graph_html(G, "galaxy.html")
                    if html_file:
                        with open(html_file, 'r', encoding='utf-8') as f:
                            components.html(f.read(), height=700)
                
                elif view_mode == "🌍 Global Map":
                    from src.map_logic import get_map_data, generate_3d_map
                    
                    map_df = get_map_data(st.session_state['articles'])
                    if not map_df.empty:
                        st.subheader("🌍 The Global Newsroom")
                        st.pydeck_chart(generate_3d_map(map_df))
                        st.caption(f"Mapped {len(map_df)} articles.")
                    else:
                        st.warning("No location keywords found in these articles.")

                # --- AI ANALYST ---
                st.markdown("---")
                st.subheader("🤖 AI Analyst")
                user_query = st.text_input("Ask the galaxy a question:", key="ai_query")

                # Ensure state exists
                if "last_ai_response" not in st.session_state:
                    st.session_state["last_ai_response"] = ""

                if "last_ai_audio" not in st.session_state:
                    st.session_state["last_ai_audio"] = None

                # ---- ANALYZE ----
                if st.button("Analyze", key="ai_analyze"):
                    if user_query.strip():
                        with st.spinner("Analyzing..."):
                            from src.ai_logic import query_moorcheh_and_gemini
                            
                            response = query_moorcheh_and_gemini(user_query)
                            st.session_state["last_ai_response"] = response
                            st.session_state["last_ai_audio"] = None
                            st.session_state["last_ai_audio"] = None 
                    else:
                        st.warning("Please type a question first.")

                # ---- DISPLAY RESPONSE ----
                if st.session_state["last_ai_response"]:
                    st.write(st.session_state["last_ai_response"])

                    st.markdown("#### 🎙️ Voice")

                    VOICE_PRESETS = {
                        "Anchor (Default)": "JBFqnCBsd6RMkjVDRZzb",
                        "Calm Narrator": "EXAVITQu4vr4xnSDxMaL",
                        "Energetic Host": "TxGEqnHWrfWFTfGW9XjX",
                    }

                    voice_name = st.selectbox("Voice", list(VOICE_PRESETS.keys()))
                    voice_id = VOICE_PRESETS[voice_name]

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        listen = st.button("▶️ Listen", use_container_width=True)

                    with col2:
                        clear = st.button("🧹 Clear", use_container_width=True)

                    with col3:
                        regen = st.button("🔁 Re-generate", use_container_width=True)

                    if clear:
                        st.session_state["last_ai_audio"] = None

                    if (listen or regen):
                        try:
                            with st.spinner("Generating voice..."):
                                script = f"""
                                You are a professional news anchor.
                                Read the following summary clearly and naturally.

                                {st.session_state["last_ai_response"]}
                                """
                                st.session_state["last_ai_audio"] = cached_tts(script, voice_id)
                        except Exception as e:
                            st.error(f"Voice failed: {e}")

                # ---- AUDIO PLAYER ----
                if st.session_state.get("last_ai_audio"):
                    st.audio(st.session_state["last_ai_audio"], format="audio/mpeg")

                    st.download_button(
                        "⬇️ Download MP3",
                        data=st.session_state["last_ai_audio"],
                        file_name="news_summary.mp3",
                        mime="audio/mpeg",
                        use_container_width=True
                    )

            else:
                st.info("Use the controls on the left to generate your galaxy.")

# ==========================================
# TAB 2: THE NEUTRALIZER
# ==========================================
with tab_neutralizer:
    st.header("⚖️ Article Analysis & Bias Neutralization")
    st.markdown("Paste a URL below to strip away manipulation.")
    
    input_method = st.radio("Input Source:", ["Paste URL", "Paste Text"], horizontal=True)
    user_content = st.text_input("🔗 Article URL") if input_method == "Paste URL" else st.text_area("📝 Article Text", height=200)

    if st.button("Neutralize Article ✨", type="primary"):
        if user_content:
            with st.spinner("Reading article and removing bias..."):
                from src.literacy_logic import neutralize_content, classify_political_leaning, format_analysis
                
                is_url_mode = (input_method == "Paste URL")
                title, orig, neut = neutralize_content(user_content, is_url=is_url_mode)
                leaning_result = classify_political_leaning(user_content, is_url=is_url_mode)
                formatted_output = format_analysis(leaning_result)

                if title == "Error":
                    st.error(neut) 
                else:
                    st.subheader(f"📄 Analysis: {title}")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 😡 Original")
                        st.text_area("Original", orig, height=600, disabled=True)
                    with c2:
                        st.markdown("### 😐 Neutralized")
                        st.text_area("Neutralized", neut, height=600, disabled=True)
                    
                    st.info(formatted_output)
        else:
            st.warning("Please provide a URL or Text first.")