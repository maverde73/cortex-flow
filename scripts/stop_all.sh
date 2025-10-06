#!/bin/bash

# Stop all running agent servers

echo "🛑 Stopping Cortex Flow agents..."

if [ -d logs ]; then
    for pidfile in logs/*.pid; do
        if [ -f "$pidfile" ]; then
            PID=$(cat "$pidfile")
            if kill -0 "$PID" 2>/dev/null; then
                echo "   Stopping process $PID..."
                kill "$PID"
            fi
            rm "$pidfile"
        fi
    done
fi

# Fallback: kill by port
pkill -f "researcher_server.py" 2>/dev/null
pkill -f "analyst_server.py" 2>/dev/null
pkill -f "writer_server.py" 2>/dev/null
pkill -f "supervisor_server.py" 2>/dev/null

echo "✅ All agents stopped"
