#!/data/data/com.termux/files/usr/bin/bash
# Need For Strength production runtime.  It owns only NFS PID files, paths and ports.
set -euo pipefail
umask 077

APP_ROOT="$HOME/apps/need-for-strength-owner-demo"
CONFIG_DIR="$HOME/.config/need-for-strength-owner-demo"
CONFIG="$CONFIG_DIR/demo.env"
STATE="$HOME/.local/state/need-for-strength-owner-demo"
PIDS="$STATE/pids"
LOGS="$STATE/logs"
TUNNEL_STATE="$HOME/.local/state/nfs-named-tunnel"
TUNNEL_PID="$TUNNEL_STATE/tunnel.pid"
TUNNEL_CONFIG="$CONFIG_DIR/cloudflared-named.yml"
TUNNEL_NAME="nfs-nmh"

fail() { echo "NFS_RUNTIME=BLOCKED: $*" >&2; exit 1; }

repo_path() {
  [ -r "$CONFIG_DIR/repository" ] || fail "missing NFS repository pointer"
  REPO="$(cat "$CONFIG_DIR/repository")"
  case "$REPO" in "$APP_ROOT"/*/admin) ;; *) fail "repository pointer is outside the NFS release root" ;; esac
  RELEASE="${REPO%/admin}"
  COMMIT="${RELEASE##*/}"
  case "$COMMIT" in
    [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
    *) fail "invalid NFS release directory" ;;
  esac
  [ -r "$RELEASE/.nfs-owner-demo-release" ] || fail "release marker missing"
  [ "$(cat "$RELEASE/.nfs-owner-demo-release")" = "$COMMIT" ] || fail "release marker does not match directory"
  [ -r "$CONFIG" ] || fail "missing NFS configuration"
}

pid_is_owned() {
  local pid="$1" marker="$2" cmd cwd
  case "$pid" in ''|*[!0-9]*) return 1 ;; esac
  kill -0 "$pid" 2>/dev/null || return 1
  cmd="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
  cwd="$(readlink "/proc/$pid/cwd" 2>/dev/null || true)"
  case "$cmd" in *"$marker"*) ;; *) return 1 ;; esac
  case "$cmd:$cwd" in *"$APP_ROOT/"*) return 0 ;; *) return 1 ;; esac
}

stop_component() {
  local name="$1" marker="$2" file="$PIDS/$1.pid" pid i
  [ -f "$file" ] || return 0
  pid="$(cat "$file" 2>/dev/null || true)"
  if kill -0 "$pid" 2>/dev/null; then
    pid_is_owned "$pid" "$marker" || fail "refusing to stop unowned $name PID $pid"
    kill "$pid"
    for i in $(seq 1 40); do kill -0 "$pid" 2>/dev/null || break; sleep .25; done
    kill -0 "$pid" 2>/dev/null && fail "$name PID $pid did not stop cleanly"
  fi
  rm -f "$file"
}

port_is_free() {
  python3 - "$1" <<'PY'
import socket, sys
s = socket.socket()
try:
    s.bind(("127.0.0.1", int(sys.argv[1])))
except OSError:
    raise SystemExit(1)
finally:
    s.close()
PY
}

start_component() {
  local name="$1" marker="$2" run="$3" file="$PIDS/$1.pid" pid i
  port_is_free "$4" || fail "port $4 is occupied; refusing to replace an unknown service"
  nohup bash "$run" >>"$LOGS/$name.log" 2>&1 < /dev/null &
  pid=$!
  printf '%s\n' "$pid" > "$file"
  for i in $(seq 1 20); do
    pid_is_owned "$pid" "$marker" && return 0
    kill -0 "$pid" 2>/dev/null || fail "$name exited during startup"
    sleep .25
  done
  fail "$name did not start from the active NFS release"
}

wait_http() {
  local url="$1" label="$2" i
  for i in $(seq 1 40); do curl -fsS --max-time 2 "$url" >/dev/null 2>&1 && return 0; sleep .5; done
  fail "$label did not become healthy"
}

