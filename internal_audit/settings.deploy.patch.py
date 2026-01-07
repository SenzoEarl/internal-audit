# - Use environment variables for secrets and DEBUG
# - Use dj-database-url for DATABASES
# - Add WhiteNoise and static storage

# Place this snippet near the top (imports)
import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()  # loads .env in project root for local development

# Replace SECRET_KEY / DEBUG / ALLOWED_HOSTS
SECRET_KEY = os.getenv("SECRET_KEY", "please-change-me")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Replace DATABASES with:
DATABASES = {
    "default": dj_database_url.parse(os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"))
}

# Insert WhiteNoise middleware just after SecurityMiddleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Static files storage for WhiteNoise
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
