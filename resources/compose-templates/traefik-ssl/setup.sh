#!/bin/bash

# Create the traefik network if it doesn't exist
if ! docker network inspect traefik-ssl >/dev/null 2>&1; then
    docker network create traefik-ssl
fi
