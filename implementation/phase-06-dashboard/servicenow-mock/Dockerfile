# Dark NOC — ServiceNow Mock API Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi==0.115.0 uvicorn==0.32.0 pydantic==2.10.0

COPY main.py .

RUN useradd -u 1001 -r -g 0 -m noc && \
    chown -R 1001:0 /app && chmod -R g+rw /app
USER 1001

EXPOSE 8080
CMD ["python", "-u", "main.py"]
