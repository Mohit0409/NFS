#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

CONFIG="${NEW_GYM_ENV_FILE:-$HOME/.config/new-gym/new-gym.env}"
REPO="$(cat "$HOME/.config/new-gym/repository")"
if [ "${NEW_GYM_ENV_LOADED:-}" != 1 ]; then
  exec python3 "$REPO/scripts/gravity-env.py" --config "$CONFIG" -- \
    env NEW_GYM_ENV_LOADED=1 "$0"
fi

output="$(GRAVITY_ENV_FILE="$CONFIG" "$REPO/scripts/backup-gravity.sh" daily)"
created="$(printf '%s\n' "$output" | sed -n 's/^created=//p')"
archive="$(printf '%s' "$created" | python3 -c 'import json,sys; print(json.load(sys.stdin)["path"])')"
remote="${NEW_GYM_BACKUP_REMOTE:-}"
required="${NEW_GYM_REQUIRE_OFFDEVICE_BACKUP:-true}"

if [ -z "$remote" ]; then
  case "$(printf '%s' "$required" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) echo "NEW_GYM_BACKUP_REMOTE is required but not configured." >&2; exit 1 ;;
    *) printf '%s\n' "$output"; exit 0 ;;
  esac
fi
case "$remote" in *:*) ;; *) echo "NEW_GYM_BACKUP_REMOTE must be an rclone remote:path." >&2; exit 1 ;; esac
command -v rclone >/dev/null 2>&1 || { echo "rclone is required for off-device backup." >&2; exit 1; }

name="$(basename "$archive")"
target="${remote%/}/$name"
rclone copyto "$archive" "$target" --immutable
rclone check "$(dirname "$archive")" "${remote%/}" --include "$name" --one-way --download

marker="${NEW_GYM_OFFDEVICE_BACKUP_MARKER:-$HOME/.local/state/new-gym/offdevice-backup.json}"
mkdir -p "$(dirname "$marker")"
archive_sha="$(python3 - "$archive" <<'PY'
import hashlib
import sys
from pathlib import Path

path = Path(sys.argv[1])
digest = hashlib.sha256()
with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
print(digest.hexdigest())
PY
)"
python3 - "$marker" "$archive" "$archive_sha" "$target" <<'PY'
import json
import os
import sys
import time
from pathlib import Path

marker = Path(sys.argv[1])
payload = {
    "verifiedAt": int(time.time()),
    "archiveName": Path(sys.argv[2]).name,
    "archiveSha256": sys.argv[3],
    "remotePath": sys.argv[4],
}
temporary = marker.with_suffix(marker.suffix + ".tmp")
temporary.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
os.chmod(temporary, 0o600)
temporary.replace(marker)
os.chmod(marker, 0o600)
PY

printf '%s\n' "$output"
printf 'offdevicePath=%s\n' "$target"
printf 'offdeviceMarker=%s\n' "$marker"
