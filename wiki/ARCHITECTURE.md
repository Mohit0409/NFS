# New Gym Architecture

## Isolation

This project is independent from Gravity Fitness and Vibe4You.

Local project root:
`C:\movieXsuggestion\MyProject\new_gym_platform`

Production target:
- Redmi / Termux
- private admin/backend on loopback
- public website on loopback
- member gateway on loopback
- Cloudflare Tunnel as the only intended public/private edge

## Runtime topology

```text
Internet
  |
Cloudflare
  |
New Gym Cloudflare Tunnel
  |
Redmi / Termux
  |-- new-gym-admin   127.0.0.1:8897
  |-- new-gym-member  127.0.0.1:8898
  |-- new-gym-web     127.0.0.1:8899
  |-- new-gym-health
  |-- new-gym-notifications
  `-- new-gym-tunnel
```

## Application modules

### Existing gym-management baseline
- authentication/admin RBAC
- members/staff
- memberships
- fees/payments/receipts
- attendance
- biometric
- enquiries
- follow-ups/notifications
- coaching
- audit/readiness

### Pool
- 1 private table
- 2 common tables
- hourly rates
- timed sessions
- reservations
- overlap protection
- check-in
- session history
- combined pool + kitchen bill
- final settlement

### Kitchen
- menu
- availability
- orders
- pool-linked orders
- order-status workflow
- payment state
- manual stock/inventory
- low-stock threshold
- audited stock movements

## Database

SQLite remains the application database for the Redmi deployment.

New Gym-specific migrations:
- 014 — pool + kitchen base
- 015 — reservations + kitchen inventory
- 016 — combined pool/kitchen payment state

## Customer website

Customer website remains separate from admin UI. It keeps the functional structure of the prior gym website while using a different design and independent configuration.

Primary business config:
`customer-website/web/js/gym-config.js`

No Gravity production Firebase/contact/gateway values are allowed in this file.
