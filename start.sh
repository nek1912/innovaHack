#!/bin/sh

set -e

PORT=${PORT:-8000}

echo "Starting OPA..."
opa run --server --addr=127.0.0.1:8181 /app/policy &
sleep 2

echo "Running migrations..."
cd /app/backend
alembic upgrade head

echo "Starting FastAPI on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
