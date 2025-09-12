#!/bin/bash

CMD=$1
PYTHON_PATH="/app/src:$PYTHON_PATH"
export PYTHONPATH

case $CMD in
  api)
    echo "Starting dev API server..."
    exec uv run uvicorn --app-dir /app/src --host "0.0.0.0" --port 8000 server:app
    #exec $PYTHON_BIN uvicorn --app-dir /app/src orchestra.server:app
    ;;

  celery-worker)
    echo "Starting celery worker..."
    sleep 3 # wait for other services to be ready
    exec uv run celery --workdir /app/src -A celery_worker.celery worker --loglevel=INFO
    ;;

  supervisor)
    echo "Starting supervisord..."
    exec /usr/bin/supervisord --nodaemon -c /etc/supervisord.conf
    ;;

  help)
    echo "Usage: $0 {api|celery-worker|supervisor|help}"
    exit 0
    ;;
esac

echo "Unknown command: $CMD"
exec "$@"
