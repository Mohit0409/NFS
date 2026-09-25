#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from urllib.request import urlopen
import json
import os
import time


KEYS = ("APP_BASE_URL", "NEW_GYM_PUBLIC_SITE_URL", "NEW_GYM_MEMBER_ALLOWED_ORIGINS")


def discover(api_url: str, edge_port: int, *, attempts: int = 30) -> str:
    for _ in range(attempts):
        try:
            with urlopen(api_url, timeout=2) as response:
                payload = json.load(response)
            for tunnel in payload.get("tunnels", []):
                public_url = str(tunnel.get("public_url") or "")
                config = tunnel.get("config") or {}
                addr = str(config.get("addr") or "")
                if public_url.startswith("https://") and (
                    addr.endswith(f":{edge_port}") or addr.endswith(str(edge_port))
                ):
                    return public_url.rstrip("/")
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("ngrok HTTPS tunnel was not discovered")


def update_env(path: Path, public_url: str) -> None:
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
    parser = ArgumentParser(description="Sync current ngrok owner-demo URL into the protected demo env.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--api", default="http://127.0.0.1:4040/api/tunnels")
    parser.add_argument("--edge-port", type=int, default=8900)
    args = parser.parse_args()

    public_url = discover(args.api, args.edge_port)
    update_env(Path(args.config).expanduser(), public_url)
    print(json.dumps({"ready": True, "publicUrl": public_url}, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
