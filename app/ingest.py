import re
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig
from endee import Endee

from app.config import (
    COLLECTION, EMBED_DIM, CHUNK_SIZE, OVERLAP, ENDEE_API_URL, HEALTH_URL,
    WEBSHARE_PROXY_USERNAME, WEBSHARE_PROXY_PASSWORD, PROXY_URL,
)
from app.embed import embed
from app.classifier import classify_video


def _proxy_config():
    """Return a youtube-transcript-api proxy config, or None if unconfigured.

    Cloud hosts (Hugging Face, most VMs) have their datacenter IP blocked by
    YouTube, so a residential proxy is required to fetch transcripts there.
    """
    if WEBSHARE_PROXY_USERNAME and WEBSHARE_PROXY_PASSWORD:
        return WebshareProxyConfig(
            proxy_username=WEBSHARE_PROXY_USERNAME,
            proxy_password=WEBSHARE_PROXY_PASSWORD,
        )
    if PROXY_URL:
        return GenericProxyConfig(http_url=PROXY_URL, https_url=PROXY_URL)
    return None


def extract_video_id(url_or_id):
    match = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", url_or_id)
    if match:
        return match.group(1)
    if len(url_or_id) == 11:
        return url_or_id
    raise ValueError(f"Invalid YouTube URL or ID: {url_or_id!r}")


def seconds_to_label(seconds):
    total = int(seconds)
    m, s = divmod(total, 60)
    return f"{m}:{s:02d}"


def fetch_title(video_id):
    cfg = _proxy_config()
    proxies = cfg.to_requests_dict() if cfg is not None else None
    try:
        resp = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://youtube.com/watch?v={video_id}", "format": "json"},
            timeout=8,
            proxies=proxies,
        )
        if resp.ok:
            return resp.json()["title"]
    except Exception:
        pass
    return f"Video {video_id}"


def _get_client():
    try:
        resp = requests.get(HEALTH_URL, timeout=3)
        if not resp.ok:
            raise ConnectionError()
    except Exception:
        raise ConnectionError("Endee is not running. Run: docker compose up -d")
    client = Endee()
    client.set_base_url(ENDEE_API_URL)
    return client


def _ensure_collection(client):
    try:
        client.get_index(name=COLLECTION)
    except Exception:
        client.create_index(name=COLLECTION, dimension=EMBED_DIM, space_type="cosine")


def fetch_transcript(video_id):
    api = YouTubeTranscriptApi(proxy_config=_proxy_config())
    try:
        transcript = api.fetch(video_id, languages=["en"])
    except Exception as e:
        if _proxy_config() is None:
            raise RuntimeError(
                "Couldn't reach YouTube. If YapBack is running on a cloud host "
                "(e.g. Hugging Face), YouTube blocks its server IP — configure a "
                "residential proxy via the WEBSHARE_PROXY_USERNAME/"
                "WEBSHARE_PROXY_PASSWORD or PROXY_URL secret. "
                f"(underlying error: {type(e).__name__}: {e})"
            ) from e
        raise
    return transcript.to_raw_data()


def chunk_transcript(raw, video_id, video_title):
    """Groups transcript entries into ~CHUNK_SIZE word segments, keeping
    each entry intact so we don't split mid-sentence."""
    chunks = []
    entry_buf = []
    word_count = 0

    for entry in raw:
        entry_words = len(entry["text"].split())
        entry_buf.append(entry)
        word_count += entry_words

        if word_count >= CHUNK_SIZE:
            text = " ".join(e["text"] for e in entry_buf)
            start_time = entry_buf[0]["start"]
            chunks.append({
                "text":            text,
                "video_id":        video_id,
                "video_title":     video_title,
                "timestamp_label": seconds_to_label(start_time),
                "yt_url":          f"https://youtube.com/watch?v={video_id}&t={int(start_time)}",
            })
            overlap_entries = entry_buf[-OVERLAP:] if OVERLAP < len(entry_buf) else entry_buf[:]
            entry_buf = list(overlap_entries)
            word_count = sum(len(e["text"].split()) for e in entry_buf)

    if entry_buf:
        text = " ".join(e["text"] for e in entry_buf)
        start_time = entry_buf[0]["start"]
        chunks.append({
            "text":            text,
            "video_id":        video_id,
            "video_title":     video_title,
            "timestamp_label": seconds_to_label(start_time),
            "yt_url":          f"https://youtube.com/watch?v={video_id}&t={int(start_time)}",
        })

    return chunks


def ingest_video(url_or_id, video_title=""):
    video_id = extract_video_id(url_or_id)

    if not video_title:
        video_title = fetch_title(video_id)

    client = _get_client()
    _ensure_collection(client)
    index = client.get_index(name=COLLECTION)

    raw = fetch_transcript(video_id)
    chunks = chunk_transcript(raw, video_id, video_title)

    classification = classify_video(chunks)

    records = []
    for i, chunk in enumerate(chunks):
        topic_info = classification["per_chunk"][i]
        records.append({
            "id":     f"{video_id}_{i:04d}",
            "vector": embed(chunk["text"]),
            "meta": {
                "text":            chunk["text"],
                "video_id":        chunk["video_id"],
                "video_title":     chunk["video_title"],
                "timestamp_label": chunk["timestamp_label"],
                "yt_url":          chunk["yt_url"],
                "topic":           topic_info["topic"],
                "topic_confidence": topic_info["confidence"],
            },
            "filter": {"video_id": video_id},
        })

    for i in range(0, len(records), 100):
        index.upsert(records[i : i + 100])

    return {
        "video_id": video_id,
        "video_title": video_title,
        "chunk_count": len(records),
        "dominant_topic": classification["dominant_topic"],
        "topic_distribution": classification["topic_distribution"],
    }
