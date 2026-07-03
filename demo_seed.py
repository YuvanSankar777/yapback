from app.ingest import ingest_video

DEMO_VIDEOS = [
    {"url": "https://www.youtube.com/watch?v=x7X9w_GIm1s", "title": "Python in 100 Seconds — Fireship"},
]

if __name__ == "__main__":
    for video in DEMO_VIDEOS:
        print(f"Ingesting: {video['title']}")
        result = ingest_video(video["url"], video["title"])
        print(f"  {result['chunk_count']} chunks stored.")
    print("\nDone. Run: streamlit run streamlit_app.py")
