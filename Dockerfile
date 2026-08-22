FROM python:3.11-slim

LABEL org.opencontainers.image.title="ShortsForge AI Worker"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.description="AI-powered YouTube Shorts generator"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p temp storage logs models

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WORKER_HOST=0.0.0.0 \
    WORKER_PORT=8000 \
    LOW_RESOURCE_MODE=true \
    DEV_MODE=false

EXPOSE 8000

CMD ["python", "-m", "worker.main"]
