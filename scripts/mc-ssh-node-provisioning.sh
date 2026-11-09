#!/bin/bash
set -euox pipefail

SSH_TARGET=${1:?SSH_TARGET missing}
SSH_ARGS="-o ConnectTimeout=10"
echo "SSH_ARGS: $SSH_ARGS"

# Probe the server, run whoami
if ! ssh -t $SSH_ARGS ${SSH_TARGET} "whoami" ; then
  echo "SSH probe failed"
  exit 1
fi

TEMPLATE=mc-node-default
exec ssh $SSH_ARGS ${SSH_TARGET} \
  TEMPLATE="$TEMPLATE" \
  bash -s << 'EOF'
set -euox pipefail

echo "Hi $(whoami)"
echo "Provisioning new node using template ${TEMPLATE} ..."
echo "!!! This is a stub script. NOT IMPLEMENTED YET !!!
sleep 3
echo "ByeBye!"
EOF