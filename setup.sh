#!/bin/bash

source scripts/docker_compose.sh

if [ -z "$DOCKER_COMPOSE" ]; then
    echo "ERROR: neither \"docker compose\" nor \"docker-compose\" appear to be installed."
    exit 1
fi

export DOCKER_DEFAULT_PLATFORM=linux/amd64
export DOCKER_COMPOSE_ARGS="up --force-recreate --build -d --remove-orphans --wait"

cd "$(dirname "$0")"
mkdir -p ingestion_data
cd db

cp .env.example .env

$DOCKER_COMPOSE $DOCKER_COMPOSE_ARGS

while ! $DOCKER_COMPOSE exec db-pg pg_isready -U calcun > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL to start..."
    sleep 5
done

echo "PostgreSQL connected, will wait for 20s to complete further processing in database..."

sleep 20

cd ..
cd age_viewer

cp .env.example .env

$DOCKER_COMPOSE $DOCKER_COMPOSE_ARGS

cd ..
cd webapp

cp .env.example .env

$DOCKER_COMPOSE $DOCKER_COMPOSE_ARGS

$DOCKER_COMPOSE exec geodjango python manage.py migrate --noinput
%DOCKER_COMPOSE% exec geodjango python manage.py dummy_building_seed_command "x3d/management/commands/DT_DB_Designv0 - Buildings.csv"
%DOCKER_COMPOSE% exec geodjango python manage.py dummy_events_seed_command "x3d/management/commands/events_data.csv"
%DOCKER_COMPOSE% exec geodjango python manage.py dummy_network_seed_command "x3d/management/commands/network_data.csv"

$DOCKER_COMPOSE exec -e DJANGO_SUPERUSER_USERNAME=admin -e DJANGO_SUPERUSER_PASSWORD=admin -e DJANGO_SUPERUSER_EMAIL=admin@admin.com geodjango python manage.py createsuperuser --noinput

cd ..

docker run --rm --name impexp --network calcun-network -v ./db/3dcitydbdata/:/data 3dcitydb/impexp:5.4.0 import -T postgresql -H db-pg -P 5432 -d citydb_v4 -S citydb -u calcun -p test Railway_Scene_LoD3.zip

cd 3dcitydb_viewer
cp .env.example .env
$DOCKER_COMPOSE $DOCKER_COMPOSE_ARGS

echo "EVERYTHING SETUP SUCCESSFULLY!"