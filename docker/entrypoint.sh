#!/bin/bash


PYTHON_PATH="/app/src:$PYTHON_PATH"
export PYTHONPATH

DEV_MODE=${DEV_MODE:-0}

FLOWER_USER_NAME=${FLOWER_USER_NAME:-admin}
FLOWER_USER_PASSWORD=${FLOWER_USER_PASSWORD:-admin}

# Not recommended to change the socket path, but provided for flexibility.
# The pre-defined path is used in the Dockerfile to create socket and set permissions.
SSH_AUTH_SOCK=${SSH_AUTH_SOCK:-/ssh-agent/agent.sock}
export SSH_AUTH_SOCK
SSH_CONFIG=${SSH_CONFIG:-/home/app/.ssh/config}
export SSH_CONFIG

VAULT_FILE=${VAULT_FILE:-/data/credentials.vault}
VAULT_PASS_FILE=${VAULT_PASS_FILE:-/run/secrets/credentials_vault_pass}
export VAULT_FILE
export VAULT_PASS_FILE

GIT_SSH_COMMAND="ssh -F $SSH_CONFIG"
export GIT_SSH_COMMAND
DOCKER_SSH_COMMAND="ssh -F $SSH_CONFIG"
export DOCKER_SSH_COMMAND


CMD=$1
shift
case $CMD in
  api)
    #echo "Starting dev API server..."
    #if [ "$DEV_MODE" -eq 1 ]; then
    #  echo "Development mode is ON"
    #  exec uv run uvicorn --app-dir /app/src --host "0.0.0.0" --port 8000 server:app --reload
    #else
    #  echo "Development mode is OFF"
    #  exec uv run uvicorn --app-dir /app/src --host "0.0.0.0" --port 8000 server:app
    #fi
    echo "Starting API server: Waiting for other services ..."
    sleep 15 # wait for other services to be ready
    echo "Starting API server: Starting on 0.0.0.0:8000 ..."
    exec uv run uvicorn --app-dir /app/src --host "0.0.0.0" --port 8000 server:app
    ;;


  scan)
    echo "Running various inventory scans..."
    sleep 60 # wait for other services to be ready
    uv run /app/src/hostsping.py
    uv run /app/src/hostsfacts.py all

    # continuously run the scans every 5 minutes
    while true; do
      uv run /app/src/hostsping.py
      uv run /app/src/hostsfacts.py all
      sleep 300
    done
    ;;


  celery-worker)
    echo "Starting celery worker..."
    sleep 30 # wait for other services to be ready
    exec uv run celery --workdir /app/src -A celery_worker.celery worker --loglevel=INFO -E
    ;;


  celery-flower)
    echo "Starting celery flower..."
    sleep 30 # wait for other services to be ready
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
      rm -f /tmp/ssh-load-keys-success
      touch /tmp/ssh-load-keys-failed
      #exit 1
    else
      echo "SSH keys loaded successfully from vault"
      rm -f /tmp/ssh-load-keys-failed
      touch /tmp/ssh-load-keys-success
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

  mcp-server-stdio)
    echo "Starting MCP server in stdio mode..."
    export MCP_TRANSPORT=stdio
    exec uv run --directory /app src/mcp_server.py
    ;;

  help)
    echo "Usage: $0 {api|celery-worker|supervisor|help}"
    exit 0
    ;;
esac

echo "Unknown command: $CMD"
exec "$@"
