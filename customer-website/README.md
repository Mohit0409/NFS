# New Gym Customer Website

Independent public/customer website for the New Gym project.

This copy keeps the proven Gravity customer-site functionality but has:
- separate branding
- a different visual theme
- no Gravity live Firebase/auth/analytics/contact configuration
- its own New Gym member-gateway environment variables
- configuration-driven business details and membership prices

## Configuration

Edit:

`web/js/gym-config.js`

It controls the public gym name, city, phone, WhatsApp, address, hours, Instagram, map, membership prices, member gateway, Firebase Auth and analytics configuration.

Unknown values should stay blank. The UI intentionally shows safe placeholders instead of inheriting Gravity business data.

## Local preview

From this folder:

```powershell
python -m http.server 8899 --bind 127.0.0.1 --directory web
```

Open:

`http://127.0.0.1:8899/`

## Member gateway

`gateway/member_gateway.py` defaults to:
- gateway: `127.0.0.1:8898`
- backend: `http://127.0.0.1:8897`

Production allowed origins must be supplied through `NEW_GYM_MEMBER_ALLOWED_ORIGINS`.

The member login remains fail-closed until the New Gym Firebase project and final gateway origin are configured.

## Verification

- Homepage tests: 8/8 PASS
- Member-login tests: 9/9 PASS
- Diet planner tests: PASS
- Member gateway tests: 7/7 PASS
- JavaScript syntax checks: PASS

## Deployment

Use the project-level Redmi/Termux profile under:

`..\admin\deploy\new-gym-termux\`

Do not deploy this project with Gravity's Firebase project, Gravity's tunnel token, or Gravity's database.
