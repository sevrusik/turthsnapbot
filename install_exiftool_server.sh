#!/bin/bash
# Install ExifTool and PyExifTool on TruthSnap Server
# Run as root: bash install_exiftool_server.sh

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════"
echo "🔧 Installing ExifTool for TruthSnap Bot"
echo "════════════════════════════════════════════════════════════"

# 1. Install system dependencies
echo ""
echo "1️⃣ Installing system packages..."
apt update
apt install -y python3-pip exiftool

# Verify exiftool CLI installed
echo ""
echo "✅ ExifTool CLI version:"
exiftool -ver

# 2. Find and activate venv
echo ""
echo "2️⃣ Looking for virtual environment..."

VENV_PATH=""
if [ -d "/opt/truthsnap-ecosystem/bot/venv" ]; then
    VENV_PATH="/opt/truthsnap-ecosystem/bot/venv"
elif [ -d "/opt/truthsnap-ecosystem/venv" ]; then
    VENV_PATH="/opt/truthsnap-ecosystem/venv"
elif [ -d "/opt/truthsnap-ecosystem/fraudlens/venv" ]; then
    VENV_PATH="/opt/truthsnap-ecosystem/fraudlens/venv"
fi

if [ -z "$VENV_PATH" ]; then
    echo "❌ No virtual environment found!"
    echo "Installing PyExifTool globally..."
    pip3 install PyExifTool==0.5.6
else
    echo "✅ Found venv: $VENV_PATH"
    echo ""
    echo "3️⃣ Installing PyExifTool in venv..."
    $VENV_PATH/bin/pip install PyExifTool==0.5.6

    echo ""
    echo "✅ Installed packages:"
    $VENV_PATH/bin/pip list | grep -i exif

    echo ""
    echo "4️⃣ Testing PyExifTool import..."
    $VENV_PATH/bin/python3 -c "from exiftool import ExifToolHelper; print('✅ Import successful')"
fi

# 3. Restart services
echo ""
echo "5️⃣ Restarting services..."

if systemctl is-active --quiet fraudlens; then
    echo "Restarting fraudlens..."
    systemctl restart fraudlens
    sleep 2
    systemctl status fraudlens --no-pager -l | head -10
fi

if systemctl is-active --quiet truthsnap-bot; then
    echo "Restarting truthsnap-bot..."
    systemctl restart truthsnap-bot
    sleep 2
    systemctl status truthsnap-bot --no-pager -l | head -10
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Installation Complete!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "1. Send a document (not photo) to bot"
echo "2. Check logs: journalctl -u fraudlens -f | grep -i exif"
echo ""