named_tunnel_owned() {
  local pid="$1" cmd
  case "$pid" in ''|*[!0-9]*) return 1 ;; esac
  kill -0 "$pid" 2>/dev/null || return 1
  cmd="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
  case "$cmd" in *cloudflared*"--config $TUNNEL_CONFIG"*"tunnel run $TUNNEL_NAME"*) return 0 ;; *) return 1 ;; esac
}

ensure_named_tunnel() {
  local pid
  [ -r "$TUNNEL_CONFIG" ] || fail "missing named-tunnel configuration"
  cloudflared tunnel --config "$TUNNEL_CONFIG" ingress validate >/dev/null || fail "named-tunnel ingress is invalid"
  mkdir -p "$TUNNEL_STATE"
  chmod 700 "$TUNNEL_STATE"
  if [ -f "$TUNNEL_PID" ]; then
    pid="$(cat "$TUNNEL_PID" 2>/dev/null || true)"
    named_tunnel_owned "$pid" && return 0
    kill -0 "$pid" 2>/dev/null && fail "refusing to replace an unowned named-tunnel PID $pid"
    rm -f "$TUNNEL_PID"
  fi
  nohup cloudflared --config "$TUNNEL_CONFIG" tunnel run "$TUNNEL_NAME" >>"$LOGS/named-tunnel.log" 2>&1 < /dev/null &
  pid=$!
  printf '%s\n' "$pid" > "$TUNNEL_PID"
  sleep 1
  named_tunnel_owned "$pid" || fail "named tunnel did not start"
}

components_are_active_release() {
  local name marker pid cwd
  for name in admin member web edge; do
    case "$name" in admin) marker=server.gravity ;; member) marker=member_gateway.py ;; web) marker=http.server ;; edge) marker=demo-edge.py ;; esac
    [ -r "$PIDS/$name.pid" ] || return 1
    pid="$(cat "$PIDS/$name.pid")"
    pid_is_owned "$pid" "$marker" || return 1
    cwd="$(readlink "/proc/$pid/cwd" 2>/dev/null || true)"
    case "$cwd" in "$RELEASE"/*) ;; *) return 1 ;; esac
  done
}

start_all() {
  mkdir -p "$PIDS" "$LOGS"
  chmod 700 "$PIDS" "$LOGS"
  start_component admin server.gravity "$REPO/deploy/owner-demo/services/nfs-demo-admin/run" 8897
  wait_http http://127.0.0.1:8897/api/health "admin backend"
  start_component member member_gateway.py "$REPO/deploy/owner-demo/services/nfs-demo-member/run" 8898
  wait_http http://127.0.0.1:8898/api/health "member gateway"
  start_component web http.server "$REPO/deploy/owner-demo/services/nfs-demo-web/run" 8899
  wait_http http://127.0.0.1:8899/ "customer web"
  start_component edge demo-edge.py "$REPO/deploy/owner-demo/services/nfs-demo-edge/run" 8900
  wait_http http://127.0.0.1:8900/api/health "edge"
  ensure_named_tunnel
}

repo_path
case "${1:-recover}" in
  stop)
    stop_component edge demo-edge.py; stop_component web http.server
    stop_component member member_gateway.py; stop_component admin server.gravity
    ;;
  restart)
    stop_component edge demo-edge.py; stop_component web http.server
    stop_component member member_gateway.py; stop_component admin server.gravity
    start_all
    ;;
  recover)
    if components_are_active_release; then
      wait_http http://127.0.0.1:8897/api/health "admin backend"
      wait_http http://127.0.0.1:8898/api/health "member gateway"
      wait_http http://127.0.0.1:8900/api/health "edge"
      ensure_named_tunnel
    else
      stop_component edge demo-edge.py; stop_component web http.server
      stop_component member member_gateway.py; stop_component admin server.gravity
      start_all
    fi
    ;;
  *) fail "usage: $0 [recover|restart|stop]" ;;
esac
