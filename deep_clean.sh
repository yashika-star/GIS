#!/bin/bash

source scripts/docker_compose.sh

if [ -z "$DOCKER_COMPOSE" ]; then
    echo "ERROR: neither \"docker compose\" nor \"docker-compose\" appear to be installed."
    exit 1
fi

cd "$(dirname "$0")"
cd 3dcitydb_viewer

$DOCKER_COMPOSE down --rmi all -v --remove-orphans

cd ..
cd webapp

$DOCKER_COMPOSE down --rmi all -v --remove-orphans

cd ..
cd age_viewer

$DOCKER_COMPOSE down --rmi all -v --remove-orphans

cd ..
cd db

$DOCKER_COMPOSE down --rmi all -v --remove-orphans

docker network rm calcun-network

echo "EVERYTHING CLEANED SUCCESSFULLY!"