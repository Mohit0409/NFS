# New Gym Platform

Separate build derived from the proven Gravity Fitness application structure.

## Safety boundary

This project is isolated at:

`C:\movieXsuggestion\MyProject\new_gym_platform`

The live Gravity Fitness projects, databases, Firebase projects, phone number, analytics configuration, public gateway and deployment state are not used by this copy.

## Structure

- `admin/` — copied Gravity admin/backend baseline, with New Gym branding and new Pool + Kitchen modules.
- `customer-website/` — copied customer website functionality with a visually different theme and independent configuration placeholders.

## Admin status

Existing gym functionality is preserved:
- member/staff directory
- memberships and plan management
- fees/payments/receipts
- attendance
- biometric device support
- enquiries
- follow-ups/notifications
- coaching
- team access
- audit/readiness

New modules:
- Pool workspace
  - Private Table
  - Common Table 1
  - Common Table 2
  - configurable hourly rate per table
  - start/end timed sessions
  - server-calculated session duration and charge
  - recent session history
- Kitchen workspace
  - menu items/categories/prices
  - available/unavailable state
  - walk-in or pool-session-linked orders
  - quantity and historical price snapshots
  - order workflow: new -> preparing -> ready -> served
  - payment state

Database migration:
- `014_pool_kitchen.sql`

Brand:
- backend default: `BUSINESS_NAME=New Gym`
- admin login/header/sidebar automatically read the business name from `/api/health`

## Customer website status

Functionality retained:
- membership information
- BMI calculator
- Indian diet planner
- exercise library
- member login UI
- enquiry UI

Visual identity changed from Gravity's dark performance theme to:
- warm light background
- deep navy typography
- coral/orange accent
- softer rounded cards
- club/lounge style presentation

Main theme:
- `customer-website/web/css/new-gym-theme.css`

Customer configuration:
- `customer-website/web/js/gym-config.js`

Gravity live Firebase/auth/analytics/contact endpoints were removed from this copy. Member login and analytics intentionally remain disabled until the new gym receives its own configuration.

## Required business details before deployment

Configure:
- real gym name
- city
- address
- phone
- WhatsApp number
- Instagram URL
- opening hours
- membership pricing
- pool private/common hourly rates
- kitchen menu and prices
- new Firebase Auth project
- customer member gateway/public URL
- analytics project if analytics is required

Do not reuse Gravity's Firebase/auth/analytics project or production database.

## Verification completed

- Python/JS syntax checks: PASS
- Migration 001-014 on clean DB: PASS
- Pool/Kitchen focused tests: 4/4 PASS
- Previously failing compatibility tests after migration 014 update: 6/6 PASS
- Full backend regression: 214/214 PASS
- Customer site scan for Gravity Firebase project, old phone, old public Firebase host and old ngrok gateway: CLEAN

Browser E2E was not run in this isolated archive copy because `node_modules` was intentionally not copied from the Gravity workspace.

## Current state

Development only. Nothing from this project has been deployed to Gravity or to a new production host.
