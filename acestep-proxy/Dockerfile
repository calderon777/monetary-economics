FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV HOST=0.0.0.0
ENV PORT=8080

CMD ["sh", "-c", "uvicorn app:app --host ${HOST} --port ${PORT}"]
