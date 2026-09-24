#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

INSTALL_PACKAGES=false
ENABLE_TUNNEL=false
while [ "$#" -gt 0 ]; do
  case "$1" in
    --install-packages) INSTALL_PACKAGES=true ;;
    --enable-tunnel) ENABLE_TUNNEL=true ;;
    *) echo "usage: install-termux.sh [--install-packages] [--enable-tunnel]" >&2; exit 2 ;;
  esac
  shift
done

case "${PREFIX:-}" in
  /data/data/com.termux/files/usr) ;;
  *) echo "This installer must run inside the official Termux environment." >&2; exit 1 ;;
esac

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$REPO/.." && pwd)"
CONFIG_DIR="$HOME/.config/new-gym"
CONFIG="$CONFIG_DIR/new-gym.env"
STATE="$HOME/.local/state/new-gym"
DATA="$HOME/.local/share/new-gym"
SERVICE_ROOT="$PREFIX/var/service"

if $INSTALL_PACKAGES; then
  pkg update
  pkg install -y python python-cryptography git termux-services curl rclone cloudflared iproute2 clang rust libffi openssl
fi
for command in python3 git curl ss sv svlogd; do
  command -v "$command" >/dev/null 2>&1 || { echo "Missing command: $command" >&2; exit 1; }
done

mkdir -p "$CONFIG_DIR" "$STATE/logs" "$DATA/data" "$DATA/backups" "$HOME/.termux/boot" "$SERVICE_ROOT"
chmod 700 "$CONFIG_DIR" "$STATE" "$STATE/logs" "$DATA" "$DATA/data" "$DATA/backups"
printf '%s\n' "$REPO" > "$CONFIG_DIR/repository"
chmod 600 "$CONFIG_DIR/repository"

if [ ! -e "$CONFIG" ]; then
  cp "$REPO/deploy/new-gym-termux/new-gym.env.example" "$CONFIG"
  chmod 600 "$CONFIG"
  echo "Created $CONFIG. Fill the verified New Gym values, then rerun this installer."
  exit 2
fi
chmod 600 "$CONFIG"

python3 "$REPO/deploy/new-gym-termux/preflight-new-gym.py" --config "$CONFIG" --stage install

python3 "$REPO/scripts/gravity-env.py" --config "$CONFIG" -- python3 -c '
import os
from urllib.parse import urlparse

if os.environ.get("GRAVITY_HOST", "127.0.0.1") != "127.0.0.1":
    raise SystemExit("GRAVITY_HOST must be 127.0.0.1")
if urlparse(os.environ.get("APP_BASE_URL", "")).scheme != "https":
    raise SystemExit("APP_BASE_URL must be the private HTTPS admin URL")
if len(os.environ.get("SECRET_KEY", "")) < 32:
    raise SystemExit("SECRET_KEY must contain at least 32 characters")
ports = [
    int(os.environ.get("GRAVITY_PORT", "8897")),
    int(os.environ.get("NEW_GYM_MEMBER_GATEWAY_PORT", "8898")),
    int(os.environ.get("NEW_GYM_PUBLIC_PORT", "8899")),
]
if any(port < 1024 or port > 65535 for port in ports) or len(set(ports)) != 3:
    raise SystemExit("Admin, member and public ports must be distinct valid high ports")
'

DEFAULT_PYTHON="$REPO/.venv/bin/python"
PYTHON="$(python3 "$REPO/scripts/gravity-env.py" --config "$CONFIG" --print GRAVITY_PYTHON)"
PYTHON="${PYTHON:-$DEFAULT_PYTHON}"
if [ ! -x "$PYTHON" ]; then
  if [ "$PYTHON" != "$DEFAULT_PYTHON" ]; then
    echo "Configured GRAVITY_PYTHON does not exist: $PYTHON" >&2
    exit 1
  fi
  NEW_GYM_VENV="$REPO/.venv" bash "$REPO/deploy/new-gym-termux/prepare-python-runtime.sh"
fi
[ -x "$PYTHON" ] || { echo "New Gym Python runtime preparation failed: $PYTHON" >&2; exit 1; }
[ -d "$PROJECT_ROOT/customer-website/web" ] || { echo "Customer website is missing." >&2; exit 1; }
[ -r "$PROJECT_ROOT/customer-website/gateway/member_gateway.py" ] || { echo "Member gateway is missing." >&2; exit 1; }

install_service() {
  name=$1
  source=$2
  target="$SERVICE_ROOT/$name"
  if [ -e "$target" ] && [ ! -f "$target/.new-gym-managed" ]; then
    echo "Refusing to replace existing service: $target" >&2
    exit 1
  fi
  mkdir -p "$target/log"
  cp "$source/run" "$target/run"
  cp "$source/log/run" "$target/log/run"
  chmod 700 "$target/run" "$target/log/run"
  touch "$target/.new-gym-managed"
}

for name in new-gym-admin new-gym-member new-gym-web new-gym-health new-gym-notifications new-gym-tunnel; do
  install_service "$name" "$REPO/deploy/new-gym-termux/services/$name"
done

BOOT_SOURCE="$REPO/deploy/new-gym-termux/termux-boot-new-gym.sh"
BOOT_TARGET="$HOME/.termux/boot/new-gym-platform"
if [ -e "$BOOT_TARGET" ]; then
  cmp -s "$BOOT_SOURCE" "$BOOT_TARGET" || { echo "Refusing to replace existing boot script: $BOOT_TARGET" >&2; exit 1; }
else
  cp "$BOOT_SOURCE" "$BOOT_TARGET"
fi
chmod 700 "$BOOT_TARGET"

source "$PREFIX/etc/profile.d/start-services.sh"
sv-enable new-gym-admin
sv-enable new-gym-member
sv-enable new-gym-web
sv-enable new-gym-health
sv-enable new-gym-notifications

if $ENABLE_TUNNEL; then
  command -v cloudflared >/dev/null 2>&1 || { echo "cloudflared is required for --enable-tunnel." >&2; exit 1; }
  [ -s "$CONFIG_DIR/cloudflared-token" ] || { echo "Create the mode-600 Cloudflare token first." >&2; exit 1; }
  chmod 600 "$CONFIG_DIR/cloudflared-token"
  python3 "$REPO/deploy/new-gym-termux/preflight-new-gym.py" --config "$CONFIG" --stage launch
  touch "$CONFIG_DIR/enable-tunnel"
  chmod 600 "$CONFIG_DIR/enable-tunnel"
  sv-enable new-gym-tunnel
else
  sv-disable new-gym-tunnel >/dev/null 2>&1 || true
fi

echo "New Gym Termux services installed."
echo "Start locally first:"
echo "  sv up new-gym-admin new-gym-member new-gym-web new-gym-health new-gym-notifications"
echo "Verify:"
echo "  curl -fsS http://127.0.0.1:8897/api/health"
echo "  curl -fsS http://127.0.0.1:8898/api/health"
echo "  curl -I http://127.0.0.1:8899/"
echo "Enable Cloudflare only after all three are healthy."
