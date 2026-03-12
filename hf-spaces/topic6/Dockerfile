FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full synced Space payload so the app can read topic question files.
COPY . .

ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "shiny run app.py --host 0.0.0.0 --port $PORT"]
