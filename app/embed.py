import time
from app.config import gemini, EMBED_MODEL

_MIN_INTERVAL = 0.7
_last_call = 0.0


def _rate_limit():
    global _last_call
    now = time.time()
    if now - _last_call < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - (now - _last_call))
    _last_call = time.time()


def embed(text):
    _rate_limit()
    result = gemini.models.embed_content(model=EMBED_MODEL, contents=text)
    return result.embeddings[0].values


def embed_query(text):
    _rate_limit()
    result = gemini.models.embed_content(model=EMBED_MODEL, contents=text)
    return result.embeddings[0].values
