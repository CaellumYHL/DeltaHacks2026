import google.generativeai as genai
import os
import dotenv
import newspaper
from newspaper import Config

# Load environment variables
dotenv.load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- THE FIX IS HERE ---
# Changed 'gemini-pro' to 'gemini-1.5-flash'
model = genai.GenerativeModel('gemini-3-flash-preview')

def get_article_text(url):
    """
    Scrapes the text from a given URL using the same anti-blocking config
    as the main pipeline.
    """
    try:
        # User-Agent to prevent 403 Forbidden errors
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        config = Config()
        config.browser_user_agent = user_agent
        config.request_timeout = 10

        article = newspaper.Article(url, config=config)
        article.download()
        article.parse()
        
        return article.title, article.text
    except Exception as e:
        return None, f"Error scraping URL: {str(e)}"

def neutralize_content(content, is_url=False):
    """
    Rewrites text (or scraped URL content) to be purely factual.
    """
    
    # 1. If it's a URL, scrape it first
    original_title = "Provided Text"
    text_to_process = content

    if is_url:
        title, scraped_text = get_article_text(content)
        if not title: # Error happened
            return "Error", scraped_text # scraped_text contains error msg here
        original_title = title
        text_to_process = scraped_text

    if not text_to_process or len(text_to_process) < 50:
        return original_title, "Error: The text was too short to analyze."

    # 2. Send to Gemini
    # We limit to 6000 chars to prevent hitting token limits on the free tier
    truncated_text = text_to_process[:6000]
    
    prompt = f"""
    Act as an objective, robot journalist. 
    Rewrite the following article to be 100% neutral and factual.
    
    Input Text: "{truncated_text}"
    
    Instructions:
    1. Keep the same structure (paragraphs).
    2. Remove all emotional adjectives and "spin".
    3. Remove any opinions or editorializing.
    4. Keep ONLY the verified facts.
    5. Output the result as a clean news report.
    """
    
    try:
        response = model.generate_content(prompt)
        # Check if the response was blocked by safety filters
        if not response.text:
            return original_title, text_to_process, "Error: The AI refused to rewrite this text (Safety Block)."
            
        return original_title, text_to_process, response.text
    except Exception as e:
        return original_title, text_to_process, f"AI Error: {str(e)}"