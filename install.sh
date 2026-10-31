#!/bin/bash
# MissionControl install script
# This script will pull the latest MissionControl image and run it as a container.
# It will also stop and remove any existing container with the same name before starting a new one.
# It is safe to run this script multiple times, as it will always pull the latest image and restart the container.
# You can customize the behavior of this script by setting the following environment variables:
# - DOCKER_HOME: The path to the Docker home directory (default: /var/lib/docker)
# - DOCKER_SOCKET: The path to the Docker socket (default: /var/run/docker.sock)
# - MC_IMAGE: The name of the MissionControl Docker image to use (default: fmlabs/mc:latest)
# - MC_CONTAINER_NAME: The name of the MissionControl container to create (default: mc)
# - MC_PORT: The port to expose for the MissionControl web interface (default: 3080)
# - MC_PORT_SSL: The port to expose for the MissionControl web interface with SSL (default: 3443)
# - MC_DATA_VOLUME: The path to the directory where MissionControl will store its data (default: mc-data)
set -e
# local docker settings
DOCKER=$(which docker)
DOCKER_HOME=${DOCKER_HOME:-/var/lib/docker}
DOCKER_SOCKET=${DOCKER_SOCKET:-/var/run/docker.sock}

# default config
MC_IMAGE=${MC_IMAGE:-fmlabs/mc:latest}
MC_CONTAINER_NAME=${MC_CONTAINER_NAME:-mc}
MC_PORT=${MC_PORT:-3080}
MC_PORT_SSL=${MC_PORT_SSL:-3443}
MC_DATA_VOLUME=${MC_DATA_VOLUME:-mc-data}
MC_EXTRA_VOLUMES=""
MC_EXTRA_ARGS=""

# if file /etc/mc/docker.env exists, add it to the extra args
if [ -f /etc/mc/docker.env ]; then
  MC_EXTRA_ARGS="--env-file /etc/mc/docker.env"
fi

MC_PRE_INSTALL_HOOK=""
# default pre-install-hook
# if script /etc/mc/hooks/pre-install exists and is executable, register as pre-install-hook
if [ -x /etc/mc/hooks/pre-install ]; then
  MC_PRE_INSTALL_HOOK="/etc/mc/hooks/pre-install"
fi

# if file /etc/mc/install.env exists, source it
# override any MC_ env var there
if [ -f /etc/mc/install.env ]; then
  source /etc/mc/install.env
fi

echo "Installing MissionControl with the following configuration:"
echo "DOCKER=${DOCKER}"
echo "DOCKER_HOME=${DOCKER_HOME}"
echo "DOCKER_SOCKET=${DOCKER_SOCKET}"
echo "MC_IMAGE=${MC_IMAGE}"
echo "MC_CONTAINER_NAME=${MC_CONTAINER_NAME}"
echo "MC_PORT=${MC_PORT}"
echo "MC_PORT_SSL=${MC_PORT_SSL}"
echo "MC_DATA_VOLUME=${MC_DATA_VOLUME}"
echo "MC_EXTRA_VOLUMES=${MC_EXTRA_VOLUMES}"
echo "MC_EXTRA_ARGS=${MC_EXTRA_ARGS}"

# run the pre-install-hook, if any
if [ -n "${MC_PRE_INSTALL_HOOK}" ]; then
  echo "Running pre-install-hook as user $USER: ${MC_PRE_INSTALL_HOOK}"
  if ! ${MC_PRE_INSTALL_HOOK}; then
    echo "Pre-install-hook failed: ${MC_PRE_INSTALL_HOOK}"
    exit 1
  fi
fi

$DOCKER stop ${MC_CONTAINER_NAME} && $DOCKER rm ${MC_CONTAINER_NAME}
$DOCKER pull ${MC_IMAGE} && \
exec $DOCKER run -d \
  --name ${MC_CONTAINER_NAME} \
  --restart always \
  --group-add $(stat -c '%g' ${DOCKER_SOCKET}) \
  -p ${MC_PORT}:3080 \
  -p ${MC_PORT_SSL}:3443 \
  -v ${MC_DATA_VOLUME}:/opt/mc \
  -v ${DOCKER_SOCKET}:/var/run/docker.sock:ro \
  ${MC_EXTRA_VOLUMES} ${MC_EXTRA_ARGS} ${MC_IMAGE}
