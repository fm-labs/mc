#!/bin/bash

set -xe

PROJECT_NAME="mc"
CONTAINER_NAME="${PROJECT_NAME}-dev"
IMAGE_NAME="${PROJECT_NAME}:dev"
DOCKER_COMPOSE_FILE="compose.dev.yaml"

CMD=$1

case $CMD in
  api)
    echo "Starting dev API server..."
    uvicorn --app-dir ./src server:app --reload
    ;;

  celery-worker)
    echo "Starting celery worker..."
    celery --workdir ./src -A celery_worker.celery worker --loglevel=INFO -E
    ;;

  celery-flower)
    echo "Starting celery flower..."
    celery --workdir ./src -A celery_worker.celery flower --loglevel=INFO
    ;;

  build-image)
    echo "Building docker image..."
    docker build -t $IMAGE_NAME -f ./Dockerfile .
    ;;

  buildx-image)
    echo "Building docker image with buildx..."
    docker buildx build --platform linux/amd64,linux/arm64 -t $IMAGE_NAME -f ./Dockerfile .
    ;;

  run-container)
    echo "Running docker container..."
    docker stop $CONTAINER_NAME || true
    docker rm $CONTAINER_NAME || true
    docker run -d --name $CONTAINER_NAME -p 3080:3080 $IMAGE_NAME
    ;;

  stop-container)
    echo "Stopping docker container..."
    docker stop $CONTAINER_NAME
    ;;

  rm-container)
    echo "Removing docker container..."
    docker rm $CONTAINER_NAME
    ;;

  stack-up)
    echo "Starting docker stack..."
    docker compose -f $DOCKER_COMPOSE_FILE -p $PROJECT_NAME up --build -d
    ;;

  devstack-up)
    echo "Starting docker stack..."
    docker compose -f $DOCKER_COMPOSE_FILE -p $PROJECT_NAME up --build --watch
    ;;

  alpine-up)
    echo "Starting docker stack..."
    docker compose -f "compose.dev.alpine.yaml" -p $PROJECT_NAME up --build -d
    ;;

  cluster-up)
    echo "Starting docker stack..."
    docker compose -f $DOCKER_COMPOSE_FILE -p $PROJECT_NAME --profile cluster up --build -d
    ;;

  stack-down)
    echo "Stopping docker stack..."
    docker compose -f $DOCKER_COMPOSE_FILE -p $PROJECT_NAME down
    ;;

  vault-decrypt)
    echo "Decrypting ansible vault..."
    shift
    VAULT_FILE=$1
    if [ -z "$VAULT_FILE" ]; then
      echo "Usage: $0 vault-decrypt <vault_file> <password_file>"
      exit 1
    fi
    if [ ! -f "$VAULT_FILE" ]; then
      echo "Vault file not found: $VAULT_FILE"
      exit 1
    fi

    PASSWORD_FILE=$2
    if [ -z "$PASSWORD_FILE" ]; then
      echo "Usage: $0 vault-decrypt <vault_file> <password_file>"
      exit 1
    fi
    if [ ! -f "$PASSWORD_FILE" ]; then
      echo "Password file not found: $PASSWORD_FILE"
      exit 1
    fi

    ansible-vault decrypt $VAULT_FILE --vault-password-file $PASSWORD_FILE
    echo "Decrypted vault file: $VAULT_FILE"
    ;;

  vault-encrypt)
    echo "Encrypting ansible vault..."
    shift
    VAULT_FILE=$1
    if [ -z "$VAULT_FILE" ]; then
      echo "Usage: $0 vault-encrypt <vault_file> <password_file>"
      exit 1
    fi
    if [ ! -f "$VAULT_FILE" ]; then
      echo "Vault file not found: $VAULT_FILE"
      exit 1
    fi

    PASSWORD_FILE=$2
    if [ -z "$PASSWORD_FILE" ]; then
      echo "Usage: $0 vault-encrypt <vault_file> <password_file>"
      exit 1
    fi
    if [ ! -f "$PASSWORD_FILE" ]; then
      echo "Password file not found: $PASSWORD_FILE"
      exit 1
    fi

    ansible-vault encrypt $VAULT_FILE --vault-password-file $PASSWORD_FILE
    echo "Encrypted vault file: $VAULT_FILE"
    ;;

  *)
    echo "Usage: $0 {api|celery-worker|build-image|run-container|stop-container|rm-container}"
    exit 1
esac