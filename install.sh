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
# - MC_DATA_DIR: The path to the directory where MissionControl will store its data (default: /opt/mc)
set -e
DOCKER=$(which docker)
DOCKER_HOME=${DOCKER_HOME:-/var/lib/docker}
DOCKER_SOCKET=${DOCKER_SOCKET:-/var/run/docker.sock}
MC_IMAGE=${MC_IMAGE:-fmlabs/mc:latest}
MC_CONTAINER_NAME=${MC_CONTAINER_NAME:-mc}
MC_PORT=${MC_PORT:-3080}
MC_PORT_SSL=${MC_PORT_SSL:-3443}
MC_DATA_DIR=${MC_DATA_DIR:-/opt/mc}

echo "Installing MissionControl with the following configuration:"
echo "DOCKER=${DOCKER}"
echo "DOCKER_HOME=${DOCKER_HOME}"
echo "DOCKER_SOCKET=${DOCKER_SOCKET}"
echo "MC_IMAGE=${MC_IMAGE}"
echo "MC_CONTAINER_NAME=${MC_CONTAINER_NAME}"
echo "MC_PORT=${MC_PORT}"
echo "MC_PORT_SSL=${MC_PORT_SSL}"
echo "MC_DATA_DIR=${MC_DATA_DIR}"

mkdir -p ${MC_DATA_DIR}

$DOCKER stop ${MC_CONTAINER_NAME} && $DOCKER rm ${MC_CONTAINER_NAME}
$DOCKER pull ${MC_IMAGE} && \
exec $DOCKER run -d \
  --name ${MC_CONTAINER_NAME} \
  --restart always \
  --group-add $(stat -c '%g' ${DOCKER_SOCKET}) \
  -p ${MC_PORT}:3080 \
  -p ${MC_PORT_SSL}:3443 \
  -v ${DOCKER_SOCKET}:/var/run/docker.sock:ro \
  -v ${MC_DATA_DIR}:/opt/mc \
  ${MC_IMAGE}
