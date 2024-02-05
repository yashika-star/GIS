@echo off
setlocal enabledelayedexpansion

call scripts/docker_compose.bat

if "%DOCKER_COMPOSE%" equ "" (
    echo ERROR: neither "docker compose" nor "docker-compose" appear to be installed.
    cmd /k
    exit /b 1
)

set DOCKER_COMPOSE_BUILD_ARGS=build --no-cache
set DOCKER_COMPOSE_UP_ARGS=up --force-recreate -d --remove-orphans --wait

cd /d %~dp0
mkdir ingestion_data 2> NUL
cd db

copy ".env.example" ".env"

%DOCKER_COMPOSE% %DOCKER_COMPOSE_BUILD_ARGS%
%DOCKER_COMPOSE% %DOCKER_COMPOSE_UP_ARGS%

:LOOP
%DOCKER_COMPOSE% exec db-pg pg_isready -U calcun >nul 2>&1
if !errorlevel! equ 0 (
    echo PostgreSQL connected, will wait for 20s to complete further processing in database...
) else (
    echo Waiting for PostgreSQL to start...
    timeout /t 5 >nul
    goto LOOP
)

timeout /t 20 >nul

cd /d %~dp0
cd age_viewer

copy ".env.example" ".env"

%DOCKER_COMPOSE% %DOCKER_COMPOSE_BUILD_ARGS%
%DOCKER_COMPOSE% %DOCKER_COMPOSE_UP_ARGS%

cd /d %~dp0
cd webapp

copy ".env.example" ".env"

%DOCKER_COMPOSE% %DOCKER_COMPOSE_BUILD_ARGS%
%DOCKER_COMPOSE% %DOCKER_COMPOSE_UP_ARGS%

%DOCKER_COMPOSE% exec geodjango python manage.py migrate --noinput
%DOCKER_COMPOSE% exec geodjango python manage.py dummy_building_seed_command "x3d/management/commands/DT_DB_Designv0 - Buildings.csv"
%DOCKER_COMPOSE% exec geodjango python manage.py dummy_events_seed_command "x3d/management/commands/events_data.csv"
%DOCKER_COMPOSE% exec geodjango python manage.py dummy_network_seed_command "x3d/management/commands/network_data.csv"

%DOCKER_COMPOSE% exec -e DJANGO_SUPERUSER_USERNAME=admin -e DJANGO_SUPERUSER_PASSWORD=admin -e DJANGO_SUPERUSER_EMAIL=admin@admin.com geodjango python manage.py createsuperuser --noinput

cd /d %~dp0

docker run --rm --name impexp --network calcun-network -v .\db\3dcitydbdata\:/data 3dcitydb/impexp:5.4.0 import -T postgresql -H db-pg -P 5432 -d citydb_v4 -S citydb -u calcun -p test Railway_Scene_LoD3.zip

cd 3dcitydb_viewer
copy ".env.example" ".env"
%DOCKER_COMPOSE% %DOCKER_COMPOSE_BUILD_ARGS%
%DOCKER_COMPOSE% %DOCKER_COMPOSE_UP_ARGS%

echo EVERYTHING SETUP SUCCESSFULLY!

cmd /k