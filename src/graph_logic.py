import networkx as nx
from pyvis.network import Network
import community.community_louvain as community_louvain
import os
import numpy as np
from textblob import TextBlob
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from urllib.parse import urlparse
from collections import Counter

# --- HELPER: SENTIMENT COLOR (Red=Bad, Green=Good) ---
def get_sentiment_color(text):
    blob = TextBlob(text)
    score = blob.sentiment.polarity # -1.0 to 1.0
    normalized = (score + 1) / 2
    cmap = cm.get_cmap('RdYlGn')
    rgba = cmap(normalized)
    return mcolors.to_hex(rgba)

# --- HELPER: POLITICAL COLOR (Blue=Left, Red=Right) ---
def get_political_color(url):
    domain = urlparse(url).netloc.lower()
    left_wing = ['cnn.com', 'msnbc.com', 'huffpost.com', 'vox.com', 'guardian.com', 'nytimes.com', 'bbc.com', 'washingtonpost.com']
    right_wing = ['foxnews.com', 'breitbart.com', 'nypost.com', 'dailymail.co.uk', 'washingtontimes.com', 'wsj.com']
    
    for site in left_wing:
        if site in domain: return "#3498db" # BLUE
    for site in right_wing:
        if site in domain: return "#e74c3c" # RED
    return "#95a5a6" # GREY

# --- NEW HELPER: CLICKBAIT CALCULATOR (Heuristic) ---
def calculate_clickbait_score(headline):
    """
    Returns a score 0-100 based on sensationalism heuristics.
    """
    score = 0
    if not headline: return 0
    
    # 1. Caps Lock Ratio (e.g. "SHOCKING")
    caps_count = sum(1 for c in headline if c.isupper())
    if len(headline) > 5 and (caps_count / len(headline) > 0.3):
        score += 30
        
    # 2. Punctuation Abuse (e.g. "!!", "??")
    if "!" in headline: score += 15
    if "?" in headline: score += 10
    
    # 3. Trigger Words
    triggers = ["shocking", "destroyed", "slammed", "secret", "miracle", "finally", 
                "you won't believe", "worst", "best", "exposed", "panic"]
    if any(t in headline.lower() for t in triggers):
        score += 25
        
    return min(score, 100)

# --- NEW HELPER: THEME EXTRACTOR ---
def get_cluster_theme(articles_in_cluster):
    stop_words = set(['the', 'and', 'to', 'of', 'a', 'in', 'is', 'for', 'on', 'with', 'at', 'by', 'an', 'be', 'from', 'that', 'it', 'as', 'are', 'this', 'was', 'or', 'new', 'how', 'why', 'what', 'who', 'when', 'where', 'video', 'watch'])
    all_words = []
    for art in articles_in_cluster:
        words = set(art['title'].lower().split()) 
        filtered = [w for w in words if w.isalpha() and w not in stop_words and len(w) > 2]
        all_words.extend(filtered)
    
    if not all_words: return "Cluster"
    
    # Top 2 most frequent words
    most_common = Counter(all_words).most_common(2)
    # Join with a newline for a nice box shape
    theme_label = "\n".join([w[0].title() for w in most_common])
    return theme_label

