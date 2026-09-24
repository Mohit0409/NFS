#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

case "${PREFIX:-}" in
  /data/data/com.termux/files/usr) ;;
  *) echo "This runtime preparer must run inside Termux." >&2; exit 1 ;;
esac

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
VENV="${NEW_GYM_VENV:-$REPO/.venv}"

for command in python3 git; do
  command -v "$command" >/dev/null 2>&1 || { echo "Missing command: $command" >&2; exit 1; }
done

if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv --system-site-packages "$VENV"
fi

"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV/bin/python" -m pip install --upgrade -e "$REPO[firebase]"

"$VENV/bin/python" - <<'PY'
import importlib
import sys

required = (
    "cryptography",
    "firebase_admin",
    "server.gravity",
)
missing = []
for name in required:
    try:
        importlib.import_module(name)
    except Exception as error:
        missing.append(f"{name}: {error}")
if missing:
    raise SystemExit("Runtime import verification failed: " + "; ".join(missing))
print("NEW_GYM_RUNTIME_IMPORTS_OK")
print("PYTHON=" + sys.executable)
PY

echo "New Gym Python runtime is ready: $VENV/bin/python"
