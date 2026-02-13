#!/bin/bash
# Update server code and restart containers

set -e

echo "════════════════════════════════════════════════════════════"
echo "🔄 Updating TruthSnap Server Code"
echo "════════════════════════════════════════════════════════════"

# Find correct directory
if [ -d "/opt/truthsnap-ecosystem/api" ]; then
    cd /opt/truthsnap-ecosystem/api
elif [ -d "/opt/truthsnap-ecosystem" ]; then
    cd /opt/truthsnap-ecosystem
else
    echo "❌ Cannot find project directory!"
    exit 1
fi

echo "Working directory: $(pwd)"

echo ""
echo "1️⃣ Current git status:"
git log --oneline -3

echo ""
echo "2️⃣ Fetching latest code from GitHub..."
git fetch origin main

echo ""
echo "3️⃣ Pulling changes..."
git pull origin main

echo ""
echo "4️⃣ New git status:"
git log --oneline -3
echo ""
echo "Latest commit should be: 714e4ee - Add comprehensive logging for EXIF"

echo ""
echo "5️⃣ Verify code updated on host:"
if grep -q "🔧 Starting exiftool" fraudlens/backend/integrations/metadata_validator.py; then
    echo "✅ NEW code on host"
else
    echo "❌ OLD code on host - something went wrong!"
    exit 1
fi

echo ""
echo "6️⃣ Install PyExifTool in backend_api container..."
docker-compose exec -T backend_api pip install PyExifTool==0.5.6 || echo "⚠️  Install failed - maybe already installed"

echo ""
echo "7️⃣ Install exiftool CLI..."
docker-compose exec -T backend_api bash -c "apt update && apt install -y exiftool" || echo "⚠️  Install failed"

echo ""
echo "8️⃣ Verify installations:"
docker-compose exec -T backend_api python3 -c "from exiftool import ExifToolHelper; print('✅ PyExifTool OK')" || echo "❌ PyExifTool failed"
docker-compose exec -T backend_api exiftool -ver || echo "❌ exiftool CLI failed"

echo ""
echo "9️⃣ Restarting backend_api..."
docker-compose restart backend_api

echo ""
echo "🔟 Waiting for startup..."
sleep 3

echo ""
echo "1️⃣1️⃣ Checking container status:"
docker-compose ps backend_api

echo ""
echo "1️⃣2️⃣ Verify code in container:"
if docker-compose exec -T backend_api grep -q "🔧 Starting exiftool" /app/backend/integrations/metadata_validator.py; then
    echo "✅ NEW code in container"
else
    echo "❌ OLD code in container - need rebuild!"
    echo "Run: docker-compose build backend_api && docker-compose up -d backend_api"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Update Complete!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 Next steps:"
echo "1. Send a DOCUMENT (not photo) to the bot"
echo "2. Watch logs: docker-compose logs -f backend_api | grep Validator"
echo ""
echo "Expected logs:"
echo "  [Validator] 🔍 Starting validation | telegram_mode=False"
echo "  [Validator] PIL extracted X basic EXIF fields"
echo "  [Validator] 🔧 Starting exiftool extraction"
echo "  [Validator] ✅ ExifToolHelper imported successfully"
echo "  [Validator] exiftool extracted Y detailed fields"
echo ""
