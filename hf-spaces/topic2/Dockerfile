FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .

# Hugging Face Spaces expects the app to listen on $PORT (defaults to 7860)
ENV PORT=7860
EXPOSE 7860

# Run the Shiny app on the expected port
CMD ["sh", "-c", "shiny run app.py --host 0.0.0.0 --port $PORT"]
