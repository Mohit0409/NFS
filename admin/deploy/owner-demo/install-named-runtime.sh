#!/data/data/com.termux/files/usr/bin/bash
# Installs only the NFS production recovery path; config and SQLite data are preserved.
set -euo pipefail
umask 077

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
APP_ROOT="$HOME/apps/need-for-strength-owner-demo"
CONFIG_DIR="$HOME/.config/need-for-strength-owner-demo"
CONFIG="$CONFIG_DIR/demo.env"
STATE="$HOME/.local/state/need-for-strength-owner-demo"
RUNTIME="$STATE/nfs-runtime.sh"
BOOT_DIR="$HOME/.termux/boot"
BOOT="$BOOT_DIR/need-for-strength-runtime"

fail() { echo "NFS_NAMED_INSTALL=BLOCKED: $*" >&2; exit 1; }
[ -r "$CONFIG" ] || fail "missing existing NFS configuration"
[ -r "$CONFIG_DIR/cloudflared-named.yml" ] || fail "missing existing NFS named-tunnel configuration"
[ -r "$REPO/../.nfs-owner-demo-release" ] || fail "run from a commit-pinned NFS release"

python3 - "$CONFIG" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
required = {
    "APP_BASE_URL": "https://nfsnmh.com",
    "NEW_GYM_PUBLIC_SITE_URL": "https://nfsnmh.com",
    "NEW_GYM_MEMBER_ALLOWED_ORIGINS": "https://nfsnmh.com,https://www.nfsnmh.com",
    "GRAVITY_ADDITIONAL_ORIGINS": "https://admin.nfsnmh.com",
    "ADMIN_PORTAL_ROOT_REDIRECT": "true",
}
lines = path.read_text(encoding="utf-8").splitlines()
seen = set()
out = []
for line in lines:
    key = line.split("=", 1)[0].strip()
    if key in required:
        out.append(f"{key}={required[key]}")
        seen.add(key)
    else:
        out.append(line)
out.extend(f"{key}={value}" for key, value in required.items() if key not in seen)
path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
chmod 600 "$CONFIG"

mkdir -p "$STATE" "$BOOT_DIR"
chmod 700 "$STATE" "$BOOT_DIR"
printf '%s\n' "$REPO" > "$CONFIG_DIR/repository"
chmod 600 "$CONFIG_DIR/repository"
install -m 700 "$REPO/deploy/owner-demo/nfs-runtime.sh" "$RUNTIME"

if [ -e "$BOOT" ] && ! grep -Fq 'Need For Strength production runtime' "$BOOT"; then
  fail "refusing to replace unmanaged Termux:Boot file $BOOT"
fi
cat > "$BOOT" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Need For Strength production runtime; owns no services outside its dedicated paths.
sleep 12
exec "$HOME/.local/state/need-for-strength-owner-demo/nfs-runtime.sh" recover
EOF
chmod 700 "$BOOT"

"$RUNTIME" restart
echo "NFS_NAMED_INSTALL=PASS"
echo "RELEASE=$(cat "$REPO/../.nfs-owner-demo-release")"
