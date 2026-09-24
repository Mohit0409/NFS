#!/data/data/com.termux/files/usr/bin/bash
set -u
LOG="$HOME/.local/state/new-gym/logs/boot.log"
mkdir -p "$(dirname "$LOG")"
exec >> "$LOG" 2>&1

echo "$(date -Iseconds) New Gym boot recovery requested"
termux-wake-lock || true
source "$PREFIX/etc/profile.d/start-services.sh"
sv up new-gym-admin new-gym-member new-gym-web new-gym-health new-gym-notifications || true
if [ -f "$HOME/.config/new-gym/enable-tunnel" ]; then
  sv up new-gym-tunnel || true
fi
echo "$(date -Iseconds) New Gym boot recovery completed"
