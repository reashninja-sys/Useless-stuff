#!/data/data/com.termux/files/usr/bin/bash
# Sets up auto-start via Termux:Boot.
# Requires: Termux:Boot installed from F-Droid and opened at least once.

BOOT_DIR="$HOME/.termux/boot"
SCRIPT="$BOOT_DIR/cupra-battery.sh"
HERE="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$BOOT_DIR"

cat > "$SCRIPT" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
# Auto-started by Termux:Boot on phone unlock/reboot
termux-wake-lock
cd "$HERE"
python3 server.py >> "$HERE/server.log" 2>&1 &
EOF

chmod +x "$SCRIPT"

echo "Boot script installed to $SCRIPT"
echo "The server will start automatically after your phone reboots."
echo "Logs will be written to: $HERE/server.log"
