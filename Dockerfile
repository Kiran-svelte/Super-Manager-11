FROM python:3.10-slim

WORKDIR /app

# Install minimal dependencies
RUN pip install --no-cache-dir fastapi uvicorn

# Create a minimal test app
RUN echo 'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/api/health")\ndef health(): return {"status": "healthy"}' > /app/test_app.py

# Set environment variables
ENV PORT=10000

# Expose port
EXPOSE 10000

# Start minimal test app
CMD ["sh", "-c", "uvicorn test_app:app --host 0.0.0.0 --port $PORT"]
