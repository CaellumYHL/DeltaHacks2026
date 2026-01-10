import networkx as nx
from pyvis.network import Network
import community.community_louvain as community_louvain
import os

def build_network_graph(articles, sim_matrix, threshold=0.4):
    """
    Input: List of articles, Similarity Matrix
    Output: A NetworkX Graph Object (G) with clusters assigned.
    """
    print(f"🕸️ Building Graph (Threshold: {threshold})...")
    G = nx.Graph()

    # 1. Add Nodes
    for i, art in enumerate(articles):
        # We add 'title' as the label and 'text' as the hover info
        G.add_node(i, label=art['title'], title=art['text'][:200] + "...", url=art['url'])

    # 2. Add Edges (Connect the dots)
    rows, cols = sim_matrix.shape
    for i in range(rows):
        for j in range(i + 1, cols): # Loop through upper triangle only
            weight = sim_matrix[i][j]
            if weight > threshold:
                # The thicker the line, the stronger the connection
                G.add_edge(i, j, value=float(weight), title=f"Similarity: {weight:.2f}")

    # 3. Detect Communities (The "Coloring" Step)
    if len(G.edges) > 0:
        partition = community_louvain.best_partition(G)
        
        for node_id, cluster_id in partition.items():
            G.nodes[node_id]['group'] = cluster_id
            
        print(f"🎨 Detected {max(partition.values()) + 1} distinct communities.")
    else:
        print("⚠️ No connections found! Try lowering the threshold.")

    return G

def save_graph_html(G, filename="galaxy.html"):
    """
    Visualizes the NetworkX graph using PyVis and saves to HTML.
    """
    # 1. Setup the Physics Engine
    # cdn_resources='remote' ensures it doesn't try to download files to your computer
    net = Network(height="750px", width="100%", bgcolor="#0d1117", font_color="white", select_menu=True, cdn_resources='remote')
    
    # 2. Convert from NetworkX
    net.from_nx(G)
    
    # 3. Tweak Physics
    net.force_atlas_2based(
        gravity=-50,
        central_gravity=0.01,
        spring_length=100,
        spring_strength=0.08,
        damping=0.4,
        overlap=0
    )
    
    # 4. Save (THE FIX IS HERE)
    # We use an absolute path to prevent confusion
    full_path = os.path.join(os.getcwd(), filename)
    print(f"💾 Saving 3D Galaxy to {full_path}...")
    
    try:
        # write_html is safer than save_graph for scripts
        net.write_html(full_path)
        return full_path
    except Exception as e:
        print(f"❌ Error saving graph: {e}")
        return None