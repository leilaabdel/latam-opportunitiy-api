# 1. Builder Stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Create the virtual environment
RUN python -m venv /opt/venv

# Ensure pip uses the venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 2. Runtime Stage
FROM gcr.io/distroless/python3-debian12

WORKDIR /app

# Copy the venv libraries from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy your application code
COPY . .

# Link the venv site-packages so the Distroless system python can see them
ENV PYTHONPATH="/opt/venv/lib/python3.11/site-packages"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Rely on the Distroless default entrypoint (/usr/bin/python3) 
# and pass the uvicorn startup command directly to it
CMD ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]