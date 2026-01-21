FROM python:3.13-bookworm

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

COPY main.py .
COPY pyproject.toml .
RUN pip install .

EXPOSE 8000

CMD ["gunicorn", "main:combined_app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "0"]
