# Dark NOC Agent — Dockerfile
# Multi-stage build for minimal production image

FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --target /opt/python \
    -r requirements.txt

# ─────────────────────────────
FROM python:3.12-slim
# ─────────────────────────────

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /opt/python /opt/python
ENV PYTHONPATH=/opt/python

# Copy agent source
COPY agent.py .
COPY state.py .

# Non-root user for OpenShift compatibility
RUN useradd -u 1001 -r -g 0 -m -d /app -s /sbin/nologin noc-agent && \
    chown -R 1001:0 /app && \
    chmod -R g+rw /app

USER 1001

EXPOSE 8080

CMD ["python", "-u", "agent.py"]
