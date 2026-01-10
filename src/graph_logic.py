import networkx as nx
from pyvis.network import Network
import community.community_louvain as community_louvain
import os
import numpy as np

def build_network_graph(articles, sim_matrix, threshold=0.4):
    """
    Input: List of articles, Similarity Matrix
    Output: A NetworkX Graph Object (G) with clusters assigned.
    """
    print(f"🕸️ Building Graph (Threshold: {threshold})...")
    G = nx.Graph()

    # 1. Add Nodes
    for i, art in enumerate(articles):
        tooltip_html = (
            f"<b>{art['title']}</b><br><br>"
            f"🔗 <a href='{art['url']}' target='_blank' style='color: #4da6ff;'>Open Article</a><br>"
            f"<span style='font-size: 10px; color: gray;'>{art['url']}</span>"
        )
        # Ensure ID is a standard int
        G.add_node(int(i), label=art['title'], title=tooltip_html, url=art['url'])

    rows, cols = sim_matrix.shape

    # --- HYBRID CONNECTION STRATEGY ---
    
    # Pass 1: Add "Strong" Edges (The Cluster Core)
    for i in range(rows):
        for j in range(i + 1, cols): 
            weight = sim_matrix[i][j]
            if weight > threshold:
                # FIX: Explicitly cast to int()
                u, v = int(i), int(j)
                G.add_edge(u, v, value=float(weight), title=f"Similarity: {weight:.2f}", color=None)

    # Pass 2: Add "Weak Bridges" (The Web Background)
    for i in range(rows):
        # argsort returns numpy integers, which crash PyVis
        sorted_indices = np.argsort(sim_matrix[i])[::-1]
        
        connections_count = 0
        for j_numpy in sorted_indices:
            # FIX: Convert numpy int64 to python int
            i_clean = int(i)
            j_clean = int(j_numpy)
            
            if i_clean == j_clean: continue 
            
            # Check existing edges using clean integers
            if G.has_edge(i_clean, j_clean):
                connections_count += 1
                continue
            
            if connections_count < 2: 
                weight = sim_matrix[i][j_numpy]
                
                if weight > 0.05: 
                    # Add Ghost Edge with clean integers
                    G.add_edge(i_clean, j_clean, value=0.1, title=f"Weak Link: {weight:.2f}", color='rgba(200, 200, 200, 0.1)', hidden=False)
                    connections_count += 1
            else:
                break

    # 3. Detect Communities
    if len(G.edges) > 0:
        partition = community_louvain.best_partition(G)
        for node_id, cluster_id in partition.items():
            G.nodes[node_id]['group'] = cluster_id
        print(f"🎨 Detected {max(partition.values()) + 1} distinct communities.")
    else:
        print("⚠️ No connections found! Try lowering the threshold.")

    return G

def save_graph_html(G, filename="galaxy.html"):
    net = Network(height="750px", width="100%", bgcolor="#0d1117", font_color="white", select_menu=True, cdn_resources='remote')
    net.from_nx(G)
    
    # Physics Tuning for "Web" Look
    net.force_atlas_2based(
        gravity=-80,            
        central_gravity=0.01,   
        spring_length=150,      
        spring_strength=0.05,   
        damping=0.4,
        overlap=1
    )
    
    full_path = os.path.join(os.getcwd(), filename)
    print(f"💾 Saving 3D Galaxy to {full_path}...")
    
    try:
        net.write_html(full_path)
        return full_path
    except Exception as e:
        print(f"❌ Error saving graph: {e}")
        return None