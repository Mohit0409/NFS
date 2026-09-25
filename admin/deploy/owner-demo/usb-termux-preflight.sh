#!/data/data/com.termux/files/usr/bin/bash
set -u

REPORT="${1:-/sdcard/Download/need-for-strength-owner-demo-preflight.txt}"
EXPECTED_USER="u0_a304"
EXPECTED_MODEL="23124RN87I"
NGROK_API="http://127.0.0.1:4040/api/tunnels"
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

port_busy() {
  python3 - "$1" <<'PY'
import socket
import sys
port = int(sys.argv[1])
sock = socket.socket()
sock.settimeout(0.5)
try:
    busy = sock.connect_ex(("127.0.0.1", port)) == 0
finally:
    sock.close()
raise SystemExit(0 if busy else 1)
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

  [ "$(whoami)" = "$EXPECTED_USER" ] || add_blocker wrong_termux_user
  [ "$(getprop ro.product.model 2>/dev/null || true)" = "$EXPECTED_MODEL" ] || add_blocker wrong_device_model

  free_kb="$(df -Pk "$HOME" 2>/dev/null | awk 'NR==2 {print $4}')"
  value freeKb "${free_kb:-0}"
  case "${free_kb:-}" in
    ''|*[!0-9]*) add_blocker storage_unknown ;;
    *) [ "$free_kb" -ge 524288 ] || add_blocker low_storage ;;
  esac

  for cmd in python3 curl tar git ngrok; do
    if command -v "$cmd" >/dev/null 2>&1; then
      value "command_$cmd" "$(command -v "$cmd")"
    else
      value "command_$cmd" missing
      add_blocker "missing_$cmd"
    fi
  done

  if python3 -m venv --help >/dev/null 2>&1; then
    value pythonVenv ok
  else
    value pythonVenv missing
    add_blocker python_venv_unavailable
  fi

  if curl -fsS --max-time 6 https://pypi.org/simple/pip/ >/dev/null 2>&1; then
    value pythonPackageIndex reachable
  else
    value pythonPackageIndex unreachable
    add_blocker python_package_index_unreachable
  fi

  tunnel_json=""
  if tunnel_json="$(curl -fsS --max-time 4 "$NGROK_API" 2>/dev/null)"; then
    value ngrokAgentApi ok
    tunnel_summary="$(printf '%s' "$tunnel_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(",".join(f"{t.get("name","")}:{(t.get("config") or {}).get("addr","")}" for t in d.get("tunnels",[])))' 2>/dev/null || true)"
    value ngrokTunnels "$tunnel_summary"
    owner_demo_addr="$(printf '%s' "$tunnel_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next(((t.get("config") or {}).get("addr","") for t in d.get("tunnels",[]) if t.get("name")=="nfs-owner-demo"),""))' 2>/dev/null || true)"
    if [ -n "$owner_demo_addr" ] && [ "$owner_demo_addr" != "http://127.0.0.1:8900" ]; then
      value ownerDemoTunnelConflict "$owner_demo_addr"
      add_blocker owner_demo_tunnel_conflict
    fi
  else
    value ngrokAgentApi unavailable
    value ngrokTunnels ""
    add_blocker ngrok_agent_api_unavailable
  fi

  service_root="${PREFIX:-/data/data/com.termux/files/usr}/var/service"
  value serviceRoot "$service_root"
  value existingServices "$(ls -1 "$service_root" 2>/dev/null | tr '\n' ',' | sed 's/,$//')"

  for port in 8897 8898 8899 8900; do
    if port_busy "$port"; then
      state=busy
      add_blocker "port_${port}_busy"
    else
      state=free
    fi
    value "port_$port" "$state"
  done

  app_root="$HOME/apps/need-for-strength-owner-demo"
  value appRoot "$app_root"
  if [ -e "$app_root" ]; then
    unmanaged_release="$(find "$app_root" -mindepth 1 -maxdepth 1 -type d ! -exec test -f '{}/.nfs-owner-demo-release' ';' -print -quit 2>/dev/null || true)"
    if [ -n "$unmanaged_release" ]; then
      value unmanagedAppRelease "$unmanaged_release"
      add_blocker unmanaged_app_release
    fi
  fi

  value ready "$READY"
  value blockers "$BLOCKERS"
} > "$REPORT"

cat "$REPORT"
[ "$READY" = true ]
