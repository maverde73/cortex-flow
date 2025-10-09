#!/bin/bash

# Run script for simple_research MCP Server

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting simple_research MCP Server${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo -e "${YELLOW}No .env file found. Copying from .env.example...${NC}"
        cp .env.example .env
        echo "Please edit .env and add your API keys"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update requirements
echo "Installing requirements..."
pip install -q -r requirements.txt

# Create logs directory if it doesn't exist
mkdir -p logs

# Parse command line arguments
TRANSPORT="${1:-stdio}"
PORT="${2:-8000}"

if [ "$TRANSPORT" == "http" ]; then
    echo -e "${GREEN}Starting HTTP server on port $PORT...${NC}"
    python server.py --transport streamable-http --port "$PORT" --host 0.0.0.0
else
    echo -e "${GREEN}Starting stdio server...${NC}"
    python server.py --transport stdio
fi
