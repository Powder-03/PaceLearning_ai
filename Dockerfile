# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --upgrade pip

# Copy and install requirements
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final
FROM python:3.11-slim

WORKDIR /app

# Copy built wheels from builder stage
COPY --from=builder /app/wheels /app/wheels

# Install wheels
RUN pip install --no-index --find-links=/app/wheels /app/wheels/*

# Copy application code
COPY ./app /app/app

# Copy Alembic for database migrations
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Health check for local testing
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health/live')"

# Use PORT environment variable from Cloud Run
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info