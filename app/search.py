import requests
from endee import Endee

from app.config import gemini, COLLECTION, LLM_MODEL, ENDEE_API_URL, HEALTH_URL
from app.embed import embed_query


def _check_endee():
    try:
        resp = requests.get(HEALTH_URL, timeout=3)
        return resp.ok
    except Exception:
        return False


def _get_client():
    if not _check_endee():
        raise ConnectionError("Endee is not running. Run: docker compose up -d")
    client = Endee()
    client.set_base_url(ENDEE_API_URL)
    return client


def search(query, video_id=None, top_k=5):
    client = _get_client()
    index = client.get_index(name=COLLECTION)
    vec = embed_query(query)

    vid_filter = [{"video_id": {"$eq": video_id}}] if video_id else None
    results = index.query(vector=vec, top_k=top_k, ef=128, filter=vid_filter)

    hits = []
    for r in results:
        meta = r.get("meta") or r.get("metadata") or {}
        hits.append({
            "text":            meta.get("text", ""),
            "video_id":        meta.get("video_id", ""),
            "video_title":     meta.get("video_title", ""),
            "timestamp_label": meta.get("timestamp_label", "0:00"),
            "yt_url":          meta.get("yt_url", ""),
            "score":           r.get("similarity", r.get("score", 0)),
        })
    return hits


def answer(query, video_id=None):
    sources = search(query, video_id=video_id, top_k=3)

    if not sources:
        return {
            "answer_text": "No relevant transcript found. Try ingesting a video first.",
            "sources": [],
        }

    context_parts = []
    for s in sources:
        context_parts.append(f"[{s['video_title']} @ {s['timestamp_label']}]: {s['text']}")
    context = "\n\n".join(context_parts)

    prompt = f"""You are a helpful assistant that answers questions about YouTube videos \
using ONLY the transcript excerpts provided below.

Rules:
- Answer using ONLY the transcript text given — do not add outside knowledge.
- For every claim you make, cite the video title and timestamp like: (Video Title @ MM:SS)
- If the transcript does not contain enough information, say so clearly.

TRANSCRIPT EXCERPTS:
{context}

QUESTION: {query}

ANSWER:"""

    response = gemini.models.generate_content(model=LLM_MODEL, contents=prompt)

    return {
        "answer_text": response.text.strip(),
        "sources":     sources,
    }
