#!/bin/bash
set -e

# Start OPA in background
opa run --server --addr :8181 /app/policy &
OPA_PID=$!

# Wait for OPA to be ready
sleep 2

# Run migrations
cd /app/backend
alembic upgrade head

# Start FastAPI
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
