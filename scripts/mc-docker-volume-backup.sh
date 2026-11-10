#!/bin/bash

set -eua

VOLUME=${1:?VOLUME_NOT_SET}
BACKUP_DIR=${2:?BACKUP_DIR_NOT_SET}

DATE=$(date '+%Y-%m-%d-%H-%M-%S')
BACKUP_FILE="${VOLUME}-backup-${DATE}.tar.gz"

docker run --rm \
  -v "${VOLUME}":/data:ro \
  -v "${BACKUP_DIR}":/backup \
  alpine tar czvf "/backup/${BACKUP_FILE}" --numeric-owner -C /data .

echo "Saved to ${BACKUP_DIR}/${BACKUP_FILE}"
exit 0