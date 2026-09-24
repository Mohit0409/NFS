# New Gym Jira Register

| ID | Item | Status | Release state |
| --- | --- | --- | --- |
| NG-001 | Isolated New Gym project/repository | DONE | Not deployed |
| NG-002 | Reuse admin portal with New Gym branding | DONE | Not deployed |
| NG-003 | Redesign customer website while preserving functionality | DONE | Not deployed |
| NG-004 | Pool base: 1 private + 2 common tables, timed sessions/rates | DONE | Not deployed |
| NG-005 | Kitchen base: menu/orders/status/payment state | DONE | Not deployed |
| NG-006 | Isolated Redmi/Termux service profile | DONE | Not deployed |
| NG-007 | Pool advance reservations and check-in | DONE | Not deployed |
| NG-008 | Kitchen manual inventory + low-stock tracking | DONE | Not deployed |
| NG-009 | Combined Pool + Kitchen final bill/settlement | DONE | Not deployed |
| NG-010 | Configure real gym name/contact/location/hours | BLOCKED — business data required | Not deployed |
| NG-011 | Configure membership and pool pricing | BLOCKED — business data required | Not deployed |
| NG-012 | Create/configure dedicated New Gym Firebase Auth | BLOCKED — credentials/project required | Not deployed |
| NG-013 | Create/configure dedicated Cloudflare Tunnel/domains | BLOCKED — domain/tunnel required | Not deployed |
| NG-014 | Configure dedicated off-device backups | BLOCKED — backup remote required | Not deployed |
| NG-015 | Browser E2E on final admin/customer origins | TODO | Not deployed |
| NG-016 | Kitchen recipe definitions + automatic ingredient deduction | BACKLOG | Not deployed |
| NG-017 | Pool/Kitchen daily revenue and operational reports | BACKLOG | Not deployed |
| NG-018 | Production deployment to Redmi | BLOCKED by NG-010..015 | Not deployed |

## Current release candidate

Local Git commit:
`7a18718 Add combined pool kitchen settlement`

Verification at this point:
- backend: 223/223 PASS
- customer homepage: 8/8 PASS
- customer member-login: 9/9 PASS
- diet planner: PASS
- member gateway: 7/7 PASS

No production deployment has occurred.
