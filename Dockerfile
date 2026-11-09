FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for audio handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

EXPOSE 7860

# Run FastAPI app on port 7860 (Hugging Face default) or PORT env var
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
