import webbrowser
import os
from src.data_pipeline import get_full_articles
from src.math_engine import vectorize_articles, calculate_similarity
from src.graph_logic import build_network_graph, save_graph_html

def run_test():
    # 1. Scrape (Mock or Real)
    # Use mock=True first to test the visualization instantly
    print("--- STEP 1: FETCHING ---")
    articles = get_full_articles(topic="AI", limit=10, mock=True)
    
    # 2. Math
    print("\n--- STEP 2: MATH ---")
    articles, vectors = vectorize_articles(articles)
    sim_matrix = calculate_similarity(vectors)
    
    # 3. Graph
    print("\n--- STEP 3: VISUALIZATION ---")
    # Threshold 0.2 is low, good for small mock datasets so we see connections
    G = build_network_graph(articles, sim_matrix, threshold=0.2) 
    
    html_file = save_graph_html(G, "test_galaxy.html")
    
    # 4. Open it automatically
    if html_file:
        print(f"🚀 Opening {html_file} in your browser...")
        webbrowser.open('file://' + os.path.realpath(html_file))

if __name__ == "__main__":
    run_test()