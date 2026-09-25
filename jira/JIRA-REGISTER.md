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
| NG-030 | Need For Strength owner preview via isolated single-URL ngrok profile | DONE — prepared/tested; not started on Redmi | Demo not deployed |
| NG-031 | Replace owner-demo database/data with clean owner-approved production data | BLOCKED — owner approval required | Not deployed |
| NG-032 | Guarded PC-to-Redmi owner-demo deployment launcher | DONE — exact-commit archive + SHA-256 + shared standalone bootstrap | Not deployed |
| NG-033 | Start owner-demo on Redmi and capture ngrok owner links | IN PROGRESS — first bootstrap blocked before extraction by Termux temp-path assumption; corrected package being restaged | Demo not deployed |
| NG-034 | Preserve existing Redmi ngrok command_line tunnel during owner demo | DONE — reuse existing agent; only nfs-owner-demo may be created/deleted | Not deployed |
| NG-035 | Remove Linux /tmp assumption from Redmi owner-demo USB tooling | DONE — use Termux TMPDIR/PREFIX tmp; regression guard added | Not deployed |

## Current release candidate

Owner-demo runtime commit:
`c77b299 Fix Termux owner demo temp paths`

Verification at this point:
- backend: 249/249 PASS
- local admin Chromium: 6/6 PASS
- customer homepage: 8/8 PASS
- customer member-login: 9/9 PASS
- diet planner: PASS
- member gateway: 7/7 PASS

No production deployment has occurred.
