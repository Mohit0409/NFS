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

### Preferred: deploy from the development PC

From the repository root on the Windows development PC:

`powershell -ExecutionPolicy Bypass -File admin/deploy/owner-demo/deploy-from-pc.ps1 -PreflightOnly`

The preflight refuses deployment unless:
- Git is clean and an exact commit can be archived
- SSH reaches the configured `redmi-host`
- Termux user is `u0_a304`
- device identifies as the configured Redmi 13C 5G / 23124RN87I
- at least 512 MB free storage exists
- ports 8897–8900 are free or already belong to the matching managed demo services
- any existing `nfs-demo-*` services carry the owner-demo managed marker
- ngrok is installed and authenticated.

After preflight passes:

`powershell -ExecutionPolicy Bypass -File admin/deploy/owner-demo/deploy-from-pc.ps1`

The PC launcher creates a `git archive` of the exact commit, uploads only to the dedicated Need For Strength owner-demo staging/app directories, runs the isolated Termux installer and prints the customer/admin ngrok URLs.

### Directly on the Redmi

1. Install/configure ngrok in Termux and confirm `ngrok config check` succeeds.
2. Run:

   `bash admin/deploy/owner-demo/install-owner-demo.sh`

3. If the admin owner is not configured, run the bootstrap command printed by the installer and choose the demo password yourself.
4. Re-run the installer after bootstrap if needed. It prints:
   - customer URL
   - admin URL at `<same-url>/admin`

## Stop the demo

`bash admin/deploy/owner-demo/stop-owner-demo.sh`

Stopping preserves the isolated demo database and config.

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
