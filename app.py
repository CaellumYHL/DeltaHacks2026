import streamlit as st
import streamlit.components.v1 as components
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from src.tts_logic import elevenlabs_tts_bytes

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Apogee AI")
load_dotenv()

# --- CSS ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

if os.path.exists("assets/styles.css"):
    load_css("assets/styles.css")

# --- DATA FUNCTIONS ---

# Keep this cached because inputs are simple strings/ints (fast to hash)
@st.cache_data(show_spinner=False)
def load_and_process_data(topic, months_back, use_mock):
    """Fetches articles and calculates vector similarity matrix."""
    from src.data_pipeline import get_full_articles
    from src.math_engine import vectorize_articles, calculate_similarity
    
    raw_articles = get_full_articles(topic=topic, limit=30, mock=use_mock, months_back=months_back)
    
    if raw_articles:
        articles, vectors = vectorize_articles(raw_articles)
        matrix = calculate_similarity(vectors)
        return articles, matrix
    return None, None

# REMOVED @st.cache_data here to prevent "Hashing Slowdown" on large datasets
def generate_graph_html(articles, matrix, threshold, color_mode):
    """Generates the PyVis graph HTML string."""
    from src.graph_logic import build_network_graph, save_graph_html
    
    G = build_network_graph(articles, matrix, threshold=threshold, color_mode=color_mode)
    html_file = save_graph_html(G, "galaxy.html")
    
    if html_file:
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    return None

# ==========================================
# 2. TTS FUNCTION (Lazy Load)
# ==========================================
@st.cache_data(show_spinner=False)
def cached_tts(text: str, voice_id: str) -> bytes:
    try:
        # Lazy import: Only loads the heavy ElevenLabs library when button is clicked
        from src.tts_logic import elevenlabs_tts_bytes
        
        # Call the function from your external file
        audio_data = elevenlabs_tts_bytes(text, voice_id=voice_id)
        return audio_data
    except Exception as e:
        st.error(f"TTS Error: {e}")
        return b""

# ==========================================
# 1. SIDEBAR
# ==========================================
with st.sidebar:
    sb_col1, sb_col2 = st.columns([1, 4])
    with sb_col1:
        if os.path.exists("assets/Apogee.png"):
            st.image("assets/Apogee.png", width=50)
        else:
            st.write("⭐")
    with sb_col2:
        st.markdown("### Apogee AI")
        st.caption("News Constellation")
    
    st.markdown("---")
    selected_page = st.radio(
        "Navigation", 
        ["Galaxy Graph", "Global Map", "Bias Neutralizer"],
        label_visibility="collapsed"
    )
    st.markdown("---")

# ==========================================
# 2. MAIN APP
# ==========================================
# Add this before you define the slider (e.g., near line 80)
if "months_input" not in st.session_state:
    st.session_state["months_input"] = 0

if selected_page == "Galaxy Graph":
    col_controls, col_display = st.columns([1, 3], gap="medium")

    # --- CONTROLS ---
    # --- CONTROLS ---
    with col_controls:
        with st.container(border=True):
            st.subheader("I!I Galaxy Controls")
            st.markdown("<br>", unsafe_allow_html=True)
            
            topic = st.text_input("Search Topic", "Artificial Intelligence")
            
            # --- FIXED SLIDER LOGIC ---
            # 1. Define callback to force reset in session state
            def reset_slider():
                st.session_state.months_input = 0

            # 2. Add 'key' to bind this slider to session state
            months_back = st.slider(
                "Months Back: 0", 
                0, 12,  
                key="months_input"
            )
            # --------------------------

            label_month = (datetime.now() - relativedelta(months=months_back)).strftime("%B %Y")
            st.caption(f"📅 {label_month}")
            st.markdown("---")
            
            mode = st.radio("Source", ["Mock Data", "Live API"], horizontal=True, label_visibility="collapsed")
            use_mock = (mode == "Mock Data")
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("**Gravity (Threshold): 0.40**")
            threshold = st.slider("Gravity", 0.0, 1.0, 0.4, 0.05, label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)

            color_option = st.selectbox("🎨 Color Stars By", ["Topic Clusters", "Sentiment", "Political Bias"])
            
            if "Sentiment" in color_option: selected_mode = "Sentiment"
            elif "Political" in color_option: selected_mode = "Politics"
            else: selected_mode = "Cluster"

            st.markdown("---")

            # 3. Add 'on_click' to trigger the reset BEFORE the script runs the scan
            if st.button("💫 Scanning Cosmos...", type="primary", use_container_width=True, on_click=reset_slider):
                
                # The spinner allows the UI to update (move slider) before code blocks
                with st.spinner(f"Scanning for '{topic}'..."):
                    
                    # 'months_back' is now guaranteed to be 0
                    articles, matrix = load_and_process_data(topic, months_back, use_mock)
        
                    # CLEAR old state first to prevent ghost data
                    st.session_state['last_graph_params'] = None 
        
                if articles:
                    st.session_state['articles'] = articles
                    st.session_state['matrix'] = matrix
                    st.success(f"Found {len(articles)} stars from {label_month}!")
                else:
                    st.session_state['articles'] = []
                    st.session_state['matrix'] = None
                    st.error(f"No articles found for {label_month}.")

    # --- DISPLAY ---
    with col_display:
        st.subheader("Galaxy Graph")
        st.caption("SEMANTIC ARTICLE TOPOLOGY")
        
        if 'articles' in st.session_state:
            # PERFORMANCE FIX: Manual State Management
            # We create a "signature" of the current settings
            current_params = (
            threshold, 
            selected_mode, 
            len(st.session_state['articles']), 
            months_back  # <--- ADD THIS
            )
            
            # If settings changed (or graph doesn't exist), regenerate HTML
            if ('last_graph_params' not in st.session_state) or (st.session_state['last_graph_params'] != current_params):
                
                # Only show spinner if we are actually doing work
                with st.spinner("Aligning stars..."):
                    html_content = generate_graph_html(
                        st.session_state['articles'], 
                        st.session_state['matrix'], 
                        threshold, 
                        selected_mode
                    )
                    st.session_state['graph_html'] = html_content
                    st.session_state['last_graph_params'] = current_params
            
            # Render the stored HTML (Instant)
            with st.container(border=True):
                if st.session_state.get('graph_html'):
                    components.html(st.session_state['graph_html'], height=600)
        
        else:
            with st.container(border=True):
                st.markdown(
                    """<div style='height: 600px; display: flex; align-items: center; justify-content: center; flex-direction: column; color: gray;'>
                    <h3>🌌</h3><p>Use the controls to generate your galaxy</p></div>""", 
                    unsafe_allow_html=True
                )

        # --- AI ANALYST ---
        st.markdown("---")
        st.subheader("🤖 AI Analyst")

        if 'articles' in st.session_state:
            user_query = st.text_input("Ask the galaxy a question:", key="ai_query")
            
            if "last_ai_response" not in st.session_state: st.session_state["last_ai_response"] = ""
            if "last_ai_audio" not in st.session_state: st.session_state["last_ai_audio"] = None

            if st.button("Analyze", key="ai_analyze"):
                if user_query.strip():
                    with st.spinner("Analyzing..."):
                        from src.ai_logic import query_moorcheh_and_gemini
                        response = query_moorcheh_and_gemini(user_query)
                        st.session_state["last_ai_response"] = response
                        st.session_state["last_ai_audio"] = None 
                else:
                    st.warning("Please type a question first.")

            if st.session_state["last_ai_response"]:
                with st.container(border=True):
                    st.markdown("#### 📝 Analysis")
                    st.write(st.session_state["last_ai_response"])
                    st.markdown("---")
                    if st.button("▶️ Read Aloud"):
                        script = f"Summary: {st.session_state['last_ai_response'][:200]}..."
                        st.session_state["last_ai_audio"] = cached_tts(script, "JBFqnCBsd6RMkjVDRZzb")
                    
                    if st.session_state.get("last_ai_audio"):
                        st.audio(st.session_state["last_ai_audio"], format="audio/mpeg")
        else:
            st.info("Launch the Galaxy to enable AI Analyst.")

# ==========================================
# PAGE: GLOBAL MAP
# ==========================================
elif selected_page == "Global Map":
    st.header("🌍 Global Map")
    if 'articles' in st.session_state:
        from src.map_logic import get_map_data, generate_3d_map
        map_df = get_map_data(st.session_state['articles'])
        if not map_df.empty:
            st.pydeck_chart(generate_3d_map(map_df))
            st.caption(f"Mapped {len(map_df)} articles.")
        else:
            st.warning("No location keywords found.")
    else:
        st.info("Please generate data in the 'Galaxy Graph' tab first.")

# ==========================================
# PAGE: BIAS NEUTRALIZER
# ==========================================
elif selected_page == "Bias Neutralizer":
    st.header("⚖️ Bias Neutralizer")
    col_input, col_result = st.columns([1, 1])
    with col_input:
        st.subheader("Input")
        input_method = st.radio("Source", ["Paste URL", "Paste Text"], horizontal=True)
        user_content = st.text_input("🔗 Article URL") if input_method == "Paste URL" else st.text_area("📝 Text", height=200)

        if st.button("Neutralize Article ✨", type="primary"):
            if user_content:
                with st.spinner("Removing bias..."):
                    from src.literacy_logic import neutralize_content, classify_political_leaning, format_analysis
                    is_url = (input_method == "Paste URL")
                    title, orig, neut = neutralize_content(user_content, is_url=is_url)
                    leaning = classify_political_leaning(user_content, is_url=is_url)
                    st.session_state['neut_results'] = {
                        'title': title, 'orig': orig, 'neut': neut, 'analysis': format_analysis(leaning)
                    }
            else:
                st.warning("Please provide content.")

    with col_result:
        if 'neut_results' in st.session_state:
            res = st.session_state['neut_results']
            if res['title'] == "Error":
                st.error(res['neut'])
            else:
                st.subheader(f"Results: {res['title']}")
                st.info(res['analysis'])
                with st.expander("Compare Texts", expanded=True):
                    c1, c2 = st.columns(2)
                    c1.text_area("Original", res['orig'], height=300)
                    c2.text_area("Neutralized", res['neut'], height=300)