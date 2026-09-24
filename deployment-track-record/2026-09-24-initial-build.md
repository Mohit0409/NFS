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

## Required before first deployment

See:
- `wiki/DEPLOYMENT_RUNBOOK.md`
- `jira/JIRA-REGISTER.md`
