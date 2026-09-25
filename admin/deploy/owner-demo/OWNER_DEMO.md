# Need For Strength — Owner Demo

This profile is for showing the current system to the gym owner before final production information is approved.

## Known details used

- Gym: **Need For Strength**
- Pool: **The Cue Master**
- Address: **Opposite Pachvati Colony, Near Nakoda Dham Temple, Neemuch, Madhya Pradesh**
- Phone / WhatsApp: **+91 98937 04372**
- Instagram: **@needforstrength**
- Membership/PT prices: taken from the supplied Need For Strength opening poster.

## Explicit demo-only values

- Opening hours: **6:00 AM – 10:00 PM daily**
- Cue Master private table: **₹300/hour**
- Cue Master common tables: **₹200/hour**
- Kitchen menu, stock quantities and recipes
- Owner email placeholder
- Firebase/member OTP is intentionally not configured for this first preview.

The demo database is marked with `owner_demo_mode=1`. The production launch preflight rejects this marker.

## Exposure

One temporary ngrok HTTPS URL is used:

- `/` → customer website
- `/admin` → admin portal
- `/api/member/*` → member gateway
- admin API/assets → admin backend

Only localhost ports are used behind ngrok:

- 8897 admin/backend
- 8898 member gateway
- 8899 customer site
- 8900 owner-demo edge router

The ngrok authtoken is managed by ngrok itself. It is never stored in this repository or passed on a command line by the demo scripts.

## Redmi/Termux setup

### Current target

The owner-demo target has been positively identified over USB as:
- Xiaomi Redmi 13C 5G
- model `23124RN87I`
- Termux user `u0_a304`
- more than 80 GB free storage at the latest USB preflight
- owner-demo ports 8897, 8898, 8899 and 8900 free
- no existing Need For Strength owner-demo app/process state.

The Redmi already has a running ngrok agent with a non-demo `command_line` tunnel targeting `localhost:8788`. The owner demo must **reuse this existing agent** and must not stop, replace or reconfigure that tunnel.

### SSH deployment when redmi-host is reachable

From the repository root on the Windows development PC:

`powershell -ExecutionPolicy Bypass -File admin/deploy/owner-demo/deploy-from-pc.ps1 -PreflightOnly`

The preflight uses the same standalone checks as the USB path: exact Redmi identity, clean Git commit, storage, Python/venv/package-index readiness, existing ngrok Agent API, and free owner-demo ports.

After preflight passes:

`powershell -ExecutionPolicy Bypass -File admin/deploy/owner-demo/deploy-from-pc.ps1`

The launcher archives the exact Git commit, calculates SHA-256, uploads the archive/hash/commit/bootstrap only to the dedicated Need For Strength staging path, then invokes the same verified standalone bootstrap used by USB deployment.

### USB deployment when Tailscale/SSH keys are unavailable

The development PC may stage four files into Android Downloads:
- `need-for-strength-owner-demo.tar.gz`
- `need-for-strength-owner-demo.sha256`
- `need-for-strength-owner-demo.commit`
- `nfs-owner-demo-bootstrap.sh`

Then, in the already-open Termux app, run exactly:

`bash /sdcard/Download/nfs-owner-demo-bootstrap.sh`

The bootstrap:
- verifies the exact Redmi user/model
- verifies archive SHA-256 and full Git commit marker
- refuses occupied owner-demo ports or previous demo state
- verifies Python/venv/PyPI readiness
- requires the existing ngrok Agent API
- installs only into dedicated Need For Strength demo paths
- creates only the `nfs-owner-demo` tunnel to `127.0.0.1:8900`
- verifies every pre-existing ngrok tunnel remains unchanged
- cleans up only Need For Strength demo processes/tunnel if setup fails.

It writes the final customer/admin links to:
`/sdcard/Download/need-for-strength-owner-demo-result.txt`

Admin-owner credentials are still created separately with the secure interactive bootstrap command; credentials are not generated or stored in Git.

## Stop the demo

For the standalone Redmi preview:

`bash ~/apps/need-for-strength-owner-demo/<commit>/admin/deploy/owner-demo/stop-owner-demo-standalone.sh`

This stops only Need For Strength demo processes and deletes only the `nfs-owner-demo` tunnel. Existing non-demo ngrok tunnels and the demo database/config remain preserved.

## After owner approval

Do **not** promote the demo database. Replace it with a clean production database and enter owner-approved:
- opening hours
- final membership structure/prices
- Cue Master rates
- kitchen menu/prices/recipes/opening stock
- owner email
- dedicated Firebase project
- production domain/tunnel
- off-device backup destination

Then run the normal production preflight and final-domain regression.
