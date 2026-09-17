FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source and pre-indexed ChromaDB vector store
COPY src/ ./src/
COPY chroma_data/ ./chroma_data/
COPY tests/ ./tests/
COPY pyproject.toml pytest.ini ./

# Expose default port
EXPOSE 8000

# Start FastAPI application
CMD ["sh", "-c", "uvicorn daaruka.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
