#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

case "${PREFIX:-}" in
  /data/data/com.termux/files/usr) ;;
  *) echo "This owner-demo installer must run inside Termux." >&2; exit 1 ;;
esac

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$REPO/.." && pwd)"
PROFILE="$REPO/deploy/owner-demo"
CONFIG_DIR="$HOME/.config/need-for-strength-owner-demo"
CONFIG="$CONFIG_DIR/demo.env"
STATE="$HOME/.local/state/need-for-strength-owner-demo"
DATA="$HOME/.local/share/need-for-strength-owner-demo"
PIDS="$STATE/pids"
LOGS="$STATE/logs"
TUNNEL_NAME="nfs-owner-demo"
NGROK_API="http://127.0.0.1:4040/api/tunnels"

mkdir -p "$CONFIG_DIR" "$STATE" "$DATA" "$PIDS" "$LOGS"
chmod 700 "$CONFIG_DIR" "$STATE" "$DATA" "$PIDS" "$LOGS"
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

if ! curl -fsS --max-time 3 "$NGROK_API" >/dev/null 2>&1; then
  echo "Existing ngrok Agent API is not reachable on 127.0.0.1:4040." >&2
  exit 1
fi

OWNER_DEMO_VENV="$REPO/.venv" bash "$PROFILE/prepare-owner-demo-runtime.sh"
PYTHON="$(python3 "$REPO/scripts/gravity-env.py" --config "$CONFIG" --print GRAVITY_PYTHON)"
PYTHON="${PYTHON:-$REPO/.venv/bin/python}"
[ -x "$PYTHON" ] || { echo "Python runtime is missing: $PYTHON" >&2; exit 1; }

cd "$REPO"
"$PYTHON" "$PROFILE/seed-owner-demo.py" --config "$CONFIG"

pid_file() { printf '%s/%s.pid' "$PIDS" "$1"; }

assert_owned_pid() {
  name="$1"
  marker="$2"
  file="$(pid_file "$name")"
  [ -f "$file" ] || return 1
  pid="$(cat "$file" 2>/dev/null || true)"
  case "$pid" in ''|*[!0-9]*) return 1 ;; esac
  kill -0 "$pid" 2>/dev/null || return 1
  cmdline="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
  case "$cmdline" in
    *"$marker"*) return 0 ;;
    *) echo "PID $pid for $name does not match owner-demo marker $marker." >&2; return 2 ;;
  esac
}

ensure_stopped() {
  name="$1"
  marker="$2"
  file="$(pid_file "$name")"
  [ -f "$file" ] || return 0
  if assert_owned_pid "$name" "$marker"; then
    pid="$(cat "$file")"
    kill "$pid"
    for _ in $(seq 1 20); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.25
    done
    if kill -0 "$pid" 2>/dev/null; then
      echo "Owner-demo process $name did not stop cleanly." >&2
      exit 1
    fi
  else
    rc=$?
    if [ "$rc" -eq 2 ]; then exit 1; fi
  fi
  rm -f "$file"
}

ensure_stopped admin server.gravity
ensure_stopped member member_gateway.py
ensure_stopped web http.server
ensure_stopped edge demo-edge.py

# Reuse the already-running ngrok agent without touching any non-demo tunnel.
# An existing owner-demo tunnel is replaceable only when it already targets our edge port.
current_tunnels="$(curl -fsS "$NGROK_API")"
owner_demo_addr="$(printf '%s' "$current_tunnels" | "$PYTHON" -c 'import json,sys; d=json.load(sys.stdin); print(next(((t.get("config") or {}).get("addr","") for t in d.get("tunnels",[]) if t.get("name")=="nfs-owner-demo"),""))')"
if [ -n "$owner_demo_addr" ] && [ "$owner_demo_addr" != "http://127.0.0.1:8900" ]; then
  echo "Refusing to replace ngrok tunnel $TUNNEL_NAME because it targets $owner_demo_addr." >&2
  exit 1
fi
if [ -n "$owner_demo_addr" ]; then
  curl -fsS -X DELETE "$NGROK_API/$TUNNEL_NAME" >/dev/null
