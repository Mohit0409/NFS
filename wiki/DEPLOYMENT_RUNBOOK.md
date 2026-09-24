# New Gym Redmi Deployment Runbook

Status: NOT DEPLOYED.

## Pre-deployment requirements

Must be known/configured:
- real gym name
- admin hostname
- customer hostname
- phone/WhatsApp/address/opening hours
- membership prices
- pool hourly rates
- initial kitchen menu/stock
- New Gym Firebase project
- New Gym Cloudflare Tunnel/token
- dedicated off-device backup remote
- production SECRET_KEY

## Termux profile

Source:
`admin/deploy/new-gym-termux/`

Runtime:
- config: `~/.config/new-gym/new-gym.env`
- state: `~/.local/state/new-gym`
- data: `~/.local/share/new-gym`

Ports:
- 8897 admin/backend
- 8898 member gateway
- 8899 public website

## Safe rollout order

1. Copy/clone this isolated project to Redmi.
2. Create Python virtual environment for the admin/backend.
3. Run the New Gym Termux installer without enabling the tunnel. On first run it creates the protected env template and exits.
4. Fill and protect `~/.config/new-gym/new-gym.env`.
5. Rerun the installer. It must pass:
   `python3 admin/deploy/new-gym-termux/preflight-new-gym.py --config ~/.config/new-gym/new-gym.env --stage install`
6. Run DB migrations and verify integrity.
7. Start local New Gym services only.
8. Verify:
   - `http://127.0.0.1:8897/api/health`
   - `http://127.0.0.1:8898/api/health`
   - `http://127.0.0.1:8899/`
9. Create and verify a local backup.
10. Verify off-device backup.
11. Configure the dedicated Cloudflare Tunnel routes and final customer `gym-config.js`.
12. Set the three owner confirmation gates to true only after reviewing membership prices, pool rates, and kitchen/menu/recipe/opening stock.
13. Run the launch gate:
   `python3 admin/deploy/new-gym-termux/preflight-new-gym.py --config ~/.config/new-gym/new-gym.env --stage launch`
14. Enable the tunnel only if the launch gate returns `"ready":true`.
15. Run browser regression against the final domains.
16. Record deployment commit, backup IDs and acceptance results in deployment-track-record.

## Preflight behavior

The preflight output is JSON and does not expose secret values. Launch is blocked for placeholder domains/business identity, copied Gravity Firebase values, missing Firebase service-account/tunnel files, missing off-device backup destination, unconfirmed pricing/rates/kitchen setup, or an incomplete customer runtime config.

At launch stage it also opens the configured New Gym SQLite database read-only and requires:
- schema migration 017 or newer
- SQLite quick-check and foreign-key check PASS
- at least one valid active membership plan
- none of the three untouched Gravity plan signatures (1 Month ₹1,200; 3 Months ₹3,000; 1 Year ₹10,000)
- exactly three pool tables with positive hourly rates
- at least one available kitchen menu item and one active inventory item
- no recipe referencing missing/inactive stock

The installer calls the install-stage preflight automatically. `--enable-tunnel` calls the stricter launch-stage preflight before the tunnel service is enabled.

A launch also requires a fresh verified off-device backup marker. `backup-offdevice.sh` creates that marker only after the archive is copied and `rclone check` succeeds. The default maximum age is 86,400 seconds (24 hours), and the marker must match the currently configured backup remote.

## Rollback

Rollback must restore:
- the prior New Gym release commit
- the matching New Gym database backup
- the New Gym tunnel/service configuration only

Never use Gravity rollback assets for this project.
