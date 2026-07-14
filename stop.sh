#!/usr/bin/env bash
# Stop everything YapBack started by serve.sh.
cd "$(dirname "$0")"
pkill -f "cloudflared tunnel --url http://localhost:8501" 2>/dev/null && echo "tunnel stopped"
pkill -f "streamlit run streamlit_app.py" 2>/dev/null && echo "streamlit stopped"
docker compose stop 2>/dev/null && echo "endee stopped"
echo "YapBack is down."
