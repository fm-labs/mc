#!/bin/bash
set -e
curl --silent --fail http://localhost:80/
if [ $? -ne 0 ]; then
  echo "Health check failed"
  exit 1
fi
exit 0
