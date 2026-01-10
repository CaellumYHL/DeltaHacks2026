from src.data_pipeline import get_full_articles


articles = get_full_articles(topic="Technology", limit=5, mock=True)

for i, art in enumerate(articles):
    print(f"\n--- Article {i+1} ---")
    print(f"TITLE: {art['title']}")
    print(f"TEXT START: {art['text'][:100]}...")