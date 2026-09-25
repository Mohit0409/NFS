#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

case "${PREFIX:-}" in
  /data/data/com.termux/files/usr) ;;
  *) echo "This owner-demo runtime preparer must run inside Termux." >&2; exit 1 ;;
esac

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
VENV="${OWNER_DEMO_VENV:-$REPO/.venv}"

for command in python3; do
  command -v "$command" >/dev/null 2>&1 || { echo "Missing command: $command" >&2; exit 1; }
done

# Owner preview intentionally has no Firebase project/service account yet.
# Reuse Termux's verified cryptography package and install only the base app.
python3 - <<'PY'
import cryptography
print("OWNER_DEMO_SYSTEM_CRYPTOGRAPHY_OK=" + cryptography.__version__)
PY

if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv --system-site-packages "$VENV"
fi

"$VENV/bin/python" -m pip install --disable-pip-version-check --no-deps --no-build-isolation -e "$REPO"

"$VENV/bin/python" - <<'PY'
import importlib
import importlib.util
import sys

for name in ("cryptography", "server.gravity"):
    importlib.import_module(name)

# Firebase is intentionally optional in the owner preview. The backend must
# remain importable even when firebase_admin is not installed.
print("OWNER_DEMO_FIREBASE_ADMIN_PRESENT=" + ("YES" if importlib.util.find_spec("firebase_admin") else "NO"))
print("OWNER_DEMO_RUNTIME_IMPORTS_OK")
print("PYTHON=" + sys.executable)
PY

echo "Need For Strength owner-demo Python runtime is ready: $VENV/bin/python"
