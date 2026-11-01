#!/bin/bash

set -eua

VOLUME=${1:?VOLUME_NOT_SET}
BACKUP_DIR=${2:?BACKUP_DIR_NOT_SET}

mkdir -p "${BACKUP_DIR}"

docker run --rm \
  -v "${VOLUME}":/data:ro \
  -v "${BACKUP_DIR}":/backup \
  alpine tar czf "/backup/${VOLUME}-backup.tar.gz" --numeric-owner -C /data .
