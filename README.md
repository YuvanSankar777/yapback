---
title: YapBack
emoji: 🎙️
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: YouTube video Q&A with RAG + timestamp citations
---

<h1 align="center">🎙️ YapBack</h1>

<p align="center">
  <b>Ask any YouTube video a question — get answers grounded in the actual transcript, with clickable timestamps that jump to the exact moment.</b>
</p>

<p align="center">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" /></a>
  <a href="https://streamlit.io/"><img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" /></a>
  <a href="https://ai.google.dev/"><img alt="Gemini" src="https://img.shields.io/badge/Gemini_2.5_Flash-8E75B2?style=flat-square&logo=googlegemini&logoColor=white" /></a>
  <a href="https://pypi.org/project/endee/"><img alt="Endee" src="https://img.shields.io/badge/Endee-Vector_DB-4C1D95?style=flat-square" /></a>
  <a href="https://www.docker.com/"><img alt="Docker" src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" /></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-green?style=flat-square" /></a>
</p>

<p align="center">
  <a href="#-live-demo">Live Demo</a> ·
  <a href="#-how-it-works">How It Works</a> ·
  <a href="#-features">Features</a> ·
  <a href="#run-locally">Run Locally</a> ·
  <a href="#-usage">Usage</a> ·
  <a href="#-evaluation">Evaluation</a> ·
  <a href="#-tech-stack">Tech Stack</a>
</p>

---

## 🌐 Live Demo

**▶️ [Try it on Hugging Face Spaces](https://Yuvan777-yapback.hf.space)**

The hosted demo comes **pre-loaded with two videos** you can ask questions about right now:

| Video | Topic | Try asking |
|:------|:------|:-----------|
| 🎬 *Python in 100 Seconds* — Fireship | Tech | *"Who created Python and when?"* |
| 🎬 *Speak English in 30 Minutes: Advanced English Lesson* | Education | *"What speaking mistakes are covered?"* |

Every answer comes back with clickable **timestamp citations** that jump to the exact moment in the video.

> ⚠️ **Why can't I add my own video on the live demo?**
> YouTube blocks transcript requests coming from **cloud-server IPs** (Hugging Face, AWS, Google Cloud, etc.) as an anti-bot measure. Because the demo runs on Hugging Face's servers, it can't fetch new transcripts — so ingestion is **disabled on the hosted demo** and limited to the pre-loaded videos.
>
> ✅ **Ingesting *any* YouTube video works when you [run YapBack locally](#run-locally)** — requests then come from your own machine's residential IP, which YouTube allows. For an always-on public instance that ingests any video, see the residential-proxy setup in **[DEPLOY.md](./DEPLOY.md)**.

---

## 🧠 How It Works

YapBack is a **Retrieval-Augmented Generation (RAG)** app. Every answer is grounded in the
video's real transcript — never hallucinated — and cites the exact timestamp it came from.

```
                          INGESTION

  YouTube URL ──▶ Transcript API ──▶ Sentence Chunker ──▶ Gemini Embed ──▶ Endee DB
                                      (~150 words)         (3072-dim)      (cosine)


                          RETRIEVAL (RAG)

  Question ──▶ Gemini Embed ──▶ Endee Search ──▶ Top 3 Chunks ──▶ Gemini 2.5 Flash ──▶ Answer
                (3072-dim)       (cosine)         + timestamps                          + citations
```

1. **Ingest** — the transcript is split into sentence-aware chunks (~150 words, 5-entry overlap),
   embedded with Gemini (3072-dim), and stored in [**Endee**](https://pypi.org/project/endee/)
   alongside metadata (timestamp, deep-link, topic).
2. **Retrieve** — your question is embedded the same way; Endee finds the most similar chunks via
   cosine similarity over an HNSW index.
3. **Answer** — the top 3 chunks are handed to Gemini 2.5 Flash, which answers using *only* that
   context and cites the video title + timestamp for every claim.

---

## 🔥 Features

- **🎯 Timestamp deep-links** — every answer cites the exact moment; click to jump straight there.
- **🏷️ Local topic classification** — a TF-IDF + Naive Bayes model tags each chunk into one of
  6 topics (Tech, Science, Business, Education, Entertainment, General) with **zero API cost**.
- **🔍 Per-video or cross-video search** — ask about one video or your whole library.
- **💬 Conversational chat UI** — Streamlit chat with expandable source citations and quick-start prompts.
- **⚡ Sentence-aware chunking** — chunks split on entry boundaries with overlap, so no context is lost at the edges.
- **📊 Built-in evaluation** — a 10-query test suite reporting Hit@K, keyword recall, and similarity.

---

<a id="run-locally"></a>

## 🚀 Run Locally — Ingest Any Video

Running locally is the **full experience**: paste any YouTube URL and ingest it, because
transcript requests come from your own residential IP (which YouTube allows) rather than a
blocked cloud IP.

**Prerequisites:** Python 3.10+, Docker Desktop, and a free [Gemini API key](https://aistudio.google.com/apikey).

```bash
# 1. Clone the repo
git clone https://github.com/YuvanSankar777/yapback.git
cd yapback

# 2. Start the Endee vector database (Docker)
docker compose up -d

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
cp .env.example .env
#   → open .env and set GEMINI_API_KEY

# 5. (Optional) Seed the pre-built demo videos (no YouTube call)
python seed_demo.py

# 6. Launch the app
streamlit run streamlit_app.py
```

Then open **http://localhost:8501** and paste any YouTube URL to get started. 🎉

---

## 📖 Usage

| Command | What it does |
|:--------|:-------------|
| `streamlit run streamlit_app.py` | Launch the chat UI at `localhost:8501` |
| `python seed_demo.py` | Load the pre-built demo videos into Endee (no YouTube call) |
| `python evaluate.py` | Run the retrieval benchmark (10 queries, Hit@K + recall) |

**In the app:** paste a YouTube URL in the sidebar → **Ingest Video** → ask questions in the chat.
Use the **Search Within** dropdown to scope answers to a single video or search across all of them.

---

## ☁️ Deploy (free)

YapBack ships as a **single Docker image** that runs *both* the Endee vector DB and the
Streamlit UI (see [`Dockerfile`](./Dockerfile) + [`start.sh`](./start.sh)), so it deploys
anywhere Docker runs. The easiest free host is **Hugging Face Spaces**:

1. Create a free account at [huggingface.co](https://huggingface.co), then **New Space** →
   **SDK: Docker** → name it `yapback`.
2. In the Space, **Settings → Variables and secrets → New secret**:
   `GEMINI_API_KEY = <your key>`.
3. Push this repo to the Space's git remote:
   ```bash
   git remote add hf https://huggingface.co/spaces/<your-username>/yapback
   git push hf main
   ```
   The YAML header in this README (`sdk: docker`, `app_port: 7860`) tells the Space to build
   the `Dockerfile`. First build takes ~5 min; the app then goes live at
   `https://<your-username>-yapback.hf.space`.

On startup the container **auto-seeds the pre-built demo videos** (`demo_data/`) so the Space
has content immediately, and runs in **demo mode** (`YAPBACK_DEMO=1`) — ingestion is disabled
because YouTube blocks the cloud IP (see [Live Demo](#-live-demo)). Visitors can query the
pre-loaded videos; adding new videos is done by [running locally](#run-locally).

**Want the hosted instance to ingest *any* video?** Configure a **residential proxy** — full
instructions (Webshare / generic `PROXY_URL`) are in **[DEPLOY.md](./DEPLOY.md)**, along with
other hosts (Render, any VM).

> ℹ️ On free tiers the Endee data volume is **ephemeral** — the demo videos are re-seeded on
> every restart, so the demo always works.

---

## 🗄️ Endee — Vector Storage

YapBack uses [**Endee**](https://pypi.org/project/endee/) as its vector database, running locally via Docker.

**Collection:** `videomind` · cosine space · 3072 dimensions · int8 precision · HNSW (M=16, ef=128)

<details>
<summary>📦 <b>Record structure</b></summary>

```json
{
  "id": "x7X9w_GIm1s_0002",
  "vector": [3072 floats],
  "meta": {
    "text": "the actual transcript text...",
    "video_id": "x7X9w_GIm1s",
    "video_title": "Python in 100 Seconds",
    "timestamp_label": "1:17",
    "yt_url": "https://youtube.com/watch?v=x7X9w_GIm1s&t=77",
    "topic": "Tech",
    "topic_confidence": 0.95
  },
  "filter": { "video_id": "x7X9w_GIm1s" }
}
```

</details>

<details>
<summary>🔧 <b>Operations used</b></summary>

| Operation | Purpose |
|:----------|:--------|
| `create_index` | Collection setup — cosine space, 3072 dims |
| `upsert` | Store embedded chunks in batches of 100 |
| `query` | Retrieve the most similar chunks |
| `query(filter=...)` | Scope search to a single video |
| Health check | `GET /api/v1/health` before every operation |

</details>

---

## 📊 Evaluation

Run `python evaluate.py` to benchmark retrieval quality against a known video (10 queries).

<details open>
<summary><b>Results (K=3)</b></summary>

| Query | Hit | Recall | Score |
|:------|:---:|:------:|:-----:|
| What is Python used for? | ✅ | 100% | 0.703 |
| What makes Python popular? | ✅ | 100% | 0.736 |
| What is the Zen of Python? | ✅ | 100% | 0.715 |
| How do you declare a variable? | ✅ | 100% | 0.701 |
| Does Python support OOP? | ✅ | 100% | 0.714 |
| Python data structures? | ✅ | 50% | 0.643 |
| Who created Python? | ✅ | 100% | 0.703 |
| Python frameworks? | ✅ | 33% | 0.672 |
| Python for ML? | ✅ | 100% | 0.680 |
| How do functions work? | ✅ | 100% | 0.645 |
| **Overall** | **100%** | **88%** | **0.691** |

</details>

> **Why K=3?** It delivers the same keyword recall as higher `top_k` values while keeping the
> LLM context clean and focused — so YapBack retrieves the **top 3** chunks per query.

---

## 🛠️ Tech Stack

| Component | Choice | Why |
|:----------|:-------|:----|
| **Vector DB** | [Endee](https://pypi.org/project/endee/) (Docker) | Lightweight, cosine + HNSW, easy self-hosting |
| **Embeddings** | Gemini `embedding-001` | 3072-dim for high semantic fidelity |
| **LLM** | Gemini 2.5 Flash | Fast, accurate generation with citations |
| **Classification** | scikit-learn (TF-IDF + Naive Bayes) | Runs locally — zero API cost |
| **Transcripts** | `youtube-transcript-api` | No auth required |
| **UI** | Streamlit | Rapid prototyping, built-in chat |
| **Language** | Python 3.10+ | Rich ecosystem |

---

## 📁 Project Structure

```
yapback/
├── app/
│   ├── config.py          # Settings, API clients, constants
│   ├── embed.py           # Gemini embedding + rate limiter
│   ├── classifier.py      # TF-IDF + Naive Bayes (6 topics)
│   ├── ingest.py          # Transcript → chunks → embeddings → Endee
│   └── search.py          # Vector search + RAG answer generation
├── streamlit_app.py       # Chat UI
├── evaluate.py            # Retrieval accuracy benchmark
├── demo_seed.py           # Seed a demo video
├── docker-compose.yml     # Endee vector DB
├── requirements.txt       # Python dependencies
└── .env.example           # Environment template
```

---

## 👤 Author

**YuvanSankar** — [@YuvanSankar777](https://github.com/YuvanSankar777)

## 📝 License

Released under the [MIT License](./LICENSE).

<p align="center"><i>If YapBack helped you, consider giving it a ⭐️</i></p>
