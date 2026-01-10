from dotenv import load_dotenv
load_dotenv()

from google import genai

# Client automatically reads GEMINI_API_KEY from env
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in one sentence."
)

print(response.text)
