#!/bin/bash
set -e
curl --silent --fail http://localhost:3080/api/health
if [ $? -ne 0 ]; then
  echo "Health check failed"
  exit 1
fi
exit 0