def build_network_graph(articles, sim_matrix, threshold=0.4, color_mode="Cluster"):
    print(f"🕸️ Building Graph (Threshold: {threshold}, Mode: {color_mode})...")
    G = nx.Graph()

    rows, cols = sim_matrix.shape
    DEFAULT_IMG = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/1200px-Wikipedia-logo-v2.svg.png"

    # 1. Add Nodes
    for i, art in enumerate(articles):
        
        # Perspective Flip Logic
        sim_scores = sim_matrix[i].copy()
        sim_scores[i] = 1.0 
        counterpoint_idx = np.argmin(sim_scores)
        counterpoint_art = articles[counterpoint_idx]
        
        img_url = art.get('image') or DEFAULT_IMG

        # --- CLICKBAIT SCORE CALCULATION ---
        cb_score = calculate_clickbait_score(art['title'])
        
        # Color code the score for the tooltip
        cb_color = "#2ecc71" # Green (Safe)
        cb_label = "Reliable"
        if cb_score > 30: 
            cb_color = "#f1c40f" # Yellow
            cb_label = "Sensational"
        if cb_score > 60: 
            cb_color = "#e74c3c" # Red
            cb_label = "High Clickbait"

        # --- UPDATED TOOLTIP HTML ---
        tooltip_html = (
            f"<div style='font-family: Arial; min-width: 200px;'>"
            f"   <b>{art['title']}</b><br>"
            f"   <span style='font-size: 10px; color: gray;'>{art['url'][:30]}...</span><br>"
            
            # NEW: Clickbait Meter
            f"   <div style='margin-top: 5px; margin-bottom: 8px; font-size: 12px; border: 1px solid #444; padding: 4px; border-radius: 4px;'>"
            f"      <span style='color: #bbb;'>Clickbait Score: </span>"
            f"      <span style='color: {cb_color}; font-weight: bold;'>{cb_score}% ({cb_label})</span>"
            f"   </div>"
            
            f"   🔗 <a href='{art['url']}' target='_blank' style='color: #4da6ff; text-decoration: none;'><b>Read This Article</b></a><br><br>"
            
            f"   <div style='background-color: #2c2c2c; padding: 8px; border-radius: 5px; margin-top: 5px;'>"
            f"      <span style='font-size: 12px; color: #ff9f43;'><b>🔄 Perspective Flip</b></span><br>"
            f"      <span style='font-size: 10px; color: #ccc;'>Different Viewpoint:</span><br>"
            f"      <a href='{counterpoint_art['url']}' target='_blank' style='color: #ff9f43; text-decoration: none;'>{counterpoint_art['title']}</a>"
            f"   </div>"
            f"</div>"
        )
        
        # --- COLOR LOGIC SWITCH ---
        node_color = None
        if color_mode == "Sentiment":
            node_color = get_sentiment_color(art['title'] + " " + art['text'][:200])
        elif color_mode == "Politics":
            node_color = get_political_color(art['url'])
        
        node_attrs = {
            'label': art['title'], 
            'title': tooltip_html, 
            'url': art['url'],
            'shape': 'circularImage',
            'image': img_url
        }
        
        if node_color:
            node_attrs['color'] = node_color
            
        G.add_node(int(i), **node_attrs)

    # Pass 1: Strong Edges
    for i in range(rows):
        for j in range(i + 1, cols): 
            weight = sim_matrix[i][j]
            if weight > threshold:
                u, v = int(i), int(j)
                G.add_edge(u, v, value=float(weight), title=f"Similarity: {weight:.2f}", color=None)

    # Pass 2: Weak Bridges
    for i in range(rows):
        sorted_indices = np.argsort(sim_matrix[i])[::-1]
        connections_count = 0
        for j_numpy in sorted_indices:
            i_clean = int(i)
            j_clean = int(j_numpy)
            if i_clean == j_clean: continue 
            if G.has_edge(i_clean, j_clean):
                connections_count += 1
                continue
            if connections_count < 2: 
                weight = sim_matrix[i][j_numpy]
                if weight > 0.05: 
                    G.add_edge(i_clean, j_clean, value=0.1, title=f"Weak Link: {weight:.2f}", color='rgba(200, 200, 200, 0.1)', hidden=False)
                    connections_count += 1
            else:
                break

    # 3. Detect Communities
    if len(G.edges) > 0:
        partition = community_louvain.best_partition(G)
        unique_clusters = set(partition.values())

        # --- INSERT THEME LABELS HERE ---
        for cluster_id in unique_clusters:
            # Get members of this cluster 
            members = [node for node, grp in partition.items() if grp == cluster_id and isinstance(node, int)]
            if not members: continue

            # Calculate Theme
            cluster_articles = [articles[m] for m in members]
            theme_label = get_cluster_theme(cluster_articles)

            # Add Label Node 
            label_node_id = 2000 + cluster_id
            G.add_node(label_node_id, 
                       label=theme_label, 
                       shape='box',
                       # --- COLOR CHANGE HERE ---
                       color='#1e2a3a', # Solid dark blue background
                       font={'size': 40, 'face': 'arial', 'color': 'white'}, # White text
                       # -------------------------
                       size=20, 
                       mass=1) 

            # Connect Label to cluster members
            for member_id in members:
                G.add_edge(label_node_id, member_id, weight=0.01, color='rgba(0,0,0,0)', hidden=True)

        # Only assign groups if we are in 'Cluster' mode
        if color_mode == "Cluster":
            for node_id, cluster_id in partition.items():
                if isinstance(node_id, int): 
                    G.nodes[node_id]['group'] = cluster_id 
    
    return G

def save_graph_html(G, filename="galaxy.html"):
    # 1. Disable the native dropdown menu here
    net = Network(height="750px", width="100%", bgcolor="#0d1117", font_color="white", select_menu=False, cdn_resources='remote')
    net.from_nx(G)
    
    # Physics settings
    net.force_atlas_2based(
        gravity=-80, 
        central_gravity=0.01, 
        spring_length=150,      
        spring_strength=0.05, 
        damping=0.4, 
        overlap=0 
    )
    
    full_path = os.path.join(os.getcwd(), filename)
    
    try:
        # Write the initial HTML
        net.write_html(full_path)
        
        # 2. Open the file to inject custom JavaScript for the "Click Background to Deselect" logic
        with open(full_path, "r", encoding="utf-8") as f:
            html = f.read()
            
        # This script listens for a click. If no nodes/edges are under the mouse, it unselects everything.
        # It relies on the 'network' variable which Pyvis creates in the HTML.
        js_injection = """
        <script type="text/javascript">
            network.on("click", function (params) {
                if (params.nodes.length === 0 && params.edges.length === 0) {
                    network.unselectAll();
                }
            });
        </script>
        </body>
        """
        
        # Insert our script before the closing body tag
        html = html.replace("</body>", js_injection)
        
        # Save the modified file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(html)
            
        return full_path
        
    except Exception as e:
        print(f"❌ Error saving graph: {e}")
        return None