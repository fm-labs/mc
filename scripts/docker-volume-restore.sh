#!/bin/bash

set -eua

VOLUME=${1:?VOLUME_NOT_SET}
BACKUP_FILE=${2:?BACKUP_FILE_NOT_SET}

docker run --rm \
  -v "${VOLUME}":/data \
  -v "${BACKUP_FILE}":/backup \
  alpine tar xzf "/backup/${VOLUME}-backup.tar.gz" --numeric-owner -C /data