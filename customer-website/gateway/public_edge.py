from __future__ import annotations

import http.client
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

HOST = "127.0.0.1"
PORT = int(os.environ.get("GRAVITY_PUBLIC_EDGE_PORT", "8791"))
MEMBER_TARGET = ("127.0.0.1", int(os.environ.get("GRAVITY_MEMBER_GATEWAY_PORT", "8788")))
ADMIN_PROXY_TARGET = ("127.0.0.1", int(os.environ.get("GRAVITY_ADMIN_PROXY_PORT", "8790")))
HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"}


def _target(path: str) -> tuple[str, int]:
    return MEMBER_TARGET if urlsplit(path).path.startswith("/api/member/") else ADMIN_PROXY_TARGET


class PublicEdge(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "GravityPublicEdge"
    sys_version = ""

    def log_message(self, _fmt: str, *_args) -> None:
        return
    def _proxy(self) -> None:
        host, port = _target(self.path)
        length = int(self.headers.get("Content-Length") or "0")
        body = self.rfile.read(length) if length else None
        headers = {}
        for key, value in self.headers.items():
            if key.lower() in HOP_BY_HOP:
                continue
            if key.lower() == "host":
                headers["Host"] = f"{host}:{port}"
            else:
                headers[key] = value
        headers.setdefault("Host", f"{host}:{port}")
        conn = http.client.HTTPConnection(host, port, timeout=30)
        try:
            conn.request(self.command, self.path, body=body, headers=headers)
            response = conn.getresponse()
            payload = response.read()
            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                if key.lower() in HOP_BY_HOP or key.lower() == "content-length":
                    continue
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload)
        finally:
            conn.close()

    do_GET = _proxy
    do_HEAD = _proxy
    do_POST = _proxy
    do_PUT = _proxy
    do_PATCH = _proxy
    do_DELETE = _proxy
    do_OPTIONS = _proxy


def main() -> None:
    ThreadingHTTPServer((HOST, PORT), PublicEdge).serve_forever()


if __name__ == "__main__":
    main()
