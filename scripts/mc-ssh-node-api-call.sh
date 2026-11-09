#!/bin/bash
set -euox pipefail

SSH_TARGET=${1:?SSH_TARGET missing}
API_KEY=${2:-}
API_PATH=${3:-/api/health}

SSH_ARGS="-o ConnectTimeout=10"
exec ssh $SSH_ARGS -t ${SSH_TARGET} \
  API_KEY="$API_KEY" \
  API_PATH="$API_PATH" \
  bash -s << 'EOF'
set -euo pipefail

echo "Calling internal API..."

BASE_URL="http://localhost:3080"

# GET request
#curl -sS "$BASE_URL/api/health"

# POST request
#curl -sS -X POST "$BASE_URL/api/data" \
#  -H "Content-Type: application/json" \
#  -d '{"name":"test","enabled":true}'

# GET request with auth
curl -sSv "${BASE_URL}${API_PATH}" \
   -H "Content-Type: application/json" \
   -H "x-api-key: ${API_KEY}"

echo "Done!"
EOF