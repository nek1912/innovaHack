#!/bin/sh

set -e

echo "Starting OPA..."

opa run \
    --server \
    --addr=127.0.0.1:8181 \
    /app/policy &

echo "Running migrations..."

cd /app/backend

alembic upgrade head

echo "Starting FastAPI..."

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000
