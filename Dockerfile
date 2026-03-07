# Stage 1: Python builder
FROM python:3.11-slim AS builder

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY foundrai/ foundrai/
RUN uv pip install --system --no-cache -e .

# Stage 2: Frontend builder
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 3: Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app
COPY --from=frontend-builder /app/foundrai/frontend/dist /app/foundrai/frontend/dist

EXPOSE 8420

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8420/api/docs')" || exit 1

CMD ["uvicorn", "foundrai.api.app:app", "--host", "0.0.0.0", "--port", "8420"]
