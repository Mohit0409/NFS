# Need For Strength Platform

Independent gym platform for **Need For Strength**, including **The Cue Master** pool lounge, built from the proven Gravity Fitness application structure.

## Safety boundary

Project root:

`C:\movieXsuggestion\MyProject\new_gym_platform`

This repository is separate from live Gravity Fitness and Vibe4You. No live Gravity database, Firebase project, customer phone number, analytics project, gateway, Cloudflare service name, or deployment state is reused.

## Structure

- `admin/` — gym backend/admin portal plus Pool and Kitchen operations.
- `customer-website/` — redesigned public website, member UI, diet planner, exercise library and independent member gateway.
- `admin/deploy/new-gym-termux/` — isolated Redmi/Termux production profile.
- `wiki/` — architecture, operations and deployment runbook.
- `jira/` — local New Gym work/status register.
- `deployment-track-record/` — immutable-style local release/deployment history.

## Admin portal

Existing gym functionality retained:
- member/staff directory
- membership plans, renewals and expiry
- fees, payments and receipts
- attendance
- biometric support
- enquiries
- notifications/follow-ups
- coaching
- admin accounts/permissions
- audit and readiness

### The Cue Master — Pool

Three seeded tables:
- Private Table
- Common Table 1
- Common Table 2

Implemented:
- configurable hourly rate
- walk-in timed sessions
- server-calculated duration/charge
- session history
- advance reservations
- upcoming reservations can be edited/rescheduled before check-in
- edit/reschedule revalidates table availability and overlap rules
- overlap protection per table/time window
- guest name/mobile/note
- reservation-specific rate
- reservation check-in starts the timer
- cancel/no-show states
- reservation automatically completes when its checked-in session ends
- next reservation visible on the live table card
- combined Pool + Kitchen final bill
- final settlement blocked until the pool session is ended and all payable kitchen orders are served/cancelled
- one settlement action records the payment method across unpaid pool/kitchen components

### Kitchen

Implemented:
- menu item/category/price management
- available/unavailable state
- walk-in and pool-session-linked orders
- historical price snapshots
- New -> Preparing -> Ready -> Served order flow
- payment state
- manual kitchen inventory
- unit + quantity + low-stock threshold
- audited purchase/usage/waste/adjustment movements
- stock cannot fall below zero
- configurable menu recipes linking menu items to inventory ingredients
- automatic ingredient deduction when an order is marked Served
- recipe deductions are idempotent and cannot be applied twice
- serving is blocked atomically if any required ingredient is inactive or insufficient
- unpaid unserved orders can be cancelled only with a required reason
- cancellation is audited, timestamps the order, and automatically moves its payment state to void
- paid orders cannot be cancelled until their payment is separately voided/refunded
- standalone paid kitchen payments can be voided only with a mandatory audit reason
- voided payments retain their original payment method and cannot be reopened
- served pool-linked kitchen payments cannot be voided independently from the combined bill
- voided, un-cancelled pool-linked orders block final settlement
- cancellation before Served never consumes recipe inventory

## Daily operations report

The admin portal now includes a date-based Pool & Kitchen Operations Report with:
- pool sessions, minutes, billed and paid amounts by table
- kitchen order count and sales
- combined operations sales
- settled revenue by payment method
- selected-day outstanding amount
- current active pool/open kitchen counts
- reservation and kitchen status counts
- top kitchen items
- current low-stock inventory

Business-day boundaries use `BUSINESS_TIMEZONE`, defaulting to `Asia/Kolkata`.

## Database

New Gym operations migrations:
- `014_pool_kitchen.sql`
- `015_pool_reservations_kitchen_inventory.sql`
- `016_pool_kitchen_billing.sql`
- `017_kitchen_recipes.sql`
- `018_kitchen_cancellation.sql`
- `019_kitchen_payment_void.sql`

Latest schema migration: `019`.

## Branding

- Backend default: `BUSINESS_NAME=Need For Strength`
- Pool display name: `POOL_NAME=The Cue Master`
- Admin login/header/sidebar and Pool workspace derive their display names from backend health/config.
- Internal `server.gravity` / `GRAVITY_*` names remain for copied-code compatibility; OS-level services/config directories stay isolated from Gravity Fitness.

## Customer website

Retained functionality:
- membership information
- BMI calculator
- Indian diet planner
- exercise library
- member login UI
- enquiry UI

New visual identity:
- warm light background
- deep navy typography
- coral/orange accent
- softer cards
- club/lounge presentation

Files:
- theme: `customer-website/web/css/new-gym-theme.css`
- tracked placeholder config: `customer-website/web/js/gym-config.js`
- runtime renderer: `customer-website/web/js/runtime-config.js`
- production config generator: `admin/deploy/new-gym-termux/render-customer-config.py`

On the Redmi, the web service does **not** serve the Git checkout directly. The installer copies the customer site into a versioned New Gym public release, renders `gym-config.js` from the protected production env plus active membership-plan prices in SQLite, writes a release manifest containing the Git commit and customer-config SHA-256, verifies the release, then points `~/.local/share/new-gym/public-current` at it. This keeps secrets/configuration and deployment state out of Git.

