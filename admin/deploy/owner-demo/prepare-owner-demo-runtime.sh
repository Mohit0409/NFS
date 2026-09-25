#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

case "${PREFIX:-}" in
  /data/data/com.termux/files/usr) ;;
  *) echo "This owner-demo runtime preparer must run inside Termux." >&2; exit 1 ;;
esac

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
PYTHON="${OWNER_DEMO_PYTHON:-$(command -v python3)}"

[ -x "$PYTHON" ] || { echo "Missing executable Python runtime: $PYTHON" >&2; exit 1; }

# Owner preview intentionally has no Firebase project/service account yet.
# Run directly from the immutable extracted source tree without a package-build step.
# This is both smaller and more reliable on Termux/Python 3.14.
export PYTHONPATH="$REPO${PYTHONPATH:+:$PYTHONPATH}"

"$PYTHON" - <<'PY'
import importlib
import importlib.util
import sys

for name in ("cryptography", "server.gravity"):
    module = importlib.import_module(name)
    if name == "cryptography":
        print("OWNER_DEMO_SYSTEM_CRYPTOGRAPHY_OK=" + module.__version__)

print("OWNER_DEMO_FIREBASE_ADMIN_PRESENT=" + ("YES" if importlib.util.find_spec("firebase_admin") else "NO"))
print("OWNER_DEMO_RUNTIME_IMPORTS_OK")
print("PYTHON=" + sys.executable)
PY

echo "Need For Strength owner-demo source runtime is ready: $PYTHON"
