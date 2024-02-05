@echo off
setlocal enabledelayedexpansion

call scripts/docker_compose.bat

if "%DOCKER_COMPOSE%" equ "" (
    echo ERROR: neither "docker compose" nor "docker-compose" appear to be installed.
    cmd /k
    exit /b 1
)

cd /d %~dp0
cd 3dcitydb_viewer

%DOCKER_COMPOSE% down -v

cd /d %~dp0
cd webapp

%DOCKER_COMPOSE% down -v

cd /d %~dp0
cd age_viewer

%DOCKER_COMPOSE% down -v

cd /d %~dp0
cd db

%DOCKER_COMPOSE% down -v

docker network rm calcun-network

echo EVERYTHING CLEANED SUCCESSFULLY!

cmd /k