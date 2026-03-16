FROM python:3.11-slim

WORKDIR /app

COPY checkbot.py .
COPY .env .

RUN pip install --no-cache-dir \
    zulip \
    python-dotenv \
    paramiko

CMD ["python", "checkbot.py"]