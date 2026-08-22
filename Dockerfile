# ══════════════════════════════════════════════
# Stage 1 — Build Next.js static export
# ══════════════════════════════════════════════
FROM node:20-alpine AS frontend-builder

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --prefer-offline

COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ══════════════════════════════════════════════
# Stage 2 — Python backend + static files
# ══════════════════════════════════════════════
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install deps first (cache layer)
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

# Copy backend code
COPY backend/ ./
# Remove venv if accidentally copied
RUN rm -rf venv __pycache__

# Copy static frontend export
COPY --from=frontend-builder /build/out ./static

# Copy env example (user provides real .env via Liara panel env vars)
COPY backend/.env.example ./.env.example

# Non-root user
RUN adduser --disabled-password --gecos '' appuser \
    && mkdir -p /app/qdrant_data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/health')" || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-3000} --workers 1"]
