#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

DATA="$HOME/.local/share/new-gym"
STATE="$HOME/.local/state/new-gym"
REPO_FILE="$HOME/.config/new-gym/repository"
[ -r "$REPO_FILE" ] || { echo "New Gym repository marker is missing." >&2; exit 1; }
REPO="$(cat "$REPO_FILE")"
RELEASES="$DATA/public-releases"
CURRENT="$DATA/public-current"

usage() {
  echo "usage: rollback-public-site.sh --list | <release-id>" >&2
  exit 2
}

[ "$#" -eq 1 ] || usage
mkdir -p "$RELEASES" "$STATE"

if [ "$1" = "--list" ]; then
  current_target="$(readlink "$CURRENT" 2>/dev/null || true)"
  for release in "$RELEASES"/*; do
    [ -d "$release" ] || continue
    name="$(basename "$release")"
    if [ "$release" = "$current_target" ]; then
      printf '* %s\n' "$name"
    else
      printf '  %s\n' "$name"
    fi
  done
  exit 0
fi

release_id="$1"
case "$release_id" in
  ""|*[!A-Za-z0-9._-]*|*..*) echo "Invalid release id." >&2; exit 2 ;;
esac

target="$RELEASES/$release_id"
[ -d "$target" ] || { echo "Release does not exist: $release_id" >&2; exit 1; }
[ -f "$target/index.html" ] || { echo "Release is missing index.html" >&2; exit 1; }
[ -f "$target/js/gym-config.js" ] || { echo "Release is missing gym-config.js" >&2; exit 1; }
[ -f "$target/.new-gym-release.json" ] || { echo "Release is missing manifest" >&2; exit 1; }

python3 "$REPO/deploy/new-gym-termux/verify-public-release.py"   --release "$target"   --release-id "$release_id"

ln -sfn "$target" "$CURRENT"
printf '%s\n' "$target" > "$STATE/public-release"
chmod 600 "$STATE/public-release"

if command -v sv >/dev/null 2>&1; then
  sv restart new-gym-web
fi
if command -v curl >/dev/null 2>&1; then
  curl -fsS --max-time 5 "http://127.0.0.1:8899/" >/dev/null
fi

echo "New Gym public site rolled back to: $release_id"
