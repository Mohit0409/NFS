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

printf '%s\n' "$output"
printf 'offdevicePath=%s\n' "$target"
