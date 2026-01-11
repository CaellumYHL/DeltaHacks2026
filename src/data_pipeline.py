import os
import requests
import newspaper
from newspaper import Config
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import dotenv

# Load environment variables
dotenv.load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_month_range(months_back: int):
    """
    months_back=0 -> current month
    months_back=1 -> last month
    returns (start_date_str, end_date_str) in YYYY-MM-DD
    """
    now = datetime.now()
    target = now - relativedelta(months=months_back)
    start = target.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = (start + relativedelta(months=1))
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def fetch_news_urls(topic="Technology", limit=10, mock=True, lang="en", months_back=0):
    """
    Step 1: Get list of URLs from NewsAPI.
    If mock=True, returns fake data to save API credits.
    """
    if mock:
        print("⚠️ USING MOCK DATA (Saving API Credits)")
        # These are stable links that definitely work for testing
        return [
            # --- CLUSTER 1: Artificial Intelligence (Vocab: algorithm, computing, logic) ---
            "https://www.britannica.com/technology/artificial-intelligence",
            "https://www.britannica.com/science/machine-learning",
            "https://www.britannica.com/technology/computational-linguistics", # NLP
            "https://www.britannica.com/technology/expert-system",
            "https://www.britannica.com/technology/neural-network",
            "https://www.britannica.com/technology/robotics",
            "https://www.britannica.com/technology/automation",
            "https://www.britannica.com/science/cybernetics",

            # --- CLUSTER 2: Baking & Culinary (Vocab: dough, fermentation, oven) ---
            "https://www.britannica.com/topic/sourdough",
            "https://www.britannica.com/topic/bread",
            "https://www.britannica.com/topic/baking",
            "https://www.britannica.com/science/fermentation",
            "https://www.britannica.com/science/yeast-fungus",
            "https://www.britannica.com/topic/pastry",

            # --- CLUSTER 3: Team Sports (Vocab: tournament, ball, athlete) ---
            "https://www.britannica.com/sports/football-soccer",
            "https://www.britannica.com/sports/basketball",
            "https://www.britannica.com/sports/rugby",
            "https://www.britannica.com/sports/cricket-sport",
            "https://www.britannica.com/sports/Super-Bowl",
            "https://www.britannica.com/sports/World-Cup-football",

            # --- CLUSTER 4: Global History (Vocab: empire, conflict, revolution) ---
            "https://www.britannica.com/event/World-War-II",
            "https://www.britannica.com/event/Industrial-Revolution",
            "https://www.britannica.com/place/Roman-Empire",
            "https://www.britannica.com/event/French-Revolution",
            "https://www.britannica.com/event/Cold-War",

            # --- CLUSTER 5: Space & Astronomy (Vocab: star, orbit, physics) ---
            "https://www.britannica.com/science/solar-system",
            "https://www.britannica.com/science/black-hole",
            "https://www.britannica.com/science/galaxy",
            "https://www.britannica.com/science/extrasolar-planet", # Britannica calls Exoplanets this
            "https://www.britannica.com/topic/NASA"
        ]

    url = "https://newsapi.org/v2/everything"
    
    # Calculate date for "Last 2 days only" (Free tier limits usually)
        
    from_date, to_date = get_month_range(months_back)

    params = {
        "q": topic,
        "from": from_date,
        "to": to_date,            
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
            "image": article.top_image,  # <--- NEW LINE
            "date": article.publish_date
        }
    except Exception as e:
        # NOW WE PRINT THE ERROR so you know why it failed
        print(f"❌ Failed to scrape {url}: {e}")
        return None

def get_full_articles(topic="Technology", limit=10, mock=False, lang="en",months_back=0):
    """
    The Main Function: Combines Fetching + Scraping (Threaded)
    """
    
    # 1. Get URLs
    urls = fetch_news_urls(topic, limit, mock, lang, months_back=months_back)
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