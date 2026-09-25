# Need For Strength Commercial Readiness

Status: **CODE HARDENED / PRODUCTION INPUTS STILL BLOCKING LAUNCH**

This document separates completed product engineering from business/external items that must be supplied before production traffic is accepted.

## Commercially hardened in code

- Need For Strength branding is now the fallback across the customer and admin surfaces; copied "New Gym" fallback text is regression-tested out.
- The production admin hostname is admin-only when `ADMIN_PORTAL_ROOT_REDIRECT=true`: legacy copied public pages such as account, coaching, gallery, trainers and privacy are not served there.
- Admin-only `robots.txt` disallows crawling and `sitemap.xml` is not exposed.
- Public customer site includes Privacy Notice and Terms of Use pages.
- Production launch now requires `NEW_GYM_LEGAL_REVIEW_CONFIRMED=true`.
- Existing launch gates still require a clean non-demo database, current schema/integrity, active real membership plans, all three pool rates, kitchen menu/inventory/recipes, final HTTPS origins, dedicated Firebase, dedicated Cloudflare tunnel token and a fresh verified off-device backup.
- Owner-demo data remains stamped `owner_demo_mode=1` and is rejected by production launch.
- Pool/Kitchen reservations, timers, combined billing, payment state, inventory, recipes, cancellation/void auditing and daily reporting are implemented.
- Admin authentication, RBAC, audit trail, member/staff separation, payments/fees, attendance, coaching and readiness remain in place.

## Production inputs still required

1. Final opening hours.
2. Owner approval of every membership/PT offer that will remain active.
3. Owner approval of The Cue Master private/common hourly rates.
4. Final kitchen menu, selling prices, recipes and opening stock.
5. Dedicated Need For Strength Firebase Auth project + service account.
6. Stable production customer/admin domains and a dedicated named Cloudflare Tunnel.
7. Dedicated off-device backup destination and a fresh verified backup marker.
8. Owner/legal review of Privacy Notice and Terms of Use.
9. Final-domain browser E2E and public HTTPS smoke on the exact production domains.
10. Production owner credentials/TOTP recovery material created only after the final production SECRET_KEY is installed.

## Launch rule

The Cloudflare Quick Tunnel used by the owner demo is **staging only**. It must not be treated as the commercial domain.

Do not set any confirmation flag to true merely to satisfy preflight. Each flag records an owner-reviewed real value.

Production is GO only when the New Gym/Need For Strength production preflight, local Redmi acceptance, off-device backup verification and final-domain browser checks all pass on one exact release commit.

## Isolation rule

Never promote the owner-demo database or config into production. Build the production database/config under the dedicated `~/.config/new-gym`, `~/.local/state/new-gym` and `~/.local/share/new-gym` paths. Do not reuse Universal Gym, LocalStoreTrack, Vibe4You or Gravity Fitness tunnels, databases, ports or credentials.
