#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

ARCHIVE="${1:-/sdcard/Download/need-for-strength-owner-demo.tar.gz}"
HASH_FILE="${2:-/sdcard/Download/need-for-strength-owner-demo.sha256}"
COMMIT_FILE="${3:-/sdcard/Download/need-for-strength-owner-demo.commit}"
RESULT="${4:-/sdcard/Download/need-for-strength-owner-demo-result.txt}"
NGROK_API="http://127.0.0.1:4040/api/tunnels"
TMP_ROOT="${TMPDIR:-${PREFIX:-/data/data/com.termux/files/usr}/tmp}"
BEFORE_JSON="$TMP_ROOT/nfs-owner-demo-ngrok-before.json"
AFTER_JSON="$TMP_ROOT/nfs-owner-demo-ngrok-after.json"
EXPECTED_USER="u0_a304"
EXPECTED_MODEL="23124RN87I"

mkdir -p "$TMP_ROOT"

exec > >(tee "$RESULT") 2>&1

fail() {
  echo "OWNER_DEMO_BOOTSTRAP=BLOCKED"
  echo "Reason: $1"
  exit 1
}

wait_ngrok_api_to_file() {
  output="$1"
  temporary="$output.wait"
  rm -f "$temporary"
  for _ in $(seq 1 60); do
    if curl -fsS --max-time 2 "$NGROK_API" >"$temporary" 2>/dev/null &&
       python3 - "$temporary" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
raise SystemExit(0 if isinstance(data.get("tunnels", []), list) else 1)
PY
    then
      mv "$temporary" "$output"
      return 0
    fi
    sleep 1
  done
  rm -f "$temporary"
  return 1
}

[ "$(whoami)" = "$EXPECTED_USER" ] || fail "wrong Termux user"
[ "$(getprop ro.product.model 2>/dev/null || true)" = "$EXPECTED_MODEL" ] || fail "wrong Redmi model"

for cmd in python3 curl tar; do
  command -v "$cmd" >/dev/null 2>&1 || fail "missing command: $cmd"
done

[ -f "$ARCHIVE" ] || fail "archive missing from Downloads"
[ -f "$HASH_FILE" ] || fail "archive SHA-256 file missing from Downloads"
[ -f "$COMMIT_FILE" ] || fail "commit marker missing from Downloads"

commit="$(tr -d '\r\n ' < "$COMMIT_FILE")"
case "$commit" in
  *[!0-9a-f]*|'') fail "invalid commit marker" ;;
esac
[ "${#commit}" -eq 40 ] || fail "commit marker is not a full Git SHA"

expected_hash="$(tr -d '\r\n ' < "$HASH_FILE")"
case "$expected_hash" in
  *[!0-9a-f]*|'') fail "invalid SHA-256 marker" ;;
esac
[ "${#expected_hash}" -eq 64 ] || fail "SHA-256 marker has wrong length"

actual_hash="$(python3 - "$ARCHIVE" <<'PY'
import hashlib, sys
h = hashlib.sha256()
with open(sys.argv[1], "rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        h.update(chunk)
print(h.hexdigest())
PY
)"
[ "$actual_hash" = "$expected_hash" ] || fail "archive SHA-256 mismatch"

free_kb="$(df -Pk "$HOME" | awk 'NR==2 {print $4}')"
case "$free_kb" in ''|*[!0-9]*) fail "unable to read free storage" ;; esac
[ "$free_kb" -ge 524288 ] || fail "less than 512 MB free storage"

wait_ngrok_api_to_file "$BEFORE_JSON" || fail "existing ngrok Agent API did not become ready within 60 seconds"
python3 - "$BEFORE_JSON" <<'PY' || fail "existing ngrok API response is invalid"
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
if not isinstance(data.get("tunnels", []), list):
    raise SystemExit(1)
PY

port_is_free() {
  python3 - "$1" <<'PY'
import socket, sys
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.bind(("127.0.0.1", int(sys.argv[1])))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}
for port in 8897 8898 8899 8900; do
  port_is_free "$port" || fail "TCP port $port is already in use"
done

