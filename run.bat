@echo off
echo PTE Vocabulary Viewer Setup

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

REM Check for Docker
where docker >nul 2>nul
if %ERRORLEVEL% equ 0 (
    where docker-compose >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        echo Docker and Docker Compose found! Starting with Docker...
        docker-compose up --build
        exit /b 0
    )
)

REM Fallback to Python
echo Docker not found. Attempting to run with Python...

REM Check for Python
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    
    echo Starting the application...
    python -m uvicorn app:app --reload
) else (
    echo Error: Python not found!
    echo Please install Python 3.8+ to run this application without Docker.
    pause
    exit /b 1
)

pause
exit /b 0 