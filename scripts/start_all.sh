#!/bin/bash

# Start Cortex Flow Workflow Server
# Workflow-centric architecture: workflows ARE the agents!
# No need for separate analyst/writer/researcher servers

set -e

echo "🚀 Starting Cortex Flow Workflow Engine..."
echo ""

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Activate virtual environment
source .venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure your API keys"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Set PYTHONPATH to project root for imports to work
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo "🎯 Starting Workflow Server (port 8000)..."
python servers/supervisor_server.py > logs/supervisor.log 2>&1 &
SUPERVISOR_PID=$!

# Wait for server to be ready
echo ""
echo "⏳ Waiting for server to start..."
sleep 3

# Health check
echo ""
echo "🏥 Checking server health..."

check_health() {
    local port=$1
    local name=$2
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "   ✅ $name is healthy"
        return 0
    else
        echo "   ❌ $name failed to start"
        return 1
    fi
}

if check_health 8000 "Workflow Server"; then
    echo ""
    echo "✅ Workflow Server is running!"
    echo ""
    echo "API Endpoint:   http://localhost:8000"
    echo "Swagger Docs:   http://localhost:8000/docs"
    echo ""
    echo "Architecture:   Workflow-centric (LLM-native)"
    echo "  • Direct LLM invocation (OpenRouter, OpenAI, Anthropic, Groq, Google)"
    echo "  • MCP tools integration"
    echo "  • Sub-workflow composition"
    echo "  • Python library execution"
    echo ""
    echo "View logs:"
    echo "  tail -f logs/supervisor.log"
    echo ""
    echo "To stop: scripts/stop_all.sh"
    echo ""

    # Save PID
    echo "$SUPERVISOR_PID" > logs/supervisor.pid
else
    echo ""
    echo "❌ Workflow server failed to start. Check logs/supervisor.log for details."
    exit 1
fi
