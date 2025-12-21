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

# Use PORT environment variable from Cloud Run
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}