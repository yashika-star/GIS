#!/bin/bash

if docker compose > /dev/null 2>&1 && [ $? -eq 0 ]; then
    echo "SUCCESS: docker compose (v2) is installed."
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose > /dev/null 2>&1; then
    echo "SUCCESS: docker-compose (v1) is installed."
    DOCKER_COMPOSE="docker-compose"
else
    echo "ERROR: neither \"docker-compose\" nor \"docker compose\" appear to be installed."
    exit 1
fi

# Return the variable to the calling script
export DOCKER_COMPOSE=$DOCKER_COMPOSE