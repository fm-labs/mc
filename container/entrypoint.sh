#!/bin/bash


PYTHON_PATH="/app/src:$PYTHON_PATH"
export PYTHONPATH

DEV_MODE=${DEV_MODE:-0}

FLOWER_USER_NAME=${FLOWER_USER_NAME:-admin}
FLOWER_USER_PASSWORD=${FLOWER_USER_PASSWORD:-admin}

# Not recommended to change the socket path, but provided for flexibility.
SSH_AUTH_SOCK=${SSH_AUTH_SOCK:-/ssh-agent/agent.sock}
export SSH_AUTH_SOCK
SSH_CONFIG=${SSH_CONFIG:-/home/app/.ssh/config}
export SSH_CONFIG

#VAULT_FILE=${VAULT_FILE:-/data/credentials.vault}
#VAULT_PASS_FILE=${VAULT_PASS_FILE:-/run/secrets/credentials_vault_pass}
#export VAULT_FILE
#export VAULT_PASS_FILE

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
    #  exec uv run uvicorn --app-dir /app/src --host "0.0.0.0" --port 5000 server:app --reload
    #else
    #  echo "Development mode is OFF"
    #  exec uv run uvicorn --app-dir /app/src --host "0.0.0.0" --port 5000 server:app
    #fi
    echo "Starting API server: Waiting for other services ..."
    sleep 15 # wait for other services to be ready
    echo "Starting API server: Starting on 0.0.0.0:5000 ..."
    exec uv run uvicorn --app-dir /app/src --host "0.0.0.0" --port 5000 server:app
    ;;

  nginx)
    echo "Starting nginx..."
    exec nginx -g "daemon off;"
    ;;

  scan)
    echo "Running various inventory scans..."
    sleep 60 # wait for other services to be ready
    #rm -rf /home/app/.ansible/cp
    #rm -rf /home/app/.ansible/tmp
    uv run /app/src/hostsping.py
    uv run /app/src/hostsfacts.py all

    # continuously run the scans every 5 minutes
    while true; do
      uv run /app/src/hostsping.py
      uv run /app/src/hostsfacts.py all
      uv run /app/src/hoststunnel.py
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

    # ensure the .ssh directory exists
    mkdir -p /home/app/.ssh
    chown app:app /home/app/.ssh
    chmod 700 /home/app/.ssh


    # check if the app user has a default ssh key, if not generate one
    if [ ! -f /home/app/.ssh/id_rsa ]; then
      echo "No default SSH key found for app user, generating one..."
      ssh-keygen -t rsa -b 4096 -f /home/app/.ssh/id_rsa -N "" -C "app_default_key"
      chown app:app /home/app/.ssh/id_rsa*
      chmod 600 /home/app/.ssh/id_rsa

      # display the public key to the user
      echo "Generated SSH public key:"
      cat /home/app/.ssh/id_rsa.pub
    else
      echo "Default SSH key found for app user."
    fi

    # add the default key to the agent
    ssh-add /home/app/.ssh/id_rsa

    # Ensure known_hosts file exists
    touch /home/app/.ssh/known_hosts
    chown app:app /home/app/.ssh/known_hosts
    chmod 600 /home/app/.ssh/known_hosts

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

    # start the hoststunnel process to maintain SSH tunnels
    echo "Starting hoststunnel process..."
    uv run /app/src/hoststunnel.py

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
