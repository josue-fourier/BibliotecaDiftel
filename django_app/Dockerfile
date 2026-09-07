FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE = 1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r  requirements.txt

COPY dashboard-interna/ /app/

RUN SECRET_KEY="dummy_for_build" POSTGRES_USER="username" POSTGRES_PASSWORD="password" POSTGRES_DB="default_database" POSTGRES_HOST="127.0.0.1" POSTGRES_PORT=5432 python manage.py collectstatic --noinput
