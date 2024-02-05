@echo off
setlocal enabledelayedexpansion
REM Check if docker compose (v2) is installed
docker compose >nul 2>nul
if %errorlevel% equ 0 (
    echo SUCCESS: docker compose ^(v2^) is installed.
    set DOCKER_COMPOSE=docker compose
) else (
    REM Check if docker-compose (v1) is installed
    docker-compose >nul 2>nul
    if !errorlevel! equ 0 (
        echo SUCCESS: docker-compose ^(v1^) is installed.
        set DOCKER_COMPOSE=docker-compose
    )
)

REM Return the variable to the calling script
endlocal & set DOCKER_COMPOSE=%DOCKER_COMPOSE%
