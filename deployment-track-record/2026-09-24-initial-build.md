# Deployment Track Record — 2026-09-24

## Deployment result

**NOT DEPLOYED**

This record documents local development milestones only.

## Git milestones

1. `fcb92de` — Initial new gym platform build
   - isolated repository
   - reused gym admin baseline
   - redesigned customer website
   - Pool/Kitchen base
   - migration 014

2. `dddea61` — Add reservations inventory and Redmi isolation
   - pool reservations/check-in
   - kitchen inventory
   - isolated New Gym Termux profile
   - customer runtime configuration
   - migration 015
   - backend regression 221/221 PASS

3. `7a18718` — Add combined pool kitchen settlement
   - combined Pool + Kitchen final bill
   - atomic final settlement/payment method
   - bill UI
   - migration 016
   - backend regression 223/223 PASS

4. `308f2f2` — Harden Firebase isolation and browser gates
   - removed copied Gravity Firebase default aliases
   - added Firebase isolation regression guard
   - installed isolated Playwright dependencies
   - added New Gym Pool/Kitchen Chromium coverage

5. `e143085` — Add daily pool kitchen operations reporting
   - date-based Pool + Kitchen operations report
   - settled/outstanding revenue, usage, top items and low-stock reporting
   - explicit Asia/Kolkata business-day handling
   - backend regression 227/227 PASS

6. `d7d7755` — Add kitchen recipes and automatic stock usage
   - recipe definitions linking menu items to inventory
   - atomic automatic ingredient deduction at Served
   - insufficient stock blocks serving without partial changes
   - idempotent per-order-item inventory usage records
   - migration 017
   - backend regression 230/230 PASS

7. `9b9b88d` — Add fail-closed New Gym launch preflight
   - staged install and launch preflight
   - tunnel enable is blocked until launch preflight passes
   - explicit owner confirmation gates for membership pricing, pool rates and kitchen setup
   - dedicated Firebase/service-account, Cloudflare token and off-device-backup checks
   - placeholder identity/domain/customer config rejected
   - template launch preflight verified to fail closed with explicit blocker codes
   - backend regression 232/232 PASS

8. `3fb4494` — Validate live New Gym database before launch
   - read-only SQLite launch inspection
   - schema/integrity/foreign-key gates
   - detects the three inherited Gravity plan signatures from migration 013
   - requires all three pool hourly rates
   - requires confirmed live kitchen menu/inventory data and valid recipes
   - backend regression 233/233 PASS

9. `e671267` — Require fresh verified off-device backup for launch
   - off-device backup marker is written only after rclone copy + rclone check
   - marker records verification time, archive SHA-256 and remote path
   - launch blocks stale, invalid or wrong-remote backup markers
   - default freshness window: 24 hours
   - backend regression 234/234 PASS

10. `966ba75` — Record kitchen payment method in admin workflow
   - standalone kitchen payments capture Cash / UPI / Card / Bank transfer / Other
   - payment method appears in order state and daily operations reporting

11. `c94ae1c` — Add audited kitchen order cancellation
   - required cancellation reason for unpaid, unserved orders
   - cancelled orders are voided and timestamped
   - paid orders must be voided/refunded before cancellation
   - cancellation before Served leaves recipe stock unchanged
   - migration 018
   - backend regression 237/237 PASS
   - local Chromium 6/6 PASS

12. `13ac7fe` — Add editable pool reservations
   - edit/reschedule upcoming reservations before check-in
   - table/time/contact/rate/note updates
   - overlap and disabled-table validation re-run on every edit
   - checked-in reservations remain immutable
   - blank custom rate inherits the selected table rate
   - no schema change; schema remains 018
   - backend regression 239/239 PASS
   - local Chromium 6/6 PASS

13. `23e5b04` — Add audited kitchen payment voiding
   - migration 019 adds payment void reason/timestamp
   - paid standalone kitchen payments require a void reason
   - voided payments cannot be reopened
   - served pool-linked orders cannot be independently voided
   - voided un-cancelled pool orders block combined final settlement
   - backend regression 241/241 PASS
   - local Chromium 6/6 PASS

14. `d4a17ba` — Automate New Gym Termux Python runtime
   - clean Termux installer can create checkout-local admin/.venv
   - installs New Gym package with Firebase dependencies
   - verifies cryptography, firebase_admin and server.gravity imports
   - Python package metadata renamed to new-gym-platform
   - isolated wheel build PASS
   - backend regression 241/241 PASS

15. `804c6d7` — Require local Redmi acceptance before tunnel
   - tunnel must be down during acceptance
   - admin/member/public services must all be running
   - ports 8897/8898/8899 must be loopback-only
   - admin and member health endpoints must pass
   - public website must respond while /admin and /api/admin/session remain unavailable
   - installer enforces launch-preflight → local-acceptance → tunnel order
   - backend regression 242/242 PASS

16. `4dad392` — Generate isolated customer runtime config
   - production customer config is rendered from protected New Gym env values
   - active 1/3/12-month membership prices are read from the live New Gym SQLite database
   - generated releases are stored outside Git under New Gym's data directory
   - web service serves only the generated `public-current` release
   - `--enable-tunnel` regenerates a complete release before launch preflight
   - launch preflight validates the generated config path instead of the tracked placeholder
   - backend regression 243/243 PASS

17. `a77aa98` — Add guarded customer-site rollback
   - every generated public release gets a Git/config-hash manifest
   - installer verifies the manifest before activating a release
   - rollback only accepts release IDs inside the New Gym public-releases directory
   - rollback re-verifies config SHA-256 and rejects Gravity live markers
   - web service is restarted and locally checked after rollback
   - backend regression 244/244 PASS

## Browser isolation verification

- copied Firebase default aliases removed from both New Gym .firebaserc files
- Firebase isolation regression: PASS
- inherited admin reliability Chromium suite: 3/3 PASS
- New Gym Pool/Kitchen/Reporting/Recipe/Reservation Chromium suite: 3/3 PASS
- daily Operations Report Chromium flow included
- local admin Chromium total: 6/6 PASS
- final-domain E2E remains pending until domains/configuration exist

## Customer verification

- homepage 8/8 PASS
- member-login 9/9 PASS
- diet planner PASS
- member gateway 7/7 PASS

## Production impact

None.

- Gravity Fitness not modified.
- Vibe4You not modified.
- No Redmi New Gym services installed.
- No tunnel created.
- No production database created.
- No Firebase project configured.
- No customer traffic moved.

## Current launch-preflight blockers

The untouched template intentionally fails launch preflight for:
- production secret key
- verified gym name/address/owner contact
- final admin/customer HTTPS origins
- membership pricing confirmation
- pool-rate confirmation
- kitchen/menu/recipe/opening-stock confirmation
- dedicated Firebase client/service-account configuration
- dedicated Cloudflare token
- off-device backup destination
- complete generated customer runtime config (business identity/contact/hours + public origin + dedicated Firebase + live membership prices)

These are configuration/business-data blockers, not unresolved code failures.

## Required before first deployment

See:
- `wiki/DEPLOYMENT_RUNBOOK.md`
- `jira/JIRA-REGISTER.md`
