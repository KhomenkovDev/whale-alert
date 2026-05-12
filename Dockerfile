FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --no-cache-dir build setuptools && pip install --no-cache-dir .

RUN python manage.py collectstatic --noinput
RUN python manage.py migrate --noinput

EXPOSE 8080

CMD daphne -b 0.0.0.0 -p $PORT whale_alert.asgi:application
