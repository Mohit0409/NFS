#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import subprocess
import sys


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def http_probe(url: str, *, expected_status: int = 200, json_require: dict[str, object] | None = None) -> tuple[bool, str]:
    request = Request(url, headers={"User-Agent": "NewGymAcceptance/1.0"})
    try:
        with urlopen(request, timeout=5) as response:
            status = int(response.status)
            body = response.read(1024 * 1024)
    except HTTPError as error:
        status = int(error.code)
        body = error.read(1024 * 1024)
    except (URLError, TimeoutError, OSError) as error:
        return False, f"request failed: {type(error).__name__}"

    if status != expected_status:
        return False, f"expected HTTP {expected_status}, got {status}"
    if json_require is not None:
        try:
            payload = json.loads(body or b"{}")
        except (ValueError, TypeError):
            return False, "response was not valid JSON"
        for key, expected in json_require.items():
            if payload.get(key) != expected:
                return False, f"JSON field {key!r} did not match"
    return True, f"HTTP {status}"


def parse_ss_listeners(text: str, ports: set[int]) -> dict[int, set[str]]:
    result = {port: set() for port in ports}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        local = ""
        if len(parts) >= 4:
            local = parts[3]
        elif parts:
            local = parts[-1]
        for port in ports:
            suffix = f":{port}"
            if local.endswith(suffix):
                result[port].add(local[: -len(suffix)] or "*")
    return result


def listener_is_loopback(addresses: set[str]) -> bool:
    if not addresses:
        return False
    normalized = {item.strip("[]") for item in addresses}
    forbidden = {"0.0.0.0", "::", "*", ""}
    if normalized & forbidden:
        return False
    return all(item in {"127.0.0.1", "::1"} for item in normalized)


def service_status(command_runner=subprocess.run) -> tuple[dict[str, bool], str]:
    services = (
        "new-gym-admin",
        "new-gym-member",
        "new-gym-web",
        "new-gym-health",
        "new-gym-notifications",
    )
    result = command_runner(
        ["sv", "status", *services],
        check=False,
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    lines = output.splitlines()
    states: dict[str, bool] = {}
    for service in services:
        states[service] = any(
            line.startswith("run:") and (f"/{service}:" in line or service in line)
            for line in lines
        )
    return states, output


def tunnel_is_down(command_runner=subprocess.run) -> tuple[bool, str]:
    result = command_runner(
        ["sv", "status", "new-gym-tunnel"],
        check=False,
        capture_output=True,
        text=True,
    )
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    return output.startswith("down:"), output


def run_acceptance(
    values: dict[str, str],
    *,
    command_runner=subprocess.run,
    probe=http_probe,
) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    blockers: list[str] = []

    def check(code: str, ok: bool, detail: str) -> None:
        checks.append({"code": code, "ok": bool(ok), "detail": detail})
        if not ok:
            blockers.append(code)

    try:
        admin_port = int(values.get("GRAVITY_PORT", "8897"))
        member_port = int(values.get("NEW_GYM_MEMBER_GATEWAY_PORT", "8898"))
        public_port = int(values.get("NEW_GYM_PUBLIC_PORT", "8899"))
        ports = {admin_port, member_port, public_port}
        ports_valid = len(ports) == 3 and all(1024 <= port <= 65535 for port in ports)
    except ValueError:
        admin_port = member_port = public_port = 0
        ports = set()
        ports_valid = False
    check("ports", ports_valid, "Admin/member/public ports must be distinct valid high ports")
    if not ports_valid:
        return {"ready": False, "blockers": blockers, "checks": checks}

    states, _status_output = service_status(command_runner)
    check(
        "services_running",
        all(states.values()),
        "Admin, member, web, health and notification services must all be running",
    )

    tunnel_down, _tunnel_output = tunnel_is_down(command_runner)
    check(
        "tunnel_disabled",
        tunnel_down,
        "Cloudflare tunnel must remain down during local acceptance",
    )

    ss_result = command_runner(
        ["ss", "-ltnH"],
        check=False,
        capture_output=True,
        text=True,
    )
    listeners = parse_ss_listeners(ss_result.stdout or "", ports)
    for code, port in (
        ("admin_loopback_listener", admin_port),
        ("member_loopback_listener", member_port),
        ("public_loopback_listener", public_port),
    ):
        check(
            code,
            listener_is_loopback(listeners.get(port, set())),
            f"Port {port} must listen only on loopback",
        )

    ok, detail = probe(
        f"http://127.0.0.1:{admin_port}/api/health",
        json_require={"status": "ok", "database": "ok"},
    )
    check("admin_health", ok, detail)

    ok, detail = probe(
        f"http://127.0.0.1:{member_port}/api/health",
        json_require={"status": "ok"},
    )
    check("member_health", ok, detail)

    ok, detail = probe(f"http://127.0.0.1:{public_port}/")
    check("public_site", ok, detail)

    ok, detail = probe(
        f"http://127.0.0.1:{public_port}/admin",
        expected_status=404,
    )
    check("public_admin_isolation", ok, detail)

    ok, detail = probe(
        f"http://127.0.0.1:{public_port}/api/admin/session",
        expected_status=404,
    )
    check("public_api_isolation", ok, detail)

    return {
        "ready": not blockers,
        "blockers": blockers,
        "checks": checks,
    }


def main() -> int:
    parser = ArgumentParser(description="Local acceptance gate for the isolated New Gym Redmi deployment.")
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "--skip-launch-preflight",
        action="store_true",
        help="Run local service checks without the stricter production launch preflight.",
    )
    args = parser.parse_args()

    config = Path(args.config).expanduser()
    if not config.is_file():
        print(json.dumps({"ready": False, "blockers": ["config_missing"], "checks": []}))
        return 2

    repo = Path(__file__).resolve().parents[2]
    if not args.skip_launch_preflight:
        preflight = subprocess.run(
            [
                sys.executable,
                str(repo / "deploy" / "new-gym-termux" / "preflight-new-gym.py"),
                "--config",
                str(config),
                "--stage",
                "launch",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if preflight.returncode != 0:
            try:
                result = json.loads(preflight.stdout or "{}")
            except ValueError:
                result = {"ready": False, "blockers": ["launch_preflight_failed"], "checks": []}
            result["acceptanceStage"] = "launch_preflight"
            print(json.dumps(result, separators=(",", ":"), sort_keys=True))
            return 2

    result = run_acceptance(load_env(config))
    result["acceptanceStage"] = "local_services"
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
