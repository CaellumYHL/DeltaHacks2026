import os
import requests
import newspaper
from newspaper import Config
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
        # These are stable links that definitely work for testing
        return [
            "https://en.wikipedia.org/wiki/Artificial_intelligence",
            "https://en.wikipedia.org/wiki/Machine_learning",
            "https://en.wikipedia.org/wiki/Natural_language_processing",
            "https://en.wikipedia.org/wiki/Large_language_model",
            "https://en.wikipedia.org/wiki/Neural_network"
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
        "pageSize": limit,
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") != "ok":
            print(f"❌ API Error: {data.get('message')}")
            return []
        
        if data.get("totalResults", 0) == 0:
            print("❌ No articles found. Try a broader topic like 'Apple' or 'Tech'.")
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
    Uses custom User-Agent to avoid 403 blocks.
    """
    try:
        # 1. Config: Pretend to be a browser (Chrome)
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        config = Config()
        config.browser_user_agent = user_agent
        config.request_timeout = 10

        # 2. Download
        article = newspaper.Article(url, config=config)
        article.download()
        article.parse()
        
        # 3. Validation
        if len(article.text) < 100:
            print(f"⚠️ Skipped (Too short): {url}")
            return None
            
        return {
            "title": article.title,
            "text": article.text,
            "url": url,
            "date": article.publish_date
        }
    except Exception as e:
        # NOW WE PRINT THE ERROR so you know why it failed
        print(f"❌ Failed to scrape {url}: {e}")
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