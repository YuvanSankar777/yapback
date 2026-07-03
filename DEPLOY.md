# Deploying YapBack

YapBack needs **two things running**: the Streamlit UI *and* the Endee vector database.
To make that trivial, the repo ships a **single Docker image** that runs both in one
container:

- [`Dockerfile`](./Dockerfile) — layers Python + the app on top of the official
  `endeeio/endee-server` image.
- [`start.sh`](./start.sh) — boots Endee in the background, waits for its health check, then
  launches Streamlit on `$PORT` (default `7860`).

The only runtime requirement is a **`GEMINI_API_KEY`** environment variable
([get one free](https://aistudio.google.com/apikey)).

---

## Option 1 — Hugging Face Spaces (recommended, free)

Free tier: 2 vCPU / 16 GB RAM, Docker support, secrets. Best free option for this app.

1. Create a free account at [huggingface.co](https://huggingface.co).
2. **New Space** → **Docker** SDK (blank template) → name `yapback` → **Create Space**.
3. **Settings → Variables and secrets → New secret** →
   `GEMINI_API_KEY = <your key>`.
4. Push this repo to the Space:
   ```bash
   git remote add hf https://huggingface.co/spaces/<your-username>/yapback
   git push hf main
   ```
   When prompted for a password, use a **Hugging Face access token**
   (Settings → Access Tokens, `write` scope), or run `huggingface-cli login` first.
5. The Space reads the YAML header in `README.md` (`sdk: docker`, `app_port: 7860`) and
   builds the `Dockerfile`. First build ≈ 5 min. Live at
   `https://<your-username>-yapback.hf.space`.

**Notes**
- Storage is **ephemeral** on the free tier — ingested videos are cleared when the Space
  sleeps (after 48 h idle) or rebuilds. Re-ingest in a few seconds.
- The Space cold-starts (~30–60 s) after sleeping while Endee boots.

---

## Option 2 — Any cloud VM (full control, persistent data)

On any VM with Docker (DigitalOcean, Hetzner, EC2/Lightsail — ~$5–12/mo):

```bash
git clone https://github.com/YuvanSankar777/yapback.git && cd yapback
docker build -t yapback .
docker run -d --name yapback -p 80:7860 \
  -e GEMINI_API_KEY=<your key> \
  -v yapback_data:/data \
  --restart unless-stopped \
  yapback
```

The `-v yapback_data:/data` volume makes ingested videos **persist** across restarts.
Point your domain at the VM (optionally add Caddy/Nginx for HTTPS).

---

## Option 3 — Render (Docker web service)

1. Push this repo to GitHub (already done).
2. On [render.com](https://render.com): **New → Web Service** → connect the repo →
   **Runtime: Docker**.
3. Add environment variable `GEMINI_API_KEY`.
4. Set the instance port to `7860` (Render also injects `$PORT`, which `start.sh` honors).

> The Render free tier has 512 MB RAM (tight for Endee + Streamlit) and no persistent disk,
> so it's fine for a quick demo but a paid instance or a VM is steadier.

---

## Requirements & gotchas

- **CPU:** the Endee server needs **AVX2** (x86_64) or **NEON/SVE2** (ARM). All mainstream
  cloud CPUs qualify; very old or heavily-emulated CPUs may not.
- **Secret required:** without `GEMINI_API_KEY` the app fails on startup (embeddings + LLM
  both need it).
- **Port:** the container serves on `$PORT` (default `7860`). Map it to whatever your host
  expects (`80`/`443` behind a proxy, `7860` on Spaces).
- **Local smoke test:**
  ```bash
  docker build -t yapback .
  docker run --rm -p 7860:7860 -e GEMINI_API_KEY=<key> yapback
  # open http://localhost:7860
  ```
