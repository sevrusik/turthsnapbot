#!/bin/bash

# TruthSnap Bot - Stop Local Services

echo "🛑 Stopping TruthSnap Bot..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Stop processes by PID
if [ -d ".pids" ]; then
    for pidfile in .pids/*.pid; do
        if [ -f "$pidfile" ]; then
            PID=$(cat "$pidfile")
            if ps -p $PID > /dev/null 2>&1; then
                kill $PID 2>/dev/null
                echo -e "${GREEN}✓${NC} Stopped $(basename $pidfile .pid)"
            fi
            rm "$pidfile"
        fi
    done
    rmdir .pids 2>/dev/null
fi

# Stop Redis
redis-cli shutdown 2>/dev/null
echo -e "${GREEN}✓${NC} Stopped Redis"

# Stop any remaining processes
pkill -f "uvicorn backend.api.main:app" 2>/dev/null
pkill -f "app.bot.main" 2>/dev/null
pkill -f "rq worker" 2>/dev/null
pkill -f "minio server" 2>/dev/null

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
