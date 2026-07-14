# YapBack — single-container image bundling the Endee vector DB + the Streamlit UI.
# Base image already contains the Endee server binaries and its entrypoint.
FROM endeeio/endee-server:latest

USER root

# Python runtime (+ curl for the readiness probe in start.sh)
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .
RUN chmod +x start.sh

# Endee server config (mirrors the base image defaults) + app wiring.
# PORT defaults to 7860 for Hugging Face Spaces; hosts like Render override it.
ENV NDD_DATA_DIR=/data \
    NDD_SERVER_PORT=8080 \
    NDD_NUM_THREADS=0 \
    ENDEE_URL=http://localhost:8080 \
    PORT=7860 \
    YAPBACK_DEMO=1

EXPOSE 7860

# Reset the base image's ENTRYPOINT (Endee's entrypoint.sh) so our start.sh runs.
# start.sh launches Endee's entrypoint itself, then Streamlit.
ENTRYPOINT []
CMD ["./start.sh"]
