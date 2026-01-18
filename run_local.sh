#!/bin/bash

# TruthSnap Bot - Local Run Script (Without Docker)

echo "🚀 Starting TruthSnap Bot Locally (No Docker)"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    echo "Install Python 3: brew install python@3.11"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found: $(python3 --version)"

# Check Redis
if ! command -v redis-server &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Redis not found"
    echo "Installing Redis via Homebrew..."
    brew install redis
fi

echo -e "${GREEN}✓${NC} Redis found"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}⚠ IMPORTANT: Edit .env and add your TELEGRAM_BOT_TOKEN${NC}"
    echo ""
    read -p "Press Enter to edit .env now..."
    nano .env
fi

# Load environment
export $(cat .env | grep -v '^#' | xargs)

# Check bot token
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_bot_token_here" ]; then
    echo -e "${RED}❌ TELEGRAM_BOT_TOKEN not configured${NC}"
    echo "Please edit .env and add your bot token"
    exit 1
fi

echo -e "${GREEN}✓${NC} Bot token configured"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install FraudLens dependencies
echo ""
echo "📦 Installing FraudLens dependencies..."
cd fraudlens
pip install -q -r requirements.txt
cd ..

# Install TruthSnap Bot dependencies
echo "📦 Installing TruthSnap Bot dependencies..."
cd truthsnap-bot
pip install -q -r requirements.txt
cd ..

echo -e "${GREEN}✓${NC} Dependencies installed"

# Start Redis
echo ""
echo "🔴 Starting Redis..."
redis-server --daemonize yes

sleep 2

if pgrep -x "redis-server" > /dev/null; then
    echo -e "${GREEN}✓${NC} Redis running"
else
    echo -e "${RED}❌ Redis failed to start${NC}"
    exit 1
fi

# Create data directories
mkdir -p data/minio

# Start services in background
echo ""
echo "🚀 Starting services..."

# Start FraudLens API
echo "   Starting FraudLens API on port 8000..."
cd fraudlens
python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 > ../logs/fraudlens.log 2>&1 &
FRAUDLENS_PID=$!
cd ..

sleep 3

# Check if API started
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo -e "   ${GREEN}✓${NC} FraudLens API running (PID: $FRAUDLENS_PID)"
else
    echo -e "   ${RED}✗${NC} FraudLens API failed to start"
    echo "   Check logs/fraudlens.log for errors"
    kill $FRAUDLENS_PID 2>/dev/null
    exit 1
fi

# Start MinIO (if available)
if command -v minio &> /dev/null; then
    echo "   Starting MinIO on port 9000..."
    MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin \
        minio server data/minio --console-address ":9001" > logs/minio.log 2>&1 &
    MINIO_PID=$!
    echo -e "   ${GREEN}✓${NC} MinIO running (PID: $MINIO_PID)"
else
    echo -e "   ${YELLOW}⚠${NC} MinIO not installed (S3 storage will fail)"
    echo "   Install: brew install minio/stable/minio"
fi

# Start RQ Workers
echo "   Starting RQ Workers (3 instances)..."
cd truthsnap-bot
for i in {1..3}; do
    rq worker high default low --url redis://localhost:6379/0 > ../logs/worker-$i.log 2>&1 &
    WORKER_PIDS[$i]=$!
done
cd ..
echo -e "   ${GREEN}✓${NC} Workers running"

# Start Telegram Bot
echo "   Starting Telegram Bot..."
cd truthsnap-bot
python3 -m app.bot.main > ../logs/bot.log 2>&1 &
BOT_PID=$!
cd ..

sleep 2

if ps -p $BOT_PID > /dev/null; then
    echo -e "   ${GREEN}✓${NC} Bot running (PID: $BOT_PID)"
else
    echo -e "   ${RED}✗${NC} Bot failed to start"
    echo "   Check logs/bot.log for errors"
    exit 1
fi

# Save PIDs
mkdir -p .pids
echo $FRAUDLENS_PID > .pids/fraudlens.pid
echo $BOT_PID > .pids/bot.pid
echo $MINIO_PID > .pids/minio.pid
for i in {1..3}; do
    echo ${WORKER_PIDS[$i]} > .pids/worker-$i.pid
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ TruthSnap Bot Started Successfully!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Services:"
echo "   • FraudLens API: http://localhost:8000"
echo "   • MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo "   • Redis: localhost:6379"
echo "   • Bot: Running in background"
echo "   • Workers: 3 instances running"
echo ""
echo "📝 Logs:"
echo "   • Bot:      tail -f logs/bot.log"
echo "   • API:      tail -f logs/fraudlens.log"
echo "   • Workers:  tail -f logs/worker-*.log"
echo ""
echo "🛑 To stop:"
echo "   ./stop_local.sh"
echo ""
echo "🧪 Test your bot in Telegram now!"
echo ""
