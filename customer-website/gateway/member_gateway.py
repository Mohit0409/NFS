from __future__ import annotations

from http.cookiejar import CookieJar
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener
import json
import os
import re
import sqlite3
import threading
import time
from pathlib import Path

HOST = "127.0.0.1"
PORT = int(os.environ.get("NEW_GYM_MEMBER_GATEWAY_PORT", "8898"))
BACKEND = os.environ.get("NEW_GYM_MEMBER_BACKEND", "http://127.0.0.1:8897").rstrip("/")
BASE_ALLOWED_ORIGINS = {
    "http://127.0.0.1:8899",
    "http://localhost:8899",
}
EXTRA_ALLOWED_ORIGINS = {
    item.strip() for item in os.environ.get("NEW_GYM_MEMBER_ALLOWED_ORIGINS", "").split(",")
    if item.strip().startswith(("https://", "http://127.0.0.1", "http://localhost"))
}
ALLOWED_ORIGINS = BASE_ALLOWED_ORIGINS | EXTRA_ALLOWED_ORIGINS
MAX_TOKEN_LENGTH = 16_384
UPSTREAM_TIMEOUT = 8
MAX_BODY_LENGTH = 512
PHONE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")
ADMIN_ROOT = Path(os.environ.get("NEW_GYM_ADMIN_ROOT", "").strip() or (Path(__file__).resolve().parents[2] / "admin")).resolve()
MEMBER_DATABASE = Path(
    os.environ.get("NEW_GYM_MEMBER_DATABASE", "").strip()
    or (Path.home() / ".local" / "share" / "new-gym" / "data" / "gravity.sqlite3")
).expanduser().resolve()
ELIGIBILITY_PATH = "/api/member/eligibility"
BOOTSTRAP_PATH = "/api/member/bootstrap"
PUBLIC_KITCHEN_MENU_PATH = "/api/public/kitchen/menu"
PUBLIC_POOL_TABLES_PATH = "/api/public/pool/tables"

