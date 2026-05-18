# Backend: Python 3.12 running the stdlib http server.
FROM python:3.12-slim

WORKDIR /app

# Copy the server code. (No pip install needed — pure stdlib.)
COPY server.py .

# Where the persistent quotes.json lives inside the container.
# In docker-compose we'll mount a volume at /app/data so additions survive restarts.
ENV QUOTES_FILE=/app/data/quotes.json
RUN mkdir -p /app/data

EXPOSE 8000

# -u = unbuffered stdout, so logs show up in `docker logs` immediately.
CMD ["python", "-u", "server.py"]
