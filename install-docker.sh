#!/bin/bash
set -e

. /etc/os-release

# check if user is root
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root" >&2
  exit 1
fi

# check if dist is ubuntu or debian (docker has a repo for each)
if [ "$ID" != "ubuntu" ] && [ "$ID" != "debian" ]; then
  echo "This script only supports Ubuntu and Debian (found: $ID)" >&2
  exit 1
fi

# add docker apt repo
apt update
apt install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/$ID/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$ID $VERSION_CODENAME stable" \
  > /etc/apt/sources.list.d/docker.list
apt update

# install docker
apt install -y --no-install-recommends docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

# verify installation
docker --version
docker compose version
docker info --format 'Docker engine {{.ServerVersion}} is running'
