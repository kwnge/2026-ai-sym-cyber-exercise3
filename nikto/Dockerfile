FROM python:3.13-bookworm


WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libnet-ssleay-perl \
    perl \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Nikto specific
RUN apt-get install -y \
        git \
        perl \
        libnet-ssleay-perl \
        ca-certificates && \
    git clone https://github.com/sullo/nikto.git /opt/nikto && \
    ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto && \
    chmod +x /usr/local/bin/nikto

ENV PYTHONUNBUFFERED=1

COPY main.py .
COPY pyproject.toml .
RUN pip install .

EXPOSE 8000

CMD ["gunicorn", "main:combined_app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "0"]
