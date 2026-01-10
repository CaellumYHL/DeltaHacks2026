from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 1. Load the Model (Global Variable)
# We do this outside the function so we don't reload it every time (Speed Boost)
print("🧠 Loading AI Model... (This happens once)")
model = SentenceTransformer('all-MiniLM-L6-v2')

def vectorize_articles(articles):
    """
    Input: List of dictionaries (from your scraper)
    Output: The same list, but now with a 'vector' key added to each article.
    """
    if not articles:
        return []

    print(f"🧮 Vectorizing {len(articles)} articles...")
    
    # Extract just the text for the AI to read
    # We combine Title + Text for better context
    texts = [f"{art['title']}: {art['text'][:500]}" for art in articles]
    
    # THE MAGIC LINE: Turns text into numbers
    vectors = model.encode(texts)
    
    # Store the vector back into the article dictionary
    for i, article in enumerate(articles):
        article['vector'] = vectors[i]
        
    return articles, vectors

def calculate_similarity(vectors):
    """
    Input: A Matrix of vectors (e.g., 50 rows x 384 columns)
    Output: A Similarity Matrix (50 x 50) where value [A][B] is how similar they are.
    """
    # Cosine Similarity is the standard for text comparison
    # Result is a number between 0 (Opposite) and 1 (Identical)
    sim_matrix = cosine_similarity(vectors)
    
    # Zero out the diagonal (An article is always 100% similar to itself, which is boring)
    np.fill_diagonal(sim_matrix, 0)
    
    return sim_matrix