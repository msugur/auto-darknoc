FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

RUN useradd -u 1001 -r -g 0 -m noc && \
    chown -R 1001:0 /app && chmod -R g+rw /app
USER 1001

EXPOSE 8003
CMD ["python", "-u", "server.py"]
