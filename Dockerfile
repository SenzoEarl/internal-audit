# File: `Dockerfile`
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# run as non-root
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

ENV DJANGO_SETTINGS_MODULE=internal_audit.settings

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "internal_audit.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-level", "info"]