Public-site rollback is isolated from backend/database rollback: `admin/deploy/new-gym-termux/rollback-public-site.sh --list` lists prepared releases, and passing a release ID switches only to a manifest/hash-verified New Gym public release before restarting the web service. A release containing Gravity live markers is refused.

The single customer config controls:
- gym name
- city
- phone
- WhatsApp
- address
- opening hours
- Instagram
- Google Maps URL/embed
- website URL
- membership prices
- member gateway
- Firebase Auth
- analytics Firebase

Known owner details now used in the owner preview are Need For Strength, Neemuch, the supplied Pachvati Colony / Nakoda Dham address, phone/WhatsApp 9893704372, Instagram @needforstrength, November 2026 opening announcement, and the membership/PT pricing visible in the supplied poster. Unknown production details remain explicit placeholders or are isolated demo-only values. Gravity's live customer endpoints/configuration are not inherited.

## Owner demo via ngrok

Dedicated preview profile:
`admin/deploy/owner-demo/`

The owner-demo profile is separate from the production Termux profile. It uses one temporary ngrok HTTPS URL:
- `/` → customer website
- `/admin` → admin portal
- `/api/member/*` → member gateway
- admin API/assets → admin backend

Local demo ports remain loopback-only: admin 8897, member gateway 8898, customer site 8899, demo edge router 8900. The ngrok authtoken is managed by ngrok itself and is never stored in this repository.

Demo-only values currently include:
- opening hours: 6:00 AM–10:00 PM daily
- The Cue Master private table: ₹300/hour
- The Cue Master two common tables: ₹200/hour
- sample kitchen menu, recipes and stock
- placeholder owner email
- Firebase/member OTP disabled for the first owner preview

The demo database is stamped `owner_demo_mode=1`; the normal production launch preflight explicitly rejects that database. After owner approval, production must use a clean database and owner-approved values rather than promoting the demo DB.

Start/stop instructions are in `admin/deploy/owner-demo/OWNER_DEMO.md`. The profile has been prepared and tested locally but **has not yet been installed or started on the Redmi**.

## Redmi / Termux production profile

Dedicated profile:
`admin/deploy/new-gym-termux/`

Loopback-only ports:
- Admin/backend: `127.0.0.1:8897`
- Member gateway: `127.0.0.1:8898`
- Public static website: `127.0.0.1:8899`

Dedicated service names:
- `new-gym-admin`
- `new-gym-member`
- `new-gym-web`
- `new-gym-health`
- `new-gym-notifications`
- `new-gym-tunnel`

Dedicated runtime locations:
- `~/.config/new-gym`
- `~/.local/state/new-gym`
- `~/.local/share/new-gym`

The installer refuses unmanaged service replacement and keeps the Cloudflare tunnel disabled until explicitly enabled. On a clean Termux host it can create the checkout-local Python virtualenv, install the New Gym package with Firebase support, and verify required runtime imports before installing services. Before `--enable-tunnel`, it also requires the local Redmi acceptance gate to prove all core services are running, all three HTTP ports are loopback-only, the tunnel is still down, health endpoints are good, and the public website does not expose admin/API routes. It also runs a fail-closed New Gym preflight before installation, and the stricter launch preflight must pass before `--enable-tunnel` can enable the public tunnel. The launch preflight reads the production SQLite database in read-only mode and rejects stale schema/integrity failures, all three untouched Gravity membership-price signatures, unset pool rates, or missing confirmed kitchen menu/stock data. It also requires a recent off-device backup marker written only after a successful rclone verification.

## Remaining owner-approved data before production deployment

Already known: Need For Strength, The Cue Master, Neemuch address, phone/WhatsApp, Instagram, and the membership/PT prices shown on the supplied opening poster.

Still confirm/replace before production:
- final opening hours
- owner email if required
- final membership rules/inclusions and whether every poster offer remains active
- final private/common The Cue Master hourly rates
- final kitchen menu/prices
- recipes and initial kitchen stock
- new Firebase Auth project
- final public/admin domains
- new Cloudflare Tunnel/token
- dedicated off-device backup destination
- analytics project if required

Never reuse Gravity's Firebase/auth/analytics project or production database.

## Verification

Current verified state:
- Python/JavaScript syntax checks: PASS
- clean migration through `001-019`: PASS
- Pool/Kitchen service + HTTP workflow tests: PASS
- Pool/Kitchen admin UI contract test: PASS
- full admin/backend regression: **249/249 PASS**
- local admin Chromium E2E: **6/6 PASS**
- customer homepage tests: **8/8 PASS**
- customer member-login tests: **9/9 PASS**
- diet planner tests: **PASS**
- member-gateway eligibility tests: **7/7 PASS**
- New Gym Termux isolation tests: PASS
- customer-site scan for Gravity live Firebase/auth/phone/gateway values: CLEAN

Local Chromium E2E has now been run in this isolated copy. Final-domain E2E remains pending until the real New Gym domains, Firebase configuration and tunnel exist.

## Current state

Owner-demo code is prepared and tested, but the ngrok demo has **not yet been started on the Redmi**. Nothing in this repository has been deployed to Gravity Fitness, Vibe4You, or a Need For Strength production host.
