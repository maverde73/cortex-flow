#!/bin/bash

# Start all agent servers in development mode
# Each server runs in the background on its configured port

set -e

echo "🚀 Starting Cortex Flow Multi-Agent System..."
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

# Read enabled agents from .env (default to all)
ENABLED_AGENTS=$(grep -E "^ENABLED_AGENTS=" .env 2>/dev/null | cut -d '=' -f 2 | tr -d '"' | tr -d "'")
if [ -z "$ENABLED_AGENTS" ]; then
    ENABLED_AGENTS="researcher,analyst,writer"
fi

echo "📋 Enabled agents: $ENABLED_AGENTS"
echo ""

# Function to check if agent is enabled
is_enabled() {
    local agent=$1
    echo "$ENABLED_AGENTS" | grep -q "$agent"
}

# Start each agent server if enabled
if is_enabled "researcher"; then
    echo "📡 Starting Researcher Agent (port 8001)..."
    python servers/researcher_server.py > logs/researcher.log 2>&1 &
    RESEARCHER_PID=$!
fi

if is_enabled "analyst"; then
    echo "📊 Starting Analyst Agent (port 8003)..."
    python servers/analyst_server.py > logs/analyst.log 2>&1 &
    ANALYST_PID=$!
fi

if is_enabled "writer"; then
    echo "✍️  Starting Writer Agent (port 8004)..."
    python servers/writer_server.py > logs/writer.log 2>&1 &
    WRITER_PID=$!
fi

# Give specialized agents time to start
sleep 2

echo "🎯 Starting Supervisor Agent (port 8000)..."
python servers/supervisor_server.py > logs/supervisor.log 2>&1 &
SUPERVISOR_PID=$!

# Wait for servers to be ready
echo ""
echo "⏳ Waiting for servers to start..."
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

ALL_HEALTHY=true

# Only check enabled agents
if is_enabled "researcher"; then
    check_health 8001 "Researcher" || ALL_HEALTHY=false
fi

if is_enabled "analyst"; then
    check_health 8003 "Analyst" || ALL_HEALTHY=false
fi

if is_enabled "writer"; then
    check_health 8004 "Writer" || ALL_HEALTHY=false
fi

check_health 8000 "Supervisor" || ALL_HEALTHY=false

echo ""
if [ "$ALL_HEALTHY" = true ]; then
    echo "✅ All agents are running!"
    echo ""
    echo "Supervisor API: http://localhost:8000"
    echo "Swagger Docs:   http://localhost:8000/docs"
    echo ""
    echo "View logs:"
    echo "  tail -f logs/supervisor.log"
    echo "  tail -f logs/researcher.log"
    echo "  tail -f logs/analyst.log"
    echo "  tail -f logs/writer.log"
    echo ""
    echo "To stop all agents: ./stop_all.sh"
    echo ""

    # Save PIDs for enabled agents
    echo "$SUPERVISOR_PID" > logs/supervisor.pid

    if is_enabled "researcher"; then
        echo "$RESEARCHER_PID" > logs/researcher.pid
    fi

    if is_enabled "analyst"; then
        echo "$ANALYST_PID" > logs/analyst.pid
    fi

    if is_enabled "writer"; then
        echo "$WRITER_PID" > logs/writer.pid
    fi

else
    echo "❌ Some agents failed to start. Check logs/ directory for details."
    exit 1
fi
