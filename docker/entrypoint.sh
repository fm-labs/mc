#!/bin/bash


PYTHON_PATH="/app/src:$PYTHON_PATH"
export PYTHONPATH

FLOWER_USER_NAME=${FLOWER_USER_NAME:-admin}
FLOWER_USER_PASSWORD=${FLOWER_USER_PASSWORD:-admin}

# Not recommended to change the socket path, but provided for flexibility.
# The pre-defined path is used in the Dockerfile to create socket and set permissions.
SSH_AUTH_SOCK=${SSH_AUTH_SOCK:-/ssh-agent/agent.sock}
export SSH_AUTH_SOCK

VAULT_FILE=${VAULT_FILE:-/app/config/credentials.yml}
VAULT_PASS_FILE=${VAULT_PASS_FILE:-/app/config/credentials.password.txt}
export VAULT_FILE
export VAULT_PASS_FILE

CMD=$1
shift
case $CMD in
  api)
    echo "Starting dev API server..."
    exec uv run uvicorn --app-dir /app/src --host "0.0.0.0" --port 8000 server:app
    #exec $PYTHON_BIN uvicorn --app-dir /app/src orchestra.server:app
    ;;


  celery-worker)
    echo "Starting celery worker..."
    sleep 3 # wait for other services to be ready
    exec uv run celery --workdir /app/src -A celery_worker.celery worker --loglevel=INFO -E
    ;;


  celery-flower)
    echo "Starting celery flower..."
    sleep 3 # wait for other services to be ready
    exec uv run celery --workdir /app/src -A celery_worker.celery flower --loglevel=INFO --basic-auth=${FLOWER_USER_NAME}:${FLOWER_USER_PASSWORD}
    ;;


  ssh-agent)
    echo "Starting ssh-agent at $SSH_AUTH_SOCK..."
    mkdir -p "/ssh-agent" && chmod 700 "/ssh-agent"
    rm -f "$SSH_AUTH_SOCK"
    # Start the ssh-agent and keep it running in the background
    eval "$(ssh-agent -a "$SSH_AUTH_SOCK")"
    echo "SSH_AUTH_SOCK=$SSH_AUTH_SOCK"
    echo "SSH_AGENT_PID=$SSH_AGENT_PID"

    # load all keys from vault
    if ! uv run /app/src/ssh_load_keys.py ; then
      echo "WARNING! Failed to load SSH keys from vault"
      #exit 1
    fi

    # delegate to a keepalive process to keep the agent alive
    exec "$0" ssh-agent-keepalive
    ;;


  ssh-agent-keepalive)
    echo "Starting ssh-agent keepalive..."
    # Keep the container running to maintain the ssh-agent
    while true; do
      ssh-add -l > /dev/null # List added keys to keep the agent active
      sleep 60
    done
    ;;


  ssh-connect)
    # Test connection to a remote server using SSH
    # Usage: ./entrypoint.sh ssh-connect user@hostname
    if [ -z "$1" ]; then
      echo "Usage: $0 ssh-connect <user@hostname>"
      exit 1
    fi
    echo "Testing SSH connection to $1..."
    exec ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$1" "echo 'SSH connection successful!'"
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
