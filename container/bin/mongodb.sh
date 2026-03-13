#!/usr/bin/env bash
set -euo pipefail

: "${MONGO_INITDB_ROOT_USERNAME:?Missing MONGO_INITDB_ROOT_USERNAME}"
: "${MONGO_INITDB_ROOT_PASSWORD:?Missing MONGO_INITDB_ROOT_PASSWORD}"
: "${MONGO_APP_DATABASE:?Missing MONGO_APP_DATABASE}"
: "${MONGO_APP_USERNAME:?Missing MONGO_APP_USERNAME}"
: "${MONGO_APP_PASSWORD:?Missing MONGO_APP_PASSWORD}"

DBPATH="/data/db"

if [ ! -f "$DBPATH/.mongodb_initialized" ]; then
  echo "Initializing MongoDB users..."

  mkdir -p "$DBPATH"

  mongod --dbpath "$DBPATH" --bind_ip 127.0.0.1 --port 27017 --logpath /tmp/mongod-init.log --fork

  cleanup() {
    mongosh --quiet --host 127.0.0.1 --port 27017 --eval 'db.adminCommand({ shutdown: 1 })' || true
  }
  trap cleanup EXIT

  until mongosh --quiet --host 127.0.0.1 --port 27017 --eval "db.adminCommand({ ping: 1 }).ok" | grep -q 1; do
    sleep 1
  done

  mongosh --quiet --host 127.0.0.1 --port 27017 admin <<EOF
db.createUser({
  user: "$MONGO_INITDB_ROOT_USERNAME",
  pwd: "$MONGO_INITDB_ROOT_PASSWORD",
  roles: [ { role: "root", db: "admin" } ]
})

db.getSiblingDB("$MONGO_APP_DATABASE").createUser({
  user: "$MONGO_APP_USERNAME",
  pwd: "$MONGO_APP_PASSWORD",
  roles: [ { role: "readWrite", db: "$MONGO_APP_DATABASE" } ]
})
EOF

  touch "$DBPATH/.mongodb_initialized"
  cleanup
  trap - EXIT
fi

exec mongod --config /etc/mongo/mongod.conf
