#!/bin/bash

docker container stop mc-traefik
docker container rm mc-traefik
docker network rm traefik
exit 0
