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

## Browser isolation verification

- copied Firebase default aliases removed from both New Gym .firebaserc files
- Firebase isolation regression: PASS
- inherited admin reliability Chromium suite: 3/3 PASS
- New Gym Pool/Kitchen/Reporting/Recipe Chromium suite: 3/3 PASS
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
- final customer runtime config

These are configuration/business-data blockers, not unresolved code failures.

## Required before first deployment

See:
- `wiki/DEPLOYMENT_RUNBOOK.md`
- `jira/JIRA-REGISTER.md`
