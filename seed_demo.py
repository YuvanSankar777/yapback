"""Seed the pre-computed demo videos into Endee so the hosted showcase has
content to answer questions about — no YouTube call, no embedding cost at boot.

Run automatically on container start (see start.sh) when YAPBACK_DEMO=1, or
manually:  python seed_demo.py
"""
import json
import os

from app.config import COLLECTION
from app.ingest import _get_client, _ensure_collection

DEMO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_data")


def seed():
    manifest_path = os.path.join(DEMO_DIR, "manifest.json")
    if not os.path.exists(manifest_path):
        print("No demo_data/manifest.json found — nothing to seed.")
        return

    with open(manifest_path) as f:
        manifest = json.load(f)

    client = _get_client()
    _ensure_collection(client)
    index = client.get_index(name=COLLECTION)

    for v in manifest:
        vid = v["video_id"]
        records_path = os.path.join(DEMO_DIR, f"{vid}.records.json")
        with open(records_path) as f:
            records = json.load(f)
        for i in range(0, len(records), 100):
            index.upsert(records[i : i + 100])
        print(f"Seeded {vid}: {len(records)} chunks ({v['title']})")


if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        # Never block app startup on a seed failure.
        print(f"Demo seed skipped: {type(e).__name__}: {e}")
