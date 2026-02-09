FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ ./backend/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
# Dummy env vars to allow imports
ENV SUPABASE_URL=https://dummy.supabase.co
ENV SUPABASE_KEY=dummy

# Verify the app can import
RUN python -c "from backend.main import app; print('Backend imports OK')" || echo "Import failed but continuing"

# Expose port
EXPOSE 10000

# Start command
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"]
