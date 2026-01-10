import os
import requests
import newspaper
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import dotenv

# Load environment variables
dotenv.load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def fetch_news_urls(topic="Technology", limit=10, mock=True):
    """
    Step 1: Get list of URLs from NewsAPI.
    If mock=True, returns fake data to save API credits.
    """
    if mock:
        print("⚠️ USING MOCK DATA (Saving API Credits)")
        return [
            "https://www.bbc.com/news/technology-67578765",  # Example real links
            "https://www.cnn.com/2023/11/29/tech/chatgpt-one-year-anniversary/index.html",
            "https://techcrunch.com/2023/11/29/pika-labs-raises-55m-for-its-ai-video-generation-platform/"
        ]

    url = "https://newsapi.org/v2/everything"
    
    # Calculate date for "Last 2 days only" (Free tier limits usually)
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')

    params = {
        "q": topic,
        "from": two_days_ago,
        "sortBy": "relevancy",
        "language": "en",
        "apiKey": NEWS_API_KEY,
        "pageSize": limit,  # Don't fetch too many
        # Restrict to scrape-friendly domains to avoid errors
        "domains": "bbc.com,cnn.com,techcrunch.com,npr.org,aljazeera.com" 
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") != "ok":
            print(f"❌ API Error: {data.get('message')}")
            return []

        urls = [article['url'] for article in data.get('articles', [])]
        print(f"✅ Found {len(urls)} articles for topic: {topic}")
        return urls
        
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return []

def scrape_single_article(url):
    """
    Step 2: Go to the URL and extract the body text.
    """
    try:
        article = newspaper.Article(url)
        article.download()
        article.parse()
        
        # Simple validation: If text is too short, it's likely a failed scrape
        if len(article.text) < 100:
            return None
            
        return {
            "title": article.title,
            "text": article.text,
            "url": url,
            "date": article.publish_date
        }
    except Exception as e:
        # Silently fail for bad links (common in scraping)
        return None

def get_full_articles(topic="Technology", limit=10, mock=False):
    """
    The Main Function: Combines Fetching + Scraping (Threaded)
    """
    # 1. Get URLs
    urls = fetch_news_urls(topic, limit, mock)
    if not urls:
        return []

    print(f"🚀 Scraping {len(urls)} articles in parallel...")
    
    # 2. Scrape in parallel (Speed boost!)
    valid_articles = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(scrape_single_article, urls))
    
    # 3. Clean up None values (failed scrapes)
    valid_articles = [r for r in results if r is not None]
    
    print(f"🎉 Successfully scraped {len(valid_articles)} full articles!")
    return valid_articles