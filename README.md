# internal-audit

This repository is a Django (6.0) application for internal auditing.

Quickstart (Docker):

1. Copy `.env.example` to `.env` and update values.
2. Build and start with Docker Compose:

```bash
docker-compose build
docker-compose up -d
```

3. Apply migrations and create a superuser (inside container):

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

Run tests locally:

```bash
pip install -r requirements.txt
python manage.py test
```

GitHub Actions:
- The workflow in `.github/workflows/ci.yml` runs tests on push/PR to main/master.

Notes:
- The repo already contains a `Dockerfile`, `entrypoint.sh`, and `docker-compose.yml`.
- Ensure you don't commit real secrets.