fi

start_component() {
  name="$1"
  marker="$2"
  shift 2
  log="$LOGS/$name.log"
  "$@" >>"$log" 2>&1 < /dev/null &
  pid=$!
  printf '%s\n' "$pid" > "$(pid_file "$name")"
  sleep 0.4
  if ! assert_owned_pid "$name" "$marker"; then
    echo "Owner-demo component $name failed to start. See $log" >&2
    exit 1
  fi
}

start_component admin server.gravity   python3 "$REPO/scripts/gravity-env.py" --config "$CONFIG" -- "$PYTHON" -m server.gravity

start_component member member_gateway.py   python3 "$REPO/scripts/gravity-env.py" --config "$CONFIG" -- "$PYTHON" "$PROJECT_ROOT/customer-website/gateway/member_gateway.py"

PUBLIC_PORT="$(python3 "$REPO/scripts/gravity-env.py" --config "$CONFIG" --print NEW_GYM_PUBLIC_PORT)"
PUBLIC_PORT="${PUBLIC_PORT:-8899}"
start_component web http.server   "$PYTHON" -m http.server "$PUBLIC_PORT" --bind 127.0.0.1 --directory "$PROJECT_ROOT/customer-website/web"

start_component edge demo-edge.py   python3 "$REPO/scripts/gravity-env.py" --config "$CONFIG" -- "$PYTHON" "$PROFILE/demo-edge.py"

wait_http() {
  url="$1"
  name="$2"
  for _ in $(seq 1 40); do
    if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then return 0; fi
    sleep 0.5
  done
  echo "$name did not become healthy: $url" >&2
  exit 1
}

wait_http "http://127.0.0.1:8897/api/health" "Admin backend"
wait_http "http://127.0.0.1:8898/api/health" "Member gateway"
wait_http "http://127.0.0.1:8899/" "Customer site"
wait_http "http://127.0.0.1:8900/" "Demo edge"

tunnel_json="$(curl -fsS -X POST "$NGROK_API"   -H 'Content-Type: application/json'   --data '{"name":"nfs-owner-demo","addr":"http://127.0.0.1:8900","proto":"http","inspect":true}')"

public_url="$(printf '%s' "$tunnel_json" | "$PYTHON" -c 'import json,sys; d=json.load(sys.stdin); print(d.get("public_url",""))')"
case "$public_url" in
  https://*) ;;
  *) echo "ngrok Agent API did not return an HTTPS owner-demo URL." >&2; exit 1 ;;
esac

"$PYTHON" "$PROFILE/sync-ngrok-url.py" --config "$CONFIG" >/dev/null

ensure_stopped admin server.gravity
ensure_stopped member member_gateway.py
start_component admin server.gravity   python3 "$REPO/scripts/gravity-env.py" --config "$CONFIG" -- "$PYTHON" -m server.gravity
start_component member member_gateway.py   python3 "$REPO/scripts/gravity-env.py" --config "$CONFIG" -- "$PYTHON" "$PROJECT_ROOT/customer-website/gateway/member_gateway.py"

wait_http "http://127.0.0.1:8897/api/health" "Admin backend after ngrok origin sync"
wait_http "http://127.0.0.1:8900/" "Demo edge after ngrok origin sync"

curl -fsS --max-time 12 -H "ngrok-skip-browser-warning: 1" "$public_url/" >/dev/null
curl -fsS --max-time 12 -H "ngrok-skip-browser-warning: 1" "$public_url/api/health" >/dev/null

cat > "$STATE/owner-demo-url.txt" <<EOF
Customer site: $public_url/
Admin portal:  $public_url/admin
Commit: $(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo archive)
EOF
chmod 600 "$STATE/owner-demo-url.txt"

echo
echo "NEED FOR STRENGTH OWNER DEMO READY"
cat "$STATE/owner-demo-url.txt"
echo
echo "Existing Universal ngrok tunnel was not stopped or modified."
echo "Demo processes are standalone PID-managed processes under $STATE."
