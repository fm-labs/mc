#!/bin/bash
set -e
#curl --silent --fail http://localhost:8000/
curl --silent http://localhost:8000/
if [ $? -ne 0 ]; then
  echo "Health check failed"
  exit 1
fi
exit 0
