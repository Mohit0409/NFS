# Gravity Fitness Customer Website

Independent public/customer website for Gravity Fitness, Neemuch.

Repository: https://github.com/Mohit0409/gravity-fitness-website

This repository is deliberately separate from the protected Gravity Fitness Admin Portal. The public-site work must never be developed, committed or deployed from the Admin repository.

## Recovery provenance

- Live source snapshot: https://gravityfitnessnmh.web.app/
- Recovered on: 2026-08-30
- Nearest known historical source commit: `3575a4fde75930fc87d90b887a31bb54f2b0d9eb`
- Historical commit subject: `chore: establish Gravity backend foundation`

The deployed homepage was not byte-identical to any single `web/index.html` revision in the protected Admin repository. The checkpoint therefore preserves the public files served by Firebase Hosting, with `.firebaserc` and `firebase.json` recovered from the historical commit above.

This repository is independent from the Gravity Fitness Admin Portal. It must not contain Admin source, private customer data, databases, service-account files, payment secrets, or private environment files.

The immutable original-site checkpoint is preserved by:

- Commit: `a843ffcd33c2e899fa8fa380d63630dcfb0a1464`
- Annotated tag: `website-original-firebase-checkpoint`

## Public-site redesign

Development is isolated on `redesign/info-enquiry-only`.

- All customer-facing payment and purchase actions are removed.
- Membership, training and nutrition content is informational and enquiry-only.
- The previous classes, motivation, transformation, testimonial and free-pass sections are removed.
- The nutrition section adapts the Admin Portal's diet concepts without moving or modifying Admin code.
- `Gravity Smart Diet` provides a browser-only Indian fitness diet starting plan from age, sex, weight, height, activity, goal, diet preference, meal frequency, workout timing and daily food budget.
- The planner uses deterministic calculations, a curated Indian meal library, conservative safety exclusions and approximate food costs. It is general fitness guidance, not clinical nutrition or an AI dietitian.
- The recovered interactive 3D athlete and its click/tap action remain available on the homepage.
- Gallery and training pages use neutral, verifiable language rather than invented people, results, prices or schedules.

## Member login integration

`web/pages/member-login.html` contains a mobile-number and OTP-only member experience. It intentionally has no password, email or public registration flow. The client expects same-origin, cookie-session endpoints:

- `POST /api/auth/phone/start`
- `POST /api/auth/phone/verify`
- `GET /api/auth/session`
- `GET /api/me`
- `GET /api/me/membership`
- `POST /api/auth/logout`

The start endpoint must perform the active-customer eligibility check before sending an OTP, return an opaque challenge, use generic enumeration-safe responses, and enforce rate limits. The verify endpoint must create a secure HTTP-only cookie session. Account endpoints must derive the customer identity from that session and return only the signed-in member's data.

These required public member-auth endpoints are not present in the currently protected Admin backend. The frontend therefore fails closed and shows a temporary-unavailable message; it must not be described as a working login until the independent backend contract is implemented and security-tested.

## Local preview

Serve the `web` directory with any static HTTP server. For example:

```powershell
python -m http.server 8080 --directory web
```

Then open `http://127.0.0.1:8080/`.

Useful routes:

- `/index.html`
- `/pages/gallery.html`
- `/pages/trainers.html`
- `/pages/member-login.html`
- `/pages/diet-planner.html`

## Diet-planner verification

Run the deterministic calculator checks with:

```powershell
node diet-planner.test.cjs
```

The recipe nutrition and price values are planning estimates and must be reviewed periodically against qualified nutrition guidance and current Neemuch ingredient prices. The repository does not bulk-copy the Indian Food Composition Tables.

## Deployment

Firebase deployment is intentionally not performed until the owner explicitly approves it. Do not deploy the member-login route until its same-origin backend endpoints and hosting/API routing are available.
