#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
import json
import os
import time

KEYS = ("APP_BASE_URL", "NEW_GYM_PUBLIC_SITE_URL", "NEW_GYM_MEMBER_ALLOWED_ORIGINS")


def _matches_edge(addr: str, edge_port: int) -> bool:
    try:
        parsed = urlsplit(addr if "://" in addr else f"http://{addr}")
        return parsed.hostname in {"127.0.0.1", "localhost"} and parsed.port == edge_port
    except (TypeError, ValueError):
        return False


def discover(api_url: str, edge_port: int, *, tunnel_name: str = "nfs-owner-demo", attempts: int = 30) -> str:
    for _ in range(attempts):
        try:
            with urlopen(api_url, timeout=2) as response:
                payload = json.load(response)
            for tunnel in payload.get("tunnels", []):
                if str(tunnel.get("name") or "") != tunnel_name:
                    continue
                public_url = str(tunnel.get("public_url") or "").rstrip("/")
                addr = str((tunnel.get("config") or {}).get("addr") or "")
                if public_url.startswith("https://") and _matches_edge(addr, edge_port):
                    return public_url
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"ngrok HTTPS tunnel {tunnel_name!r} was not discovered on edge port {edge_port}")


def validate_public_url(public_url: str) -> str:
    value = public_url.strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("owner-demo public URL must be an absolute HTTPS origin")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("owner-demo public URL must not include path/query/fragment")
    return value


def update_env(path: Path, public_url: str) -> None:
    public_url = validate_public_url(public_url)
    values = {
        "APP_BASE_URL": public_url,
        "NEW_GYM_PUBLIC_SITE_URL": public_url,
        "NEW_GYM_MEMBER_ALLOWED_ORIGINS": public_url,
    }
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        if "=" not in line or line.lstrip().startswith("#"):
            output.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in values:
            output.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            output.append(line)
    for key in KEYS:
        if key not in seen:
            output.append(f"{key}={values[key]}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(output) + "\n", encoding="utf-8")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    temporary.replace(path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def main() -> int:
    parser = ArgumentParser(description="Sync the exact Need For Strength owner-demo ngrok URL into protected demo env.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--api", default="http://127.0.0.1:4040/api/tunnels")
    parser.add_argument("--edge-port", type=int, default=8900)
    parser.add_argument("--tunnel-name", default="nfs-owner-demo")
    parser.add_argument("--public-url")
    args = parser.parse_args()

    public_url = validate_public_url(args.public_url) if args.public_url else discover(
        args.api, args.edge_port, tunnel_name=args.tunnel_name
    )
    update_env(Path(args.config).expanduser(), public_url)
    print(json.dumps({"ready": True, "publicUrl": public_url, "tunnelName": args.tunnel_name}, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
