@echo off
echo Starting PTE Vocabulary Viewer with Docker...

REM Check for database file
if not exist "pte_vocabulary.db" (
    echo Copying database file from parent directory...
    copy ..\pte_vocabulary.db .
    
    if not exist "pte_vocabulary.db" (
        echo Error: pte_vocabulary.db not found!
        echo Please make sure the database file exists in the parent directory.
        pause
        exit /b 1
    )
)

REM Check if Docker is running
docker info >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Build and start containers
echo Building and starting Docker containers...
docker-compose up --build

pause
exit /b 0 