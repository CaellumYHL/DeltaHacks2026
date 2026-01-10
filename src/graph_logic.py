import networkx as nx
from pyvis.network import Network

def build_graph(articles, vectors):
    """
    TODO: Need to connect this graph to the vector data and use cosine similarity to calculate nodes. 
    """
    G = nx.Graph()
    # Dummy node creation
    for i, art in enumerate(articles):
        G.add_node(i, label=art['title'], title=art['text'][:100])
    
    G.add_edge(0, 1) 
    return G

def save_pyvis_html(G, filename="graph.html"):
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
    net.from_nx(G)
    net.save_graph(filename)
    return filename
