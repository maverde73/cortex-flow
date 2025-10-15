#!/bin/bash

# Stop Cortex Flow Workflow Server

echo "🛑 Stopping Cortex Flow Workflow Server..."

# Stop from PID file
if [ -f logs/supervisor.pid ]; then
    PID=$(cat logs/supervisor.pid)
    if kill -0 "$PID" 2>/dev/null; then
        echo "   Stopping Workflow Server (PID: $PID)..."
        kill "$PID"
    fi
    rm logs/supervisor.pid
fi

# Fallback: kill by process name
pkill -f "supervisor_server.py" 2>/dev/null

# Clean up any legacy agent servers (if still running)
pkill -f "researcher_server.py" 2>/dev/null
pkill -f "analyst_server.py" 2>/dev/null
pkill -f "writer_server.py" 2>/dev/null

# Remove legacy PID files
rm -f logs/researcher.pid logs/analyst.pid logs/writer.pid 2>/dev/null

echo "✅ Workflow Server stopped"
