#!/bin/sh
set -e

# Wait for DB if using postgres (simple loop)
if [ -n "$DATABASE_URL" ]; then
  echo "Waiting for database..."
  # Try bounding with psycopg2-binary available in requirements
  until python - <<PY
import os, sys, time, urllib.parse as p, psycopg2
url = os.environ.get("DATABASE_URL")
if not url:
    sys.exit(0)
print("checking", url)
parsed = p.urlparse(url)
try:
    conn = psycopg2.connect(dbname=parsed.path[1:], user=parsed.username, password=parsed.password, host=parsed.hostname, port=parsed.port)
    conn.close()
    print("db ready")
except Exception:
    sys.exit(1)
PY
  do
    sleep 1
  done || true
fi