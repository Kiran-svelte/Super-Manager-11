FROM python:3.10-slim

WORKDIR /app

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

# Start command - use uvicorn directly
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
