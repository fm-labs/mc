#!/bin/bash

echo "Starting API server on port 8080 ..."
exec uv run uvicorn --app-dir /app/src --host "0.0.0.0" --port 8080 server:app
