# Need For Strength Jira Register

| ID | Item | Status | Release state |
| --- | --- | --- | --- |
| NG-001 | Isolated New Gym project/repository | DONE | Not deployed |
| NG-002 | Reuse admin portal with Need For Strength branding | DONE | Not deployed |
| NG-003 | Redesign customer website while preserving functionality | DONE | Not deployed |
| NG-004 | Pool base: 1 private + 2 common tables, timed sessions/rates | DONE | Not deployed |
| NG-005 | Kitchen base: menu/orders/status/payment state | DONE | Not deployed |
| NG-006 | Isolated Redmi/Termux service profile | DONE | Not deployed |
| NG-007 | Pool advance reservations and check-in | DONE | Not deployed |
| NG-008 | Kitchen manual inventory + low-stock tracking | DONE | Not deployed |
| NG-009 | Combined Pool + Kitchen final bill/settlement | DONE | Not deployed |
| NG-010 | Configure real gym identity/contact/location/hours | IN PROGRESS — Need For Strength, address, phone/WhatsApp and Instagram captured; owner-demo hours are temporary | Not deployed |
| NG-011 | Configure membership and pool pricing | IN PROGRESS — poster membership/PT prices captured for owner demo; The Cue Master ₹300/₹200 hourly rates are DEMO ONLY pending owner approval | Not deployed |
| NG-012 | Create/configure dedicated New Gym Firebase Auth | BLOCKED — credentials/project required | Not deployed |
| NG-013 | Create/configure dedicated Cloudflare Tunnel/domains | BLOCKED — domain/tunnel required | Not deployed |
| NG-014 | Configure dedicated off-device backups | BLOCKED — backup remote required | Not deployed |
| NG-015 | Browser E2E on final admin/customer origins | IN PROGRESS — local admin Chromium 6/6 PASS; final-origin run still required | Not deployed |
| NG-016 | Kitchen recipe definitions + automatic ingredient deduction | DONE | Not deployed |
| NG-017 | Pool/Kitchen daily revenue and operational reports | DONE | Not deployed |
| NG-018 | Production deployment to Redmi | BLOCKED by NG-010..015 | Not deployed |
| NG-019 | Remove copied Gravity Firebase default aliases and add regression guard | DONE | Not deployed |
| NG-020 | Fail-closed Redmi install/launch preflight with explicit pricing/rate/kitchen confirmation gates | DONE | Not deployed |
| NG-021 | Database-aware launch gate for schema/integrity/legacy Gravity pricing/pool rates/kitchen live data | DONE | Not deployed |
| NG-022 | Fresh verified off-device backup marker required before tunnel enable | DONE | Not deployed |
| NG-023 | Audited kitchen order cancellation with required reason and safe payment/stock behavior | DONE | Not deployed |
| NG-024 | Edit/reschedule upcoming pool reservations with overlap revalidation | DONE | Not deployed |
| NG-025 | Audited standalone Kitchen payment void with pool-bill accounting safeguards | DONE | Not deployed |
| NG-026 | Clean-Termux Python runtime/virtualenv dependency automation | DONE | Not deployed |
| NG-027 | Local Redmi acceptance gate before Cloudflare tunnel enable | DONE | Not deployed |
| NG-028 | Generate versioned customer runtime config from protected env + live membership DB | DONE | Not deployed |
| NG-029 | Manifest-verified customer-site release rollback | DONE | Not deployed |
| NG-030 | Need For Strength owner preview via isolated Cloudflare Quick Tunnel | DONE — live on Redmi; staging only | Demo deployed |
| NG-031 | Replace owner-demo database/data with clean owner-approved production data | BLOCKED — owner approval required | Not deployed |
| NG-032 | Guarded PC-to-Redmi owner-demo deployment launcher | DONE — exact-commit archive + SHA-256 + shared standalone bootstrap | Not deployed |
| NG-033 | Start owner-demo on Redmi and capture owner links | DONE — live release `e7ba8b9`; Cloudflare Quick Tunnel health accepted | Demo deployed |
| NG-034 | Preserve Universal Gym ngrok while isolating Need For Strength ingress | DONE — Need For Strength uses Cloudflare; stale nfs-owner-demo ngrok endpoint removed without changing command_line | Demo deployed |
| NG-035 | Remove Linux /tmp assumption from Redmi owner-demo USB tooling | DONE — use Termux TMPDIR/PREFIX tmp; regression guard added | Demo deployed |
| NG-036 | Remove copied New Gym fallback branding from customer/admin surfaces | DONE — regression guarded in `c2a047b` | Commercial candidate |
| NG-037 | Make production admin hostname admin-only and block copied legacy public pages | DONE — root redirects to /admin, legacy public pages/sitemap denied, robots disallow all | Commercial candidate |
| NG-038 | Add Need For Strength Privacy/Terms pages and legal-review launch gate | DONE — production launch requires explicit legal review confirmation | Commercial candidate |
| NG-039 | Supply final commercial configuration: hours, approved prices/rates/menu, dedicated Firebase, named Cloudflare tunnel and off-device backup | BLOCKED — owner/external inputs required | Not deployed |
| NG-040 | Final-domain production browser/cutover acceptance on exact release | BLOCKED by NG-039 | Not deployed |
| NG-041 | Add prominent BCA body-composition feature to customer website | DONE — customer section + dedicated AI visual + safety copy | Pending owner-demo deploy |
| NG-042 | Publish live kitchen catalog on a separate customer page | DONE — read-only catalog endpoint + dynamic menu page | Pending owner-demo deploy |
| NG-043 | Publish The Cue Master three-table page with reservation-request flow | DONE — 1 private + 2 common, live rates/status, WhatsApp confirmation request | Pending owner-demo deploy |
| NG-044 | Replace copied Gravity customer imagery with original Need For Strength AI imagery | DONE — old copied image assets removed and four NFS assets wired | Pending owner-demo deploy |

## Current release candidates

Commercial-hardening implementation:
`c2a047bb1a7a32fc719dbd868c893cb9a1dad866`

Live owner-demo runtime:
`e7ba8b9f847a606723724162b808760b09f52fbf`

The `c2a047b` owner-demo archive is SHA-256 staged on the Redmi but has not replaced the live demo runtime yet.

Verification for `c2a047b`:
- backend: 251/251 PASS
- full Chromium release suite: 63/63 PASS
- customer homepage: 10/10 PASS
- customer member-login: 9/9 PASS
- diet planner: PASS
- member gateway: 7/7 PASS
- Python/JavaScript/shell syntax: PASS
- git diff check: PASS

No Need For Strength production deployment has occurred.
