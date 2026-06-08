FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY auto_capture.py .

VOLUME /app/data

EXPOSE 18732

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:18732/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "18732", "--log-level", "info"]
