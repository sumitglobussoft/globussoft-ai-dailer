# ─── Stage 1: Build frontend ────────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build


# ─── Stage 2: Python 3.10 backend ───────────────────────────────────────────
FROM python:3.10-slim AS backend

WORKDIR /app

# System deps required for:
#   chromadb / hnswlib  → build-essential, g++, python3-dev
#   pymupdf             → libmupdf-dev (bundled in pymupdf wheel, no extra dep)
#   faiss-cpu           → libgomp1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    python3-dev \
    libgomp1 \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence-transformers model at build time
# (avoids 15-20s cold-start download on each container restart)
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application source
COPY . .

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure directories exist for runtime data
RUN mkdir -p recordings faiss_indexes

EXPOSE 8001

# Use exec form so signals are forwarded correctly
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--loop", "uvloop", "--log-level", "info"]
