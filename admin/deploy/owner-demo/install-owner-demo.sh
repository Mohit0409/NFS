#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

case "${PREFIX:-}" in
  /data/data/com.termux/files/usr) ;;
  *) echo "This owner-demo installer must run inside Termux." >&2; exit 1 ;;
esac

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$REPO/.." && pwd)"
CONFIG_DIR="$HOME/.config/need-for-strength-owner-demo"
CONFIG="$CONFIG_DIR/demo.env"
STATE="$HOME/.local/state/need-for-strength-owner-demo"
DATA="$HOME/.local/share/need-for-strength-owner-demo"
SERVICE_ROOT="$PREFIX/var/service"
PROFILE="$REPO/deploy/owner-demo"

mkdir -p "$CONFIG_DIR" "$STATE" "$DATA" "$SERVICE_ROOT"
chmod 700 "$CONFIG_DIR" "$STATE" "$DATA"
printf '%s\n' "$REPO" > "$CONFIG_DIR/repository"
chmod 600 "$CONFIG_DIR/repository"

if [ ! -f "$CONFIG" ]; then
  cp "$PROFILE/owner-demo.env.example" "$CONFIG"
  python3 - "$CONFIG" "$REPO" "$DATA" "$STATE" <<'PY'
import secrets
import sys
from pathlib import Path

path = Path(sys.argv[1])
repo = sys.argv[2]
data = sys.argv[3]
state = sys.argv[4]
values = {
    "SECRET_KEY": secrets.token_urlsafe(48),
    "NEW_GYM_ADMIN_ROOT": repo,
    "NEW_GYM_MEMBER_DATABASE": f"{data}/data/gravity.sqlite3",
    "GRAVITY_DATA_DIR": f"{data}/data",
    "GRAVITY_BACKUP_DIR": f"{data}/backups",
    "GRAVITY_RUNTIME_DIR": state,
    "GRAVITY_LOG_DIR": f"{state}/logs",
}
lines = path.read_text(encoding="utf-8").splitlines()
out = []
for line in lines:
    key = line.split("=", 1)[0].strip() if "=" in line else ""
    out.append(f"{key}={values[key]}" if key in values else line)
path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
  chmod 600 "$CONFIG"
fi

if ! command -v sv >/dev/null 2>&1; then
  echo "termux-services is required. Run: pkg install termux-services" >&2
  exit 1
fi
if ! command -v ngrok >/dev/null 2>&1; then
  echo "ngrok is required for the owner demo. Install/configure ngrok first." >&2
  exit 1
fi
if ! ngrok config check >/dev/null 2>&1; then
  echo "ngrok is installed but not authenticated. Configure your ngrok authtoken, then rerun." >&2
  exit 1
fi

if [ ! -x "$REPO/.venv/bin/python" ]; then
  NEW_GYM_VENV="$REPO/.venv" bash "$REPO/deploy/new-gym-termux/prepare-python-runtime.sh"
fi
PYTHON="$(python3 "$REPO/scripts/gravity-env.py" --config "$CONFIG" --print GRAVITY_PYTHON)"
PYTHON="${PYTHON:-$REPO/.venv/bin/python}"
[ -x "$PYTHON" ] || { echo "Python runtime is missing: $PYTHON" >&2; exit 1; }

cd "$REPO"
"$PYTHON" "$PROFILE/seed-owner-demo.py" --config "$CONFIG"

install_service() {
  name="$1"
  source="$PROFILE/services/$name"
  target="$SERVICE_ROOT/$name"
  if [ -e "$target" ] && [ ! -f "$target/.nfs-owner-demo-managed" ]; then
    echo "Refusing to replace unmanaged service: $target" >&2
    exit 1
  fi
  rm -rf "$target"
  cp -R "$source" "$target"
  touch "$target/.nfs-owner-demo-managed"
  chmod +x "$target/run"
}

for service in nfs-demo-admin nfs-demo-member nfs-demo-web nfs-demo-edge nfs-demo-ngrok; do
  install_service "$service"
done

for service in nfs-demo-admin nfs-demo-member nfs-demo-web nfs-demo-edge; do
  sv-enable "$service" >/dev/null 2>&1 || true
  sv up "$service"
done

wait_http() {
  url="$1"
  name="$2"
  for _ in $(seq 1 30); do
    if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "$name did not become healthy: $url" >&2
  exit 1
}

wait_http "http://127.0.0.1:8897/api/health" "Admin backend"
wait_http "http://127.0.0.1:8898/api/health" "Member gateway"
wait_http "http://127.0.0.1:8899/" "Customer site"
wait_http "http://127.0.0.1:8900/" "Demo edge"

sv-enable nfs-demo-ngrok >/dev/null 2>&1 || true
sv up nfs-demo-ngrok
sync_json="$("$PYTHON" "$PROFILE/sync-ngrok-url.py" --config "$CONFIG")"
public_url="$(printf '%s' "$sync_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["publicUrl"])')"

sv restart nfs-demo-admin
sv restart nfs-demo-member
sleep 2
wait_http "http://127.0.0.1:8897/api/health" "Admin backend after ngrok origin sync"
wait_http "http://127.0.0.1:8900/" "Demo edge after origin sync"

if ! curl -fsS --max-time 10 -H "ngrok-skip-browser-warning: 1" "$public_url/" >/dev/null; then
  echo "ngrok tunnel exists but public customer smoke check failed." >&2
  exit 1
fi
if ! curl -fsS --max-time 10 -H "ngrok-skip-browser-warning: 1" "$public_url/api/health" >/dev/null; then
  echo "ngrok tunnel exists but public admin-health smoke check failed." >&2
  exit 1
fi

echo
echo "NEED FOR STRENGTH OWNER DEMO READY"
echo "Customer site: $public_url/"
echo "Admin portal:  $public_url/admin"
echo
echo "If the owner admin account has not been created yet, run:"
echo "  cd $REPO"
echo "  python3 $REPO/scripts/gravity-env.py --config $CONFIG -- $PYTHON -m server.gravity --bootstrap-owner owner-demo"
echo
echo "Demo-only values include pool hourly rates, kitchen menu/stock and opening hours."
echo "Production launch is intentionally blocked for this demo database."
