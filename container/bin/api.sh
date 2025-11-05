#!/bin/bash
# unused for now
echo "Starting API server on port 5000 ..."
exec uv run uvicorn --app-dir /app/src --host "0.0.0.0" --port 5000 server:app
