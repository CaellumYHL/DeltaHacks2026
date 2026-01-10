from src.math_engine import vectorize_articles, calculate_similarity

# 1. Create Fake Data (Two similar, one different)
fake_articles = [
    {"title": "Nvidia Stocks Rise", "text": "The GPU market is booming due to AI demand."},
    {"title": "AI Chips in Demand", "text": "Tech companies are buying more hardware for training models."},
    {"title": "Best Pizza Recipe", "text": "Use fresh mozzarella and tomato sauce for the best taste."}
]

# 2. Turn them into numbers
print("--- Phase 1: Vectorization ---")
processed_articles, vectors = vectorize_articles(fake_articles)
print(f"✅ Generated vectors of shape: {vectors.shape} (Rows x Dimensions)")

# 3. Calculate Similarity
print("\n--- Phase 2: Similarity Check ---")
matrix = calculate_similarity(vectors)

# 4. Print Results (Human Readable)
labels = ["Nvidia", "AI Chips", "Pizza"]

print(f"{'':<12} | {labels[0]:<10} | {labels[1]:<10} | {labels[2]:<10}")
print("-" * 50)

for i, row in enumerate(matrix):
    print(f"{labels[i]:<12} | {row[0]:.2f}       | {row[1]:.2f}       | {row[2]:.2f}")