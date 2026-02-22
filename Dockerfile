# 1. Builder Stage - MUST match Distroless (3.11)
FROM python:3.11-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 2. Runtime Stage
FROM gcr.io/distroless/python3-debian12

WORKDIR /app

COPY --from=builder /opt/venv/lib /opt/venv/lib
COPY . .

ENV PYTHONPATH="/opt/venv/lib/python3.11/site-packages"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]