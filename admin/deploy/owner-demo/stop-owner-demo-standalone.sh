#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

STATE="$HOME/.local/state/need-for-strength-owner-demo"
PIDS="$STATE/pids"
APP_ROOT="$HOME/apps/need-for-strength-owner-demo"
TUNNEL_UPSTREAM="http://127.0.0.1:8900"

stop_pid_if_owned() {
  pid="$1"
  marker="$2"
  label="$3"

  case "$pid" in
    ''|*[!0-9]*) echo "Invalid owner-demo PID for $label: $pid" >&2; return 1 ;;
  esac

  kill -0 "$pid" 2>/dev/null || return 0

  cmdline="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
  cwd="$(readlink "/proc/$pid/cwd" 2>/dev/null || true)"
  owned_path=false
  case "$cmdline" in *"$APP_ROOT/"*) owned_path=true ;; esac
  case "$cwd" in "$APP_ROOT"/*) owned_path=true ;; esac
  if [ "$owned_path" != true ]; then
    echo "Refusing to kill PID $pid for $label: neither command line nor working directory is inside the Need For Strength owner-demo app root." >&2
    return 1
  fi
  case "$cmdline" in
    *"$marker"*) ;;
    *)
      echo "Refusing to kill PID $pid for $label: command line does not contain expected marker '$marker'." >&2
      return 1
      ;;
  esac

  kill "$pid"
  for _ in $(seq 1 40); do
    kill -0 "$pid" 2>/dev/null || return 0
    sleep 0.25
  done

  echo "Owner-demo process $label (PID $pid) did not stop cleanly." >&2
  return 1
}

stop_owned_pid_file() {
  name="$1"
  marker="$2"
  file="$PIDS/$name.pid"
  [ -f "$file" ] || return 0

  pid="$(cat "$file" 2>/dev/null || true)"
  stop_pid_if_owned "$pid" "$marker" "$name"
  rm -f "$file"
}

stop_tunnel_if_owned() {
  file="$PIDS/tunnel.pid"
  [ -f "$file" ] || return 0
  pid="$(cat "$file" 2>/dev/null || true)"
  case "$pid" in
    ''|*[!0-9]*) echo "Invalid owner-demo tunnel PID: $pid" >&2; return 1 ;;
  esac
  if kill -0 "$pid" 2>/dev/null; then
    cmdline="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
    case "$cmdline" in
      *cloudflared*"tunnel --url $TUNNEL_UPSTREAM"*) ;;
      *) echo "Refusing to kill PID $pid: not the Need For Strength Cloudflare Quick Tunnel." >&2; return 1 ;;
    esac
    kill "$pid"
    for _ in $(seq 1 40); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.25
    done
    kill -0 "$pid" 2>/dev/null && { echo "Owner-demo tunnel PID $pid did not stop cleanly." >&2; return 1; }
  fi
  rm -f "$file"
}

stop_orphaned_components() {
  for proc in /proc/[0-9]*; do
    [ -r "$proc/cmdline" ] || continue
    pid="${proc##*/}"
    [ "$pid" = "$$" ] && continue

    cmdline="$(tr '\0' ' ' < "$proc/cmdline" 2>/dev/null || true)"
    case "$cmdline" in
      *"$APP_ROOT/"*"member_gateway.py"*)
        stop_pid_if_owned "$pid" "member_gateway.py" "orphan member gateway"
        ;;
      *"$APP_ROOT/"*"demo-edge.py"*)
        stop_pid_if_owned "$pid" "demo-edge.py" "orphan demo edge"
        ;;
      *"$APP_ROOT/"*"http.server 8899"*)
        stop_pid_if_owned "$pid" "http.server 8899" "orphan customer web"
        ;;
      *"$APP_ROOT/"*"server.gravity"*)
        stop_pid_if_owned "$pid" "server.gravity" "orphan admin backend"
        ;;
      *cloudflared*"tunnel --url $TUNNEL_UPSTREAM"*)
        kill "$pid"
        for _ in $(seq 1 40); do
          kill -0 "$pid" 2>/dev/null || break
          sleep 0.25
        done
        kill -0 "$pid" 2>/dev/null && { echo "Orphan owner-demo Cloudflare tunnel PID $pid did not stop." >&2; return 1; }
        ;;
    esac
  done
}

stop_owned_pid_file member member_gateway.py
stop_owned_pid_file admin server.gravity
stop_owned_pid_file edge demo-edge.py
stop_owned_pid_file web "http.server 8899"
stop_tunnel_if_owned

# A previous failed restart can lose PID-file bookkeeping while leaving a child
# process alive. Recover only processes whose command line proves they belong
# to the dedicated Need For Strength owner-demo app tree.
stop_orphaned_components

echo "Need For Strength standalone owner demo stopped."
echo "Existing non-demo services/tunnels and demo database/config were preserved."
