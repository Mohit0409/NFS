#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

STATE="$HOME/.local/state/need-for-strength-owner-demo"
PIDS="$STATE/pids"
NGROK_API="http://127.0.0.1:4040/api/tunnels"
TUNNEL_NAME="nfs-owner-demo"

stop_owned() {
  name="$1"
  marker="$2"
  file="$PIDS/$name.pid"
  [ -f "$file" ] || return 0
  pid="$(cat "$file" 2>/dev/null || true)"
  case "$pid" in
    ''|*[!0-9]*) echo "Invalid owner-demo PID file: $file" >&2; return 1 ;;
  esac
  if kill -0 "$pid" 2>/dev/null; then
    cmdline="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
    case "$cmdline" in
      *"$marker"*)
        kill "$pid"
        for _ in $(seq 1 20); do
          kill -0 "$pid" 2>/dev/null || break
          sleep 0.25
        done
        if kill -0 "$pid" 2>/dev/null; then
          echo "Owner-demo process $name did not stop cleanly." >&2
          return 1
        fi
        ;;
      *)
        echo "Refusing to kill PID $pid: command line does not match owner-demo marker '$marker'." >&2
        return 1
        ;;
    esac
  fi
  rm -f "$file"
}

stop_owned member member_gateway.py
stop_owned admin server.gravity
stop_owned edge demo-edge.py
stop_owned web http.server

if curl -fsS --max-time 3 "$NGROK_API" >/dev/null 2>&1; then
  curl -fsS -X DELETE "$NGROK_API/$TUNNEL_NAME" >/dev/null 2>&1 || true
fi

echo "Need For Strength standalone owner demo stopped."
echo "Existing non-demo ngrok tunnels and demo database/config were preserved."
