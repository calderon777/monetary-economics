FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app and the tutorials/ folder.
COPY . .

# Hugging Face Spaces serve on port 7860. Give Streamlit a writable home for
# its config/cache so it runs as the Space's non-root user.
ENV PORT=7860 \
    HOME=/app \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
EXPOSE 7860

CMD ["sh", "-c", "streamlit run app.py --server.address 0.0.0.0 --server.port $PORT"]
