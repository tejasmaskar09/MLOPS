# ============================================================
# Experiment 5: Dockerfile for FastAPI ML Service
# ============================================================
# Multi-stage build for smaller final image

FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies in a virtual env for clean copy
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# -----------------------------------------------------------
FROM python:3.12-slim

LABEL maintainer="mlops-student"
LABEL description="FastAPI ML Service — Student Score Predictor"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app.py schemas.py logging_config.py auth.py ./
COPY model.pkl .
COPY student_data.csv .

# Environment defaults (override at runtime)
ENV API_KEY="mlops-demo-key-2024"
ENV JWT_SECRET_KEY="super-secret-key-change-in-production"

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
