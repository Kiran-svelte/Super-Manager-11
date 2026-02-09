FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ ./backend/
COPY *.py ./

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 10000

# Start command
CMD ["gunicorn", "backend.main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:10000"]