def _read_request_json(handler) -> dict:
    try:
        length = int(handler.headers.get("Content-Length") or "0")
    except ValueError:
        return {}
    if length < 1 or length > MAX_BODY_LENGTH:
        return {}
    try:
        value = json.loads(handler.rfile.read(length).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _member_is_eligible(phone: str) -> bool:
    if not PHONE_PATTERN.fullmatch(phone) or not MEMBER_DATABASE.is_file():
        return False
    now = int(time.time())
    connection = sqlite3.connect(str(MEMBER_DATABASE), timeout=2)
    try:
        connection.execute("PRAGMA query_only = ON")
        row = connection.execute(
            "SELECT c.id FROM customers c WHERE c.phone_e164 = ? AND c.status = 'active' "
            "AND c.person_type = 'member' AND c.created_by_admin_user_id IS NOT NULL "
            "AND EXISTS (SELECT 1 FROM memberships m WHERE m.customer_id = c.id "
            "AND m.status IN ('active','scheduled') AND m.starts_at <= ? AND m.ends_at > ?) LIMIT 1",
            (phone, now, now),
        ).fetchone()
        return row is not None
    finally:
        connection.close()


def _customer_is_login_eligible(customer_id: str) -> bool:
    if not customer_id or not MEMBER_DATABASE.is_file():
        return False
    now = int(time.time())
    connection = sqlite3.connect(str(MEMBER_DATABASE), timeout=2)
    try:
        connection.execute("PRAGMA query_only = ON")
        row = connection.execute(
            "SELECT c.id FROM customers c WHERE c.id = ? AND c.status = 'active' "
            "AND c.person_type = 'member' AND c.created_by_admin_user_id IS NOT NULL "
            "AND EXISTS (SELECT 1 FROM memberships m WHERE m.customer_id = c.id "
            "AND m.status IN ('active','scheduled') AND m.starts_at <= ? AND m.ends_at > ?) LIMIT 1",
            (customer_id, now, now),
        ).fetchone()
        return row is not None
    finally:
        connection.close()


def _membership_summary_allows_access(summary: object) -> bool:
    if not isinstance(summary, dict):
        return False
    current = summary.get('current')
    if not isinstance(current, dict) or str(current.get('status') or '').casefold() != 'active':
        return False
    try:
        starts_at = int(current.get('startsAt'))
        ends_at = int(current.get('endsAt'))
    except (TypeError, ValueError):
        return False
    now = int(time.time())
    return starts_at <= now < ends_at


def _public_catalog() -> dict:
    if not MEMBER_DATABASE.is_file():
        raise sqlite3.OperationalError("database unavailable")
    connection = sqlite3.connect(str(MEMBER_DATABASE), timeout=2)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        menu = [
            {
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "pricePaise": int(row["price_paise"]),
            }
            for row in connection.execute(
                "SELECT id,name,category,price_paise FROM kitchen_menu_items "
                "WHERE status='available' ORDER BY category,sort_order,name"
            ).fetchall()
        ]
        tables = [
            {
                "id": row["id"],
                "name": row["name"],
                "tableType": row["table_type"],
                "status": row["status"],
                "ratePaisePerHour": int(row["default_rate_paise"] or 0),
            }
            for row in connection.execute(
                "SELECT id,name,table_type,status,default_rate_paise FROM pool_tables "
                "WHERE status!='disabled' ORDER BY CASE table_type WHEN 'private' THEN 0 ELSE 1 END,name"
            ).fetchall()
        ]
        demo = connection.execute(
            "SELECT value FROM app_metadata WHERE key='owner_demo_mode'"
        ).fetchone()
        return {"menu": menu, "tables": tables, "ownerDemoMode": bool(demo and str(demo["value"]) == "1")}
    finally:
        connection.close()


def _read_json(response) -> dict:
    raw = response.read(1_048_576)
    if not raw:
        return {}
    try:
        value = json.loads(raw.decode("utf-8"))
        return value if isinstance(value, dict) else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _upstream(opener, path: str, *, method: str = "GET", headers=None):
    request_headers = {"Accept": "application/json", "User-Agent": "NewGymMemberGateway/1.0"}
    request_headers.update(headers or {})
    request = Request(BACKEND + path, data=(b"" if method == "POST" else None), method=method, headers=request_headers)
    try:
        with opener.open(request, timeout=UPSTREAM_TIMEOUT) as response:
            return response.status, _read_json(response), dict(response.headers)
    except HTTPError as error:
        return error.code, _read_json(error), dict(error.headers)
    except (URLError, TimeoutError, OSError):
        return 503, {"error": "authentication_unavailable"}, {}



def _logout_async(opener, csrf: str) -> None:
    if not csrf:
        return
    def cleanup() -> None:
        _upstream(opener, "/api/auth/logout", method="POST", headers={"Origin": BACKEND, "X-CSRF-Token": csrf})
    threading.Thread(target=cleanup, name="new-gym-member-logout", daemon=True).start()

def _public_error(status: int, payload: dict):
    code = str(payload.get("error") or "")
    if code in {"account_not_provisioned", "account_disabled", "account_link_required"}:
        return 403, {"error": "member_not_eligible"}
    if code == "rate_limited" or status == 429:
        return 429, {"error": "rate_limited"}
    if code == "invalid_credentials" or status == 401:
        return 401, {"error": "invalid_credentials"}
    return 503, {"error": "authentication_unavailable"}

class MemberGatewayHandler(BaseHTTPRequestHandler):
    server_version = "NewGymMemberGateway"
    sys_version = ""

    def log_message(self, format_string: str, *args) -> None:
        return

    def _origin(self) -> str:
        return (self.headers.get("Origin") or "").strip()

    def _origin_allowed(self) -> bool:
        return self._origin() in ALLOWED_ORIGINS

    def _send_json(self, status: int, payload: dict, *, cors: bool = True) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cors and self._origin_allowed():
            self.send_header("Access-Control-Allow-Origin", self._origin())
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        if self.path not in {ELIGIBILITY_PATH, BOOTSTRAP_PATH} or not self._origin_allowed():
            self._send_json(403, {"error": "origin_not_allowed"}, cors=False)
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self._origin())
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, ngrok-skip-browser-warning")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/api/health":
            status, payload, _ = _upstream(build_opener(), "/api/health")
            healthy = status == 200 and payload.get("status") == "ok" and payload.get("database") == "ok"
            self._send_json(200 if healthy else 503, {"status": "ok" if healthy else "unavailable"}, cors=False)
            return
        if self.path in {PUBLIC_KITCHEN_MENU_PATH, PUBLIC_POOL_TABLES_PATH}:
            try:
                catalog = _public_catalog()
            except sqlite3.Error:
                self._send_json(503, {"error": "catalog_unavailable"}, cors=False)
                return
            if self.path == PUBLIC_KITCHEN_MENU_PATH:
                self._send_json(200, {"items": catalog["menu"], "ownerDemoMode": catalog["ownerDemoMode"]}, cors=False)
            else:
                self._send_json(200, {"tables": catalog["tables"], "ownerDemoMode": catalog["ownerDemoMode"]}, cors=False)
            return
        self._send_json(404, {"error": "not_found"}, cors=False)

    def do_POST(self) -> None:
        if self.path not in {ELIGIBILITY_PATH, BOOTSTRAP_PATH}:
            self._send_json(404, {"error": "not_found"}, cors=False)
            return
        if not self._origin_allowed():
            self._send_json(403, {"error": "origin_not_allowed"}, cors=False)
            return
        if self.path == ELIGIBILITY_PATH:
            payload = _read_request_json(self)
            phone = str(payload.get("phone") or "").strip()
            try:
                eligible = _member_is_eligible(phone)
            except sqlite3.Error:
                self._send_json(503, {"error": "account_unavailable"})
                return
            self._send_json(200, {"eligible": eligible})
            return
        auth = (self.headers.get("Authorization") or "").strip()
        if not auth.startswith("Bearer "):
            self._send_json(401, {"error": "invalid_credentials"})
            return
        token = auth[7:].strip()
        if not 20 <= len(token) <= MAX_TOKEN_LENGTH:
            self._send_json(401, {"error": "invalid_credentials"})
            return

        jar = CookieJar()
        opener = build_opener(HTTPCookieProcessor(jar))
        status, session_payload, _ = _upstream(
            opener,
            "/api/auth/session",
            method="POST",
            headers={"Origin": BACKEND, "Authorization": f"Bearer {token}"},
        )
        if status != 200 or not session_payload.get("authenticated"):
            public_status, public_payload = _public_error(status, session_payload)
            self._send_json(public_status, public_payload)
            return

        csrf = str(session_payload.get("csrfToken") or "")
        try:
            user = session_payload.get("user", {})
            if not isinstance(user, dict) or not user.get("id"):
                me_status, me_payload, _ = _upstream(opener, "/api/me")
                if me_status != 200:
                    self._send_json(503, {"error": "account_unavailable"})
                    return
                user = me_payload.get("user", {})
            customer_id = str(user.get("id") or "") if isinstance(user, dict) else ""
            try:
                login_eligible = _customer_is_login_eligible(customer_id)
            except sqlite3.Error:
                self._send_json(503, {"error": "account_unavailable"})
                return
            if not login_eligible:
                self._send_json(403, {"error": "member_not_eligible"})
                return
            membership_status, membership_payload, _ = _upstream(opener, "/api/me/membership")
            if membership_status != 200:
                self._send_json(503, {"error": "account_unavailable"})
                return
            membership_summary = membership_payload.get("membership", {})
            if not _membership_summary_allows_access(membership_summary):
                self._send_json(403, {"error": "member_not_eligible"})
                return
            self._send_json(200, {
                "authenticated": True,
                "user": user,
                "membership": membership_summary,
            })
        finally:
            _logout_async(opener, csrf)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), MemberGatewayHandler)
    print(f"Need For Strength member gateway listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

