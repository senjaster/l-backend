#!/bin/sh
set -e

# Use PORT environment variable, default to 8000 if not set
PORT=${PORT:-8080}

echo "Starting uvicorn on port $PORT"

# Execute uvicorn with the port from environment variable
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
