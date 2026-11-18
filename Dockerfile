# ==============================================================================
# Dockerfile: 3D Cricket Ball Trajectory Prediction Engine & Web Platform
# ==============================================================================

# Stage 1: Build React + Tailwind Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY cricket_trajectory_engine/frontend/package*.json ./
RUN npm install
COPY cricket_trajectory_engine/frontend ./
RUN npm run build

# Stage 2: Python Backend & Web Serving Platform
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging:
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    HOST=0.0.0.0 \
    PORT=8000

# Install required system libraries (ffmpeg for video generation, curl for healthchecks):
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies:
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application codebase and delivery tracking feeds:
COPY . .
COPY --from=frontend-builder /app/frontend/dist ./cricket_trajectory_engine/frontend/dist
COPY --from=frontend-builder /app/frontend/index.html ./cricket_trajectory_engine/frontend/index.html

# Ensure entrypoint script is executable:
RUN chmod +x /app/entrypoint.sh

# Expose web application port:
EXPOSE 8000

# Container Healthcheck:
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/experiments || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn"]
