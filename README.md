# New Gym Platform

Independent gym platform built from the proven Gravity Fitness application structure.

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

### Pool

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

Latest schema migration: `017`.

## Branding

- Backend default: `BUSINESS_NAME=New Gym`
- Admin login/header/sidebar derive the display name from backend health/config.
- Internal `server.gravity` / `GRAVITY_*` names remain for copied-code compatibility; OS-level services/config directories are New Gym-specific.

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
- business config: `customer-website/web/js/gym-config.js`
- runtime renderer: `customer-website/web/js/runtime-config.js`

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

Unknown business details remain explicit placeholders. Gravity's live customer endpoints/configuration are not inherited.

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

The installer refuses unmanaged service replacement and keeps the Cloudflare tunnel disabled until explicitly enabled. It also runs a fail-closed New Gym preflight before installation, and the stricter launch preflight must pass before `--enable-tunnel` can enable the public tunnel.

## Required real business data before deployment

Configure:
- real gym name
- city/address
- phone/WhatsApp
- Instagram
- opening hours
- membership prices
- private/common pool rates
- kitchen menu
- initial kitchen stock
- new Firebase Auth project
- final public/admin domains
- new Cloudflare Tunnel/token
- dedicated off-device backup destination
- analytics project if required

Never reuse Gravity's Firebase/auth/analytics project or production database.

## Verification

Current verified state:
- Python/JavaScript syntax checks: PASS
- clean migration through `001-017`: PASS
- Pool/Kitchen service + HTTP workflow tests: PASS
- Pool/Kitchen admin UI contract test: PASS
- full admin/backend regression: **232/232 PASS**
- local admin Chromium E2E: **6/6 PASS**
- customer homepage tests: **8/8 PASS**
- customer member-login tests: **9/9 PASS**
- diet planner tests: **PASS**
- member-gateway eligibility tests: **7/7 PASS**
- New Gym Termux isolation tests: PASS
- customer-site scan for Gravity live Firebase/auth/phone/gateway values: CLEAN

Local Chromium E2E has now been run in this isolated copy. Final-domain E2E remains pending until the real New Gym domains, Firebase configuration and tunnel exist.

## Current state

Development only. Nothing in this repository has been deployed to Gravity Fitness or to a New Gym production host.
