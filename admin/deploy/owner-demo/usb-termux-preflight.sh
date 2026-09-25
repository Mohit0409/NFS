#!/data/data/com.termux/files/usr/bin/bash
set -u

REPORT="${1:-/sdcard/Download/need-for-strength-owner-demo-preflight.txt}"
EXPECTED_USER="u0_a304"
EXPECTED_MODEL="23124RN87I"
TMP_ROOT="${TMPDIR:-${PREFIX:-/data/data/com.termux/files/usr}/tmp}"
mkdir -p "$TMP_ROOT"
READY=true
BLOCKERS=""

add_blocker() {
  READY=false
  if [ -n "$BLOCKERS" ]; then
    BLOCKERS="$BLOCKERS,$1"
  else
    BLOCKERS="$1"
  fi
}

value() {
  printf '%s=%s\n' "$1" "$2"
}

port_state() {
  python3 - "$1" <<'PY'
import socket, sys
port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    sock.bind(("127.0.0.1", port))
except OSError:
    print("busy")
else:
    print("free")
finally:
    sock.close()
PY
}

{
  value checkedAt "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date)"
  value user "$(whoami)"
  value manufacturer "$(getprop ro.product.manufacturer 2>/dev/null || true)"
  value model "$(getprop ro.product.model 2>/dev/null || true)"
  value device "$(getprop ro.product.device 2>/dev/null || true)"
  value prefix "${PREFIX:-}"
  value home "$HOME"

  if [ "$(whoami)" != "$EXPECTED_USER" ]; then add_blocker wrong_termux_user; fi
  if [ "$(getprop ro.product.model 2>/dev/null || true)" != "$EXPECTED_MODEL" ]; then add_blocker wrong_device_model; fi

  free_kb="$(df -Pk "$HOME" 2>/dev/null | awk 'NR==2 {print $4}')"
  value freeKb "${free_kb:-0}"
  case "${free_kb:-}" in
    ''|*[!0-9]*) add_blocker storage_unknown ;;
    *) [ "$free_kb" -ge 524288 ] || add_blocker low_storage ;;
  esac

  for cmd in python3 curl tar git cloudflared; do
    if command -v "$cmd" >/dev/null 2>&1; then
      value "command_$cmd" "$(command -v "$cmd")"
    else
      value "command_$cmd" missing
      add_blocker "missing_$cmd"
    fi
  done

  if python3 -c 'import cryptography' >/dev/null 2>&1; then
    value pythonCryptography ok
  else
    value pythonCryptography missing
    add_blocker python_cryptography_unavailable
  fi

  value ownerDemoTunnelProvider "cloudflare-quick-tunnel"

  for port in 8897 8898 8899 8900; do
    state="$(port_state "$port")"
    value "port_$port" "$state"
    if [ "$state" != free ]; then
      add_blocker "port_${port}_busy"
    fi
  done

  state_root="$HOME/.local/state/need-for-strength-owner-demo"
  app_root="$HOME/apps/need-for-strength-owner-demo"
  value stateRoot "$state_root"
  value appRoot "$app_root"

  if [ -d "$state_root/pids" ] && find "$state_root/pids" -type f -name '*.pid' -print -quit 2>/dev/null | grep -q .; then
    value existingOwnerDemoPids yes
    add_blocker owner_demo_already_present
  else
    value existingOwnerDemoPids no
  fi

  if [ -d "$app_root" ] && find "$app_root" -mindepth 1 -maxdepth 1 -type d -print -quit 2>/dev/null | grep -q .; then
    value existingOwnerDemoApp yes
    add_blocker owner_demo_app_already_present
  else
    value existingOwnerDemoApp no
  fi

  service_root="${PREFIX:-/data/data/com.termux/files/usr}/var/service"
  value existingServices "$(ls -1 "$service_root" 2>/dev/null | tr '\n' ',' | sed 's/,$//')"

  value ready "$READY"
  value blockers "$BLOCKERS"
} > "$REPORT"

cat "$REPORT"
[ "$READY" = true ]
