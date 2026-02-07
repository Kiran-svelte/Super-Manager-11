# =============================================================================
# Super Manager - Production-Grade Multi-stage Dockerfile
# =============================================================================
# Features:
# - Multi-stage builds for minimal image size
# - Security hardening (non-root user, minimal packages)
# - Layer caching optimization
# - Health checks
# - Multi-platform support (amd64, arm64)
# =============================================================================

# Build arguments
ARG PYTHON_VERSION=3.11
ARG NODE_VERSION=20
ARG PORT=8000

# =============================================================================
# Stage 1: Frontend Builder
# =============================================================================
FROM node:${NODE_VERSION}-alpine AS frontend-builder

# Set working directory
WORKDIR /build

# Install dependencies first (better cache utilization)
COPY frontend/package*.json ./
RUN npm ci --prefer-offline --no-audit --legacy-peer-deps

# Copy source files
COPY frontend/ ./

# Build for production with optimizations
ENV NODE_ENV=production
RUN npm run build && \
    # Remove source maps in production
    find dist -name "*.map" -delete 2>/dev/null || true

# =============================================================================
# Stage 2: Python Dependencies Builder
# =============================================================================
FROM python:${PYTHON_VERSION}-slim AS python-builder

# Prevent Python from writing bytecode and buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# =============================================================================
# Stage 3: Production Runtime
# =============================================================================
FROM python:${PYTHON_VERSION}-slim AS production

# Labels for container metadata
LABEL org.opencontainers.image.title="Super Manager AI" \
      org.opencontainers.image.description="Intelligent AI assistant for task management" \
      org.opencontainers.image.vendor="Super Manager" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

# Build arguments
ARG PORT=8000

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PORT=${PORT} \
    # App configuration
    APP_ENV=production \
    LOG_LEVEL=INFO \
    WORKERS=4 \
    # Security
    SECURE_HEADERS=true

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Create non-root user with specific UID/GID for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy virtual environment from builder
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appgroup backend/ ./backend/

# Copy built frontend assets
COPY --from=frontend-builder --chown=appuser:appgroup /build/dist ./frontend/dist

# Copy configuration files
COPY --chown=appuser:appgroup requirements.txt .
COPY --chown=appuser:appgroup .env.example .env.example 2>/dev/null || true

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/tmp && \
    chown -R appuser:appgroup /app

# Security: Remove unnecessary files and restrict permissions
RUN chmod -R 550 /app/backend && \
    chmod -R 770 /app/logs /app/data /app/tmp

# Switch to non-root user
USER appuser

# Health check with proper timeout and intervals
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Expose the application port
EXPOSE ${PORT}

# Use tini as init system for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start the application with gunicorn for production
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS} --loop uvloop --http httptools --access-log --log-level ${LOG_LEVEL,,}"]

# =============================================================================
# Stage 4: Development (optional build target)
# =============================================================================
FROM production AS development

USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install dev Python packages
RUN pip install pytest pytest-asyncio pytest-cov black flake8 mypy

USER appuser

ENV APP_ENV=development \
    LOG_LEVEL=DEBUG \
    WORKERS=1

# Use auto-reload for development
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT} --reload --log-level debug"]
