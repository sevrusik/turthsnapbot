#!/bin/bash

# TruthSnap Bot - Setup Verification Script

echo "🔍 Verifying TruthSnap Bot Setup..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Check 1: Directory structure
echo "📁 Checking directory structure..."
REQUIRED_DIRS=(
    "fraudlens/backend/api/routes"
    "fraudlens/backend/integrations"
    "fraudlens/backend/core"
    "fraudlens/backend/models"
    "truthsnap-bot/app/bot/handlers"
    "truthsnap-bot/app/bot/middlewares"
    "truthsnap-bot/app/workers"
    "truthsnap-bot/app/services"
    "truthsnap-bot/app/database/repositories"
    "truthsnap-bot/migrations"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "  ${GREEN}✓${NC} $dir"
    else
        echo -e "  ${RED}✗${NC} $dir (missing)"
        ((ERRORS++))
    fi
done

# Check 2: Critical files
echo ""
echo "📄 Checking critical files..."
REQUIRED_FILES=(
    "fraudlens/backend/api/routes/consumer.py"
    "fraudlens/backend/integrations/watermark_detector.py"
    "fraudlens/backend/core/fraud_detector.py"
    "truthsnap-bot/app/bot/main.py"
    "truthsnap-bot/app/bot/handlers/photo.py"
    "truthsnap-bot/app/workers/tasks.py"
    "truthsnap-bot/app/services/fraudlens_client.py"
    "truthsnap-bot/app/services/queue.py"
    "docker-compose.yml"
    "README.md"
    ".env.example"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (missing)"
        ((ERRORS++))
    fi
done

# Check 3: Environment configuration
echo ""
echo "🔧 Checking environment configuration..."
if [ -f ".env" ]; then
    echo -e "  ${GREEN}✓${NC} .env file exists"

    if grep -q "TELEGRAM_BOT_TOKEN" .env; then
        if grep -q "TELEGRAM_BOT_TOKEN=your_bot_token_here" .env; then
            echo -e "  ${YELLOW}⚠${NC} TELEGRAM_BOT_TOKEN not configured (using placeholder)"
        else
            echo -e "  ${GREEN}✓${NC} TELEGRAM_BOT_TOKEN configured"
        fi
    else
        echo -e "  ${RED}✗${NC} TELEGRAM_BOT_TOKEN missing in .env"
        ((ERRORS++))
    fi
else
    echo -e "  ${YELLOW}⚠${NC} .env file not found (copy from .env.example)"
fi

# Check 4: Docker
echo ""
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Docker installed"

    if command -v docker-compose &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Docker Compose installed"
    else
        echo -e "  ${RED}✗${NC} Docker Compose not installed"
        ((ERRORS++))
    fi
else
    echo -e "  ${RED}✗${NC} Docker not installed"
    ((ERRORS++))
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Setup verification passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. cp .env.example .env"
    echo "  2. Edit .env and add your TELEGRAM_BOT_TOKEN"
    echo "  3. make start"
    echo "  4. Test your bot!"
else
    echo -e "${RED}❌ Setup verification failed with $ERRORS error(s)${NC}"
    echo ""
    echo "Please fix the errors above and run this script again."
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit $ERRORS
