# Dark NOC — MCP OpenShift Server Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl and provide `oc` shim used by server.py
RUN curl -LO "https://dl.k8s.io/release/v1.32.0/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && mv kubectl /usr/local/bin/ && \
    ln -sf /usr/local/bin/kubectl /usr/local/bin/oc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

RUN useradd -u 1001 -r -g 0 -m noc && \
    chown -R 1001:0 /app && chmod -R g+rw /app
USER 1001

EXPOSE 8001
CMD ["python", "-u", "server.py"]
