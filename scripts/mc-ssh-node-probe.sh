#!/bin/bash
set -euox pipefail

SSH_TARGET=${1:?SSH_TARGET missing}
SSH_ARGS="-o ConnectTimeout=10"

exec ssh -t ${SSH_TARGET} 'whoami'