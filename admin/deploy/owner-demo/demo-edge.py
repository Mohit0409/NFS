#!/usr/bin/env python3
from __future__ import annotations

from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import os

HOST = "127.0.0.1"
PORT = int(os.environ.get("NFS_DEMO_EDGE_PORT", "8900"))
ADMIN_PORT = int(os.environ.get("GRAVITY_PORT", "8897"))
MEMBER_PORT = int(os.environ.get("NEW_GYM_MEMBER_GATEWAY_PORT", "8898"))
PUBLIC_PORT = int(os.environ.get("NEW_GYM_PUBLIC_PORT", "8899"))

HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def target_port(path: str) -> int:
    if path.startswith("/api/member/") or path.startswith("/api/public/"):
        return MEMBER_PORT
    if (
        path == "/admin"
        or path.startswith("/admin/")
        or path.startswith("/api/admin/")
        or path == "/api/health"
        or path == "/css/admin.css"
        or path.startswith("/js/admin")
        or path.startswith("/assets/icons/")
    ):
        return ADMIN_PORT
    return PUBLIC_PORT


class Handler(BaseHTTPRequestHandler):
    server_version = "NeedForStrengthOwnerDemo/1.0"

    def _proxy(self) -> None:
        parsed = urlsplit(self.path)
        port = target_port(parsed.path)
        length = int(self.headers.get("Content-Length") or "0")
        body = self.rfile.read(length) if length else None

        headers: dict[str, str] = {}
        for key, value in self.headers.items():
            if key.lower() in HOP_HEADERS or key.lower() == "host":
                continue
            headers[key] = value
        headers["Host"] = f"127.0.0.1:{port}"
        headers["X-Forwarded-Host"] = self.headers.get("Host", "")
        headers["X-Forwarded-Proto"] = self.headers.get("X-Forwarded-Proto", "https")
        headers["X-Forwarded-For"] = self.client_address[0]

        connection = HTTPConnection("127.0.0.1", port, timeout=15)
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            payload = response.read()
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() in HOP_HEADERS or key.lower() == "content-length":
                    continue
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload)
        except OSError:
            payload = b'{"error":"demo_upstream_unavailable"}'
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload)
        finally:
            connection.close()

    do_GET = _proxy
    do_HEAD = _proxy
    do_POST = _proxy
    do_PATCH = _proxy
    do_PUT = _proxy
    do_DELETE = _proxy
    do_OPTIONS = _proxy

    def log_message(self, fmt: str, *args) -> None:
        return


def main() -> int:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Need For Strength owner-demo edge listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
