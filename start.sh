#!/usr/bin/env bash
# Boot the Endee vector DB in the background, wait for it, then run Streamlit.
set -euo pipefail

: "${NDD_DATA_DIR:=/data}"
: "${PORT:=7860}"
mkdir -p "$NDD_DATA_DIR"

echo "==> Starting Endee vector database..."
/usr/local/bin/entrypoint.sh &
ENDEE_PID=$!

echo "==> Waiting for Endee to become ready..."
for _ in $(seq 1 90); do
  if curl -sf http://localhost:8080/api/v1/health >/dev/null 2>&1; then
    echo "==> Endee is up."
    break
  fi
  if ! kill -0 "$ENDEE_PID" 2>/dev/null; then
    echo "!!! Endee server exited before becoming ready." >&2
    exit 1
  fi
  sleep 1
done

if [ "${YAPBACK_DEMO:-0}" = "1" ]; then
  echo "==> Seeding demo videos into Endee..."
  python3 seed_demo.py || echo "==> Demo seed skipped."
fi

echo "==> Starting Streamlit on port ${PORT}..."
exec streamlit run streamlit_app.py \
  --server.port="${PORT}" \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --browser.gatherUsageStats=false
