# Cloudflare routing for the New Gym Redmi server

Use a **new Cloudflare Tunnel**, separate from Gravity and Vibe4You.

Recommended routes:

| Public hostname/path | Redmi target |
| --- | --- |
| private admin hostname, all paths | http://127.0.0.1:8897 |
| public customer hostname, `/api/member/*` | http://127.0.0.1:8898 |
| public customer hostname, `/api/public/*` | http://127.0.0.1:8898 |
| public customer hostname, all other paths | http://127.0.0.1:8899 |

Important:

- Do not expose ports 8897, 8898 or 8899 directly on the LAN/WAN.
- Keep all three services bound to `127.0.0.1`.
- Restrict the admin hostname with Cloudflare Access to the owner/admin identities.
- The public hostname may remain public; only `/api/member/*` and read-only `/api/public/*` catalog paths should reach port 8898.
- Use a new tunnel token stored at `~/.config/new-gym/cloudflared-token` with mode `600`.
- Set `NEW_GYM_MEMBER_ALLOWED_ORIGINS` to the final public HTTPS customer origin.
- Set `APP_BASE_URL` to the final private HTTPS admin origin.
