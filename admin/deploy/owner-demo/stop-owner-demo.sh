#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
for service in nfs-demo-ngrok nfs-demo-edge nfs-demo-web nfs-demo-member nfs-demo-admin; do
  if [ -d "$PREFIX/var/service/$service" ]; then
    sv down "$service" >/dev/null 2>&1 || true
  fi
done
echo "Need For Strength owner-demo services stopped."
echo "Demo database/config were preserved for the next preview."