APP_ROOT="$HOME/apps/need-for-strength-owner-demo"
STATE_ROOT="$HOME/.local/state/need-for-strength-owner-demo"
CONFIG_ROOT="$HOME/.config/need-for-strength-owner-demo"

if [ -d "$STATE_ROOT/pids" ] && find "$STATE_ROOT/pids" -type f -name '*.pid' -print -quit 2>/dev/null | grep -q .; then
  fail "owner-demo PID state already exists"
fi

if python3 - "$BEFORE_JSON" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
raise SystemExit(0 if any(t.get("name") == "nfs-owner-demo" for t in data.get("tunnels", [])) else 1)
PY
then
  fail "nfs-owner-demo tunnel already exists; stop the existing demo before first-install cleanup"
fi

if [ -e "$APP_ROOT" ]; then
  [ -d "$APP_ROOT" ] || fail "owner-demo app root exists but is not a directory"
  python3 - "$APP_ROOT" <<'PY' || fail "owner-demo app root contains unmanaged or malformed content"
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
entries = list(root.iterdir())
for entry in entries:
    if entry.is_symlink() or not entry.is_dir():
        raise SystemExit(1)
    name = entry.name
    if not re.fullmatch(r"[0-9a-f]{40}", name):
        raise SystemExit(1)
    marker = entry / ".nfs-owner-demo-release"
    if not marker.is_file():
        raise SystemExit(1)
    if marker.read_text(encoding="utf-8").strip() != name:
        raise SystemExit(1)
print(f"SAFE_RESIDUAL_RELEASES={len(entries)}")
PY
  find "$APP_ROOT" -mindepth 1 -maxdepth 1 -type d -exec rm -rf -- {} +
  rmdir "$APP_ROOT" 2>/dev/null || fail "owner-demo app root could not be cleaned safely"
  echo "Removed inactive managed owner-demo release residue from an earlier failed attempt."
fi

APP="$APP_ROOT/$commit"
TMP="$APP_ROOT/.extract-$commit"
mkdir -p "$APP_ROOT"
rm -rf "$TMP"
mkdir -p "$TMP"
tar -xzf "$ARCHIVE" -C "$TMP"
[ -f "$TMP/admin/deploy/owner-demo/install-owner-demo-standalone.sh" ] || fail "archive is missing standalone owner-demo installer"
mv "$TMP" "$APP"
printf '%s\n' "$commit" > "$APP/.nfs-owner-demo-release"

cleanup_failed_install() {
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "Owner-demo install failed; cleaning only Need For Strength demo processes/tunnel."
    if [ -x "$APP/admin/deploy/owner-demo/stop-owner-demo-standalone.sh" ]; then
      bash "$APP/admin/deploy/owner-demo/stop-owner-demo-standalone.sh" || true
    fi
  fi
  exit "$rc"
}
trap cleanup_failed_install EXIT

cd "$APP"
bash admin/deploy/owner-demo/install-owner-demo-standalone.sh

wait_ngrok_api_to_file "$AFTER_JSON" || fail "ngrok Agent API did not recover after owner-demo install"
python3 - "$BEFORE_JSON" "$AFTER_JSON" <<'PY'
import json, sys
before = json.load(open(sys.argv[1], encoding="utf-8"))
after = json.load(open(sys.argv[2], encoding="utf-8"))
before_map = {t.get("name"): t.get("public_url") for t in before.get("tunnels", [])}
after_map = {t.get("name"): t.get("public_url") for t in after.get("tunnels", [])}
for name, public in before_map.items():
    if name == "nfs-owner-demo":
        continue
    if after_map.get(name) != public:
        raise SystemExit(f"pre-existing ngrok tunnel changed: {name}")
if not str(after_map.get("nfs-owner-demo") or "").startswith("https://"):
    raise SystemExit("owner-demo HTTPS tunnel missing")
print("EXISTING_NGROK_TUNNELS=PRESERVED")
PY

trap - EXIT
rm -f "$BEFORE_JSON" "$AFTER_JSON"

echo "OWNER_DEMO_BOOTSTRAP=PASS"
echo "Commit: $commit"
echo "Result file: $RESULT"
echo "To stop only the owner demo:"
echo "  bash $APP/admin/deploy/owner-demo/stop-owner-demo-standalone.sh"
