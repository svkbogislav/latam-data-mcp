FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY latam_data/ ./latam_data/
COPY server.py .

# Hosting platforms inject $PORT; the entrypoint switches to Streamable HTTP.
ENV PORT=8000
EXPOSE 8000

CMD ["python", "server.py"]
