#!/usr/bin/env bash
# Launch YapBack publicly from your Mac:
#   Endee (Docker DB)  +  Streamlit (native — so YouTube ingestion works)  +  Cloudflare tunnel
# One command. Press Ctrl+C to stop the app + tunnel.
set -e
cd "$(dirname "$0")"

echo "==> Starting Endee (Docker)..."
docker compose up -d

echo "==> Waiting for Endee on :8080..."
until curl -sf http://localhost:8080/api/v1/health >/dev/null 2>&1; do sleep 1; done
echo "    Endee ready."

echo "==> Starting Streamlit (native) on :8501..."
source .venv/bin/activate
streamlit run streamlit_app.py \
  --server.port 8501 --server.address 127.0.0.1 \
  --server.headless true --browser.gatherUsageStats false \
  >/tmp/yapback-streamlit.log 2>&1 &
ST_PID=$!

cleanup() { echo; echo "==> Stopping app + tunnel..."; kill "$ST_PID" 2>/dev/null; exit 0; }
trap cleanup INT TERM

echo "==> Waiting for Streamlit..."
until curl -sf http://localhost:8501/_stcore/health >/dev/null 2>&1; do
  kill -0 "$ST_PID" 2>/dev/null || { echo "Streamlit failed — see /tmp/yapback-streamlit.log"; exit 1; }
  sleep 1
done
echo "    Streamlit ready."

echo "==> Opening public link (Ctrl+C to stop)..."
echo "    Look for the https://<...>.trycloudflare.com URL below:"
echo
cloudflared tunnel --url http://localhost:8501 --protocol http2
cleanup
