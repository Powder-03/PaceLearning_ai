# Stage 1: Frontend Builder
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Set the API URL for production build
ENV VITE_API_URL=""

# Build frontend
RUN npm run build

# Stage 2: Python Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --upgrade pip

# Copy and install requirements
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Stage 3: Final
FROM python:3.11-slim

WORKDIR /app

# Copy built wheels from builder stage
COPY --from=builder /app/wheels /app/wheels

# Install wheels
RUN pip install --no-index --find-links=/app/wheels /app/wheels/*

# Copy application code
COPY ./app /app/app

# Copy frontend build from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist /app/static

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Use PORT environment variable from Cloud Run
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}