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
def classify_political_leaning(content, is_url=False):
    """
    Uses Gemini to classify political framing as Left, Right, or Neutral.
    Returns: (label, confidence, explanation)
    """

    # Reuse your scraping logic if it's a URL
    text_to_analyze = content
    if is_url:
        title, scraped_text = get_article_text(content)
        if not title:
            return "Error", "N/A", scraped_text
        text_to_analyze = scraped_text

    if not text_to_analyze or len(text_to_analyze) < 50:
        return "Error", "N/A", "Text too short to analyze."

    truncated_text = text_to_analyze[:6000]

    prompt = f"""
    You are a media analysis system.

    You will analyze the following news article and perform TWO tasks.

    OUTPUT FORMAT (ABSOLUTE – DO NOT DEVIATE):

    You MUST output EXACTLY the following 5 lines.
    Each item MUST be on its own line.
    DO NOT combine lines.
    DO NOT add extra text.
    DO NOT reorder fields.

    Political Framing: <Left-leaning | Right-leaning | Neutral>
    Confidence: <Low | Medium | High>
    Explanation: <1–3 sentences>

    Source Quality Grade: <F | D | C | B | A | A+>
    Source Quality Explanation: <1–3 sentences>

    ────────────────────────
    TASK 1: Political Framing Classification
    ────────────────────────

    Classify the political framing of the article as ONE of the following:
    - Left-leaning
    - Right-leaning
    - Neutral / Straight reporting

    Definitions:
    - Left-leaning: Emphasizes social justice, systemic inequality, regulation, climate issues, or critiques of corporations and power structures.
    - Right-leaning: Emphasizes tradition, nationalism, free markets, limited government, or cultural conservatism.
    - Neutral: Primarily factual reporting with minimal framing, emotional language, or opinion.

    For this task:
    1. Choose ONE category.
    2. Assign a confidence level: Low, Medium, or High.
    3. Explain the reasoning in 1–2 sentences.
    4. Do NOT mention political parties or specific political figures.

    ────────────────────────
    TASK 2: Source Quality & Citation Grade
    ────────────────────────

    Grade the article’s source quality on a scale from **F to A+** based ONLY on:
    - Use of legitimate, verifiable sources
    - Clear attribution of claims
    - Presence of primary sources (documents, data, direct quotes)
    - Transparency (who said what, and how it’s known)

    Grading guidance:
    - A+ : Multiple clearly cited primary sources, official data, documents, or direct expert quotes
    - A : Strong sourcing with reputable outlets, experts, or institutions
    - B  : Some credible sources, but limited depth or attribution
    - C  : Vague sourcing, anonymous claims, or weak attribution
    - D  : Minimal sourcing, heavy assertions without evidence
    - F  : No meaningful sources, speculative or unsupported claims
    For this task:
    1. Assign ONE letter grade (F to A+).
    2. Explain the grade in 1–2 sentences.
    3. Do NOT judge political ideology — only sourcing quality.



    Article Text:
    \"\"\"{truncated_text}\"\"\"
    """

    try:
        response = model.generate_content(prompt)

        if not response.text:
            return "Error", "N/A", "AI refused classification (safety block)."

        return response.text.strip()

    except Exception as e:
        return "Error", "N/A", str(e)
    
def format_analysis(text):
    fields = [
        "Political Framing:",
        "Confidence:",
        "Explanation:",
        "Source Quality Grade:",
        "Source Quality Explanation:"
    ]

    for field in fields:
        text = text.replace(field, f"\n{field}")

    return text.strip()