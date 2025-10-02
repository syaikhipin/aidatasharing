# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/storage/uploads /app/storage/documents /app/storage/images /app/storage/datasets /app/storage/temp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV PORT=8000

# Required environment variables with defaults
ENV DATABASE_URL=${DATABASE_URL:-postgresql://user:pass@localhost/db}
ENV SECRET_KEY=${SECRET_KEY:-default-secret-key-change-in-production}
ENV JWT_SECRET_KEY=${JWT_SECRET_KEY:-default-jwt-secret-change-in-production}
ENV BACKEND_CORS_ORIGINS=${BACKEND_CORS_ORIGINS:-*}
ENV MINDSDB_URL=${MINDSDB_URL:-http://localhost:47334}

# Expose only the main API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# Run the application with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]