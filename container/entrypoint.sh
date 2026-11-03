#!/bin/bash

set -eua

PATH=/app/.venv/bin:/app/bin:/var/lib/mc/bin:$PATH
export PATH
PYTHONPATH="/app/src:${PYTHONPATH:-}"
export PYTHONPATH

# Not recommended to change the socket path, but provided for flexibility.
SSH_AUTH_SOCK=/ssh-agent/agent.sock
export SSH_AUTH_SOCK
SSH_CONFIG=${SSH_CONFIG:-/home/app/.ssh/config}
export SSH_CONFIG

GIT_SSH_COMMAND="ssh -F $SSH_CONFIG"
export GIT_SSH_COMMAND
DOCKER_SSH_COMMAND="ssh -F $SSH_CONFIG"
export DOCKER_SSH_COMMAND

FLOWER_USER_NAME=${FLOWER_USER_NAME:-}
FLOWER_USER_PASSWORD=${FLOWER_USER_PASSWORD:-}

REDIS_DATA_DIR=${REDIS_DATA_DIR:-/redis}
export REDIS_DATA_DIR

#VAULT_ENABLED=${VAULT_ENABLED:-true}
#VAULT_FILE=${VAULT_FILE:-/data/credentials.vault}
#VAULT_PASS_FILE=${VAULT_PASS_FILE:-/data/credentials.vault.pass}
#if [ ! -f "$VAULT_PASS_FILE" ]; then
#  #echo "Vault pass file not found, creating a new secure one..."
#  #head -c 32 /dev/urandom | base64 > "$VAULT_PASS_FILE"
#  #chmod 600 "$VAULT_PASS_FILE"
#  #echo "Vault pass file created at $VAULT_PASS_FILE"
#  echo "warning: Vault pass file not found at $VAULT_PASS_FILE"
#fi
#export VAULT_FILE
#export VAULT_PASS_FILE


init_ssl() {
  echo "Initializing SSL configuration ..."
  mkdir -p ${MC_CONFIG_DIR}/ssl

  # Generate custom self-signed certificate
  if [[ ! -f ${MC_CONFIG_DIR}/ssl/self-signed.crt ]]; then
    echo "Generating self-signed certificate ..."
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout ${MC_CONFIG_DIR}/ssl/self-signed.key -out ${MC_CONFIG_DIR}/ssl/self-signed.crt -subj '/CN=localhost'
    RC=$?
    if [[ $RC != 0 ]]; then
      echo "ERROR: Failed to generate self-signed certificate"
      exit 1
    fi
  fi

  # Generate custom dhparam.pem
  if [[ ! -f ${MC_CONFIG_DIR}/ssl/dhparam.pem ]]; then
    echo "Generating dhparam.pem ..."
    openssl dhparam -out ${MC_CONFIG_DIR}/ssl/dhparam.pem 2048
    RC=$?
    if [[ $RC != 0 ]]; then
      echo "ERROR: Failed to generate dhparam.pem"
      exit 1
    fi
  fi

  # Use self signed cert, if no other cert is available
  if [[ ! -f /etc/nginx/ssl/cert.pem ]]; then
    echo "Using self signed cert ..."
    ln -sf ${MC_CONFIG_DIR}/ssl/self-signed.crt /etc/nginx/ssl/cert.pem
    ln -sf ${MC_CONFIG_DIR}/ssl/self-signed.key /etc/nginx/ssl/key.pem
  fi

  # Use custom dhparam.pem, if no other dhparam.pem is available
  if [[ ! -f /etc/nginx/ssl/dhparam.pem ]]; then
    echo "Using self signed cert ..."
    ln -sf ${MC_CONFIG_DIR}/ssl/dhparam.pem /etc/nginx/ssl/dhparam.pem
  fi

  # alpine-specific adjustments
  #if [[ "${MC_ALPINE}" == "1" ]]; then
  #  echo "Running in alpine mode, adjusting nginx configuration for alpine ..."
  #fi

  # Test nginx configuration
  ls -la /etc/nginx/ssl
  if ! nginx -t ; then
    echo "ERROR: Failed to test nginx configuration"
    exit 1
  fi
}




CMD=$1
shift
case $CMD in

  #devserver)
  #  echo "Development mode is ON"
  #  exec python -m uvicorn --app-dir /app/src --host "0.0.0.0" --port 5000 server:app --reload
  #  ;;

  api)
    echo "Starting API server: Waiting for other services ..."
    sleep 1 # wait for other services to be ready
    echo "Starting API server: Starting on 0.0.0.0:5000 ..."
    exec python -m uvicorn --app-dir /app/src --host "0.0.0.0" --port 5000 server:app
    #exec python -m uvicorn --app-dir /app/src --host "0.0.0.0" --port 5000 server:app
    #exec /usr/bin/mc-srv
    ;;

  nginx)
    init_ssl
    echo "Starting nginx..."
    exec nginx -g "daemon off;"
    ;;

  redis)
    echo "Starting redis server..."
    exec redis-server /etc/redis/redis.conf --protected-mode no --dir /redis
    ;;

  #  scan)
  #    echo "Running various inventory scans..."
  #    sleep 60 # wait for other services to be ready
  #    python /app/src/hostsping.py
  #    python /app/src/hostsfacts.py all
  #    python /app/src/hoststunnel.py
  #
  #    # continuously run the scans every 5 minutes
  #    while true; do
  #    #  python /app/src/hostsping.py
  #    #  python /app/src/hostsfacts.py all
  #    #  python /app/src/hoststunnel.py
  #      sleep 300
  #    done
  #    ;;

  celery-worker)
    echo "Starting celery worker..."
    sleep 30 # wait for other services to be ready
    exec python -m celery --workdir /app/src -A celery_worker.celery worker --loglevel=INFO -E
    ;;

  celery-flower)
    echo "Starting celery flower..."
    sleep 30 # wait for other services to be ready
    exec python -m celery --workdir /app/src -A celery_worker.celery flower --loglevel=INFO --basic-auth=${FLOWER_USER_NAME:-}:${FLOWER_USER_PASSWORD:-}
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
    #chown app:app /home/app/.ssh
    #chmod 700 /home/app/.ssh

    #    # check if the app user has a default RSA ssh key, if not generate one
    #    if [ ! -f /home/app/.ssh/id_rsa ]; then
    #      echo "No default SSH key found for app user, generating one..."
    #      ssh-keygen -t rsa -b 4096 -f /home/app/.ssh/id_rsa -N "" -C "default"
    #      chown app:app /home/app/.ssh/id_rsa*
    #      chmod 600 /home/app/.ssh/id_rsa
    #    else
    #      echo "Default SSH key found for app user."
    #    fi
    #    ssh-add /home/app/.ssh/id_rsa
    #    echo "Default SSH public key:"
    #    cat /home/app/.ssh/id_rsa.pub

    #    # check if the app user has a default ED25519 ssh key, if not generate one
    #    if [ ! -f /home/app/.ssh/ed25519 ]; then
    #      echo "No default SSH key found for app user, generating one..."
    #      ssh-keygen -t ed25519 -f /home/app/.ssh/ed25519 -N "" -C "default"
    #      chown app:app /home/app/.ssh/ed25519*
    #      chmod 600 /home/app/.ssh/ed25519
    #    else
    #      echo "Default SSH key found for app user."
    #    fi
    #    # add the default key to the agent
    #    ssh-add /home/app/.ssh/ed25519
    #    echo "Default SSH public key:"
    #    cat /home/app/.ssh/ed25519.pub
    #
    #    # Ensure known_hosts file exists
    #    touch /home/app/.ssh/known_hosts
    #    chown app:app /home/app/.ssh/known_hosts
    #    chmod 600 /home/app/.ssh/known_hosts
    #
    #    # load all keys from vault
    #    if ! python /app/src/ssh_agent.py ; then
    #      echo "WARNING! Failed to load SSH keys from vault"
    #      rm -f /tmp/ssh-load-keys-success
    #      touch /tmp/ssh-load-keys-failed
    #      #exit 1
    #    else
    #      echo "SSH keys loaded successfully from vault"
    #      rm -f /tmp/ssh-load-keys-failed
    #      touch /tmp/ssh-load-keys-success
    #    fi


    # start the hoststunnel process to maintain SSH tunnels
    #echo "Starting hoststunnel process..."
    #python /app/src/hoststunnel.py

    # scan for keys and add to agent
    if ! ssh-add-all ; then
      echo "WARNING! Failed to add some SSH keys"
    fi

    # delegate to a keepalive process to keep the agent alive
    echo "SSH_AUTH_SOCK=$SSH_AUTH_SOCK"
    export SSH_AUTH_SOCK=$SSH_AUTH_SOCK
    exec "$0" ssh-agent-keepalive
    ;;

  ssh-agent-keepalive)
    echo "Starting ssh-agent keepalive... ${SSH_AUTH_SOCK}"
    # Keep the container running to maintain the ssh-agent
    while true; do
      export SSH_AUTH_SOCK=$SSH_AUTH_SOCK
      ssh-add -l > /dev/null || true # List added keys to keep the agent active
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
    export MCP_TRANSPORT=stdio
    exec python /app/src/mcp_server.py
    ;;

  mcp-server-http)
    export MCP_TRANSPORT=streamable-http
    export MCP_HOST=0.0.0.0
    exec python /app/src/mcp_server.py
    ;;

  help)
    echo "Usage: $0 {api|celery-worker|supervisor|mcp-server-stdio|mcp-server-http|help}"
    exit 0
    ;;
esac

echo "Unknown command: $CMD"
exec "$@"
