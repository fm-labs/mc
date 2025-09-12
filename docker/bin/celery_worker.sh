#!/bin/bash

exec uv run celery --workdir /app/src -A celery_worker.celery worker --loglevel=INFO
