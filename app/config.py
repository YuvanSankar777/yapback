import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
ENDEE_URL      = os.getenv("ENDEE_URL", "http://localhost:8080").rstrip("/")
COLLECTION     = os.getenv("COLLECTION", "videomind")

# The Endee client and health probe both live under the /api/v1 prefix.
ENDEE_API_URL  = f"{ENDEE_URL}/api/v1"
HEALTH_URL     = f"{ENDEE_API_URL}/health"
EMBED_MODEL    = "gemini-embedding-001"
LLM_MODEL      = "gemini-2.5-flash"
EMBED_DIM      = 3072
CHUNK_SIZE     = 150
OVERLAP        = 5

gemini = genai.Client(api_key=GEMINI_API_KEY)
