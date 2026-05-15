#!/data/data/com.termux/files/usr/bin/bash
# One-time setup. Run this once after installing Termux.

set -e

echo "=== Updating packages ==="
pkg update -y && pkg upgrade -y

echo "=== Installing Python ==="
pkg install python -y

echo "=== Installing Python dependencies ==="
pip install flask requests python-dotenv

echo ""
echo "=== Done! Next steps: ==="
echo ""
echo "1. Copy and edit your config:"
echo "   cp .env.example .env && nano .env"
echo ""
echo "2. Generate a random API key and paste it into .env:"
echo "   python3 -c \"import secrets; print(secrets.token_urlsafe(24))\""
echo ""
echo "3. Start the server:"
echo "   bash start.sh"
echo ""
echo "4. (Optional) Auto-start on boot — install Termux:Boot from F-Droid, then:"
echo "   bash install-boot.sh"
