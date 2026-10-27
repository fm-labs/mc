#!/bin/bash

VOLUME=${1:?VOLUME_NOT_SET}

mkdir -p "$(pwd)/backup"

docker run --rm \
  -v "${VOLUME}":/data:ro \
  -v "$(pwd)/backup":/backup \
  alpine tar czf "/backup/${VOLUME}-backup.tar.gz" --numeric-owner -C /data .

