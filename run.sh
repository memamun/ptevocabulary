#!/bin/bash

# Run PTE Vocabulary Viewer

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}PTE Vocabulary Viewer Setup${NC}"

# Check for database file
if [ ! -f "pte_vocabulary.db" ]; then
    echo -e "${YELLOW}Copying database file from parent directory...${NC}"
    cp ../pte_vocabulary.db .
    
    if [ ! -f "pte_vocabulary.db" ]; then
        echo -e "${RED}Error: pte_vocabulary.db not found!${NC}"
        echo "Please make sure the database file exists in the parent directory."
        exit 1
    fi
fi

# Check for Docker
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}Docker and Docker Compose found! Starting with Docker...${NC}"
    docker-compose up --build
    exit 0
fi

# Fallback to Python
echo -e "${YELLOW}Docker not found. Attempting to run with Python...${NC}"

# Check for Python
if command -v python3 &> /dev/null; then
    python_cmd="python3"
elif command -v python &> /dev/null; then
    python_cmd="python"
else
    echo -e "${RED}Error: Python not found!${NC}"
    echo "Please install Python 3.8+ to run this application without Docker."
    exit 1
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
$python_cmd -m pip install -r requirements.txt

# Run the application
echo -e "${GREEN}Starting the application...${NC}"
$python_cmd -m uvicorn app:app --reload

exit 0 