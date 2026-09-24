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
3. Run the New Gym Termux installer without enabling the tunnel.
4. Fill and protect `~/.config/new-gym/new-gym.env`.
5. Run DB migrations and verify integrity.
6. Start local New Gym services only.
7. Verify:
   - `http://127.0.0.1:8897/api/health`
   - `http://127.0.0.1:8898/api/health`
   - `http://127.0.0.1:8899/`
8. Create and verify a local backup.
9. Verify off-device backup.
10. Configure the dedicated Cloudflare Tunnel routes.
11. Enable the tunnel.
12. Run browser regression against the final domains.
13. Record deployment commit, backup IDs and acceptance results in deployment-track-record.

## Rollback

Rollback must restore:
- the prior New Gym release commit
- the matching New Gym database backup
- the New Gym tunnel/service configuration only

Never use Gravity rollback assets for this project.
