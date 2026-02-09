FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ ./backend/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Expose port
EXPOSE 10000

# Start command - use python -m to ensure module path is correct
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"]
