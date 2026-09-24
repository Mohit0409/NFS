#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import sqlite3
import sys
import time


TRUTHY = {"1", "true", "yes", "on"}
PLACEHOLDER_HOSTS = {"admin.new-gym.example", "www.new-gym.example", "new-gym.example"}
GRAVITY_MARKERS = (
    "gravityfitnessnmh",
    "gravity-authe",
    "917999526112",
    "foyer-amenity-staff.ngrok-free.dev",
)
MINIMUM_SCHEMA_VERSION = 18


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def _https_origin(value: str) -> bool:
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and not parsed.username
        and not parsed.password
        and not parsed.path
        and not parsed.query
        and not parsed.fragment
    )


def _is_placeholder_origin(value: str) -> bool:
    try:
        host = (urlparse(value).hostname or "").lower()
    except ValueError:
        return True
    return host in PLACEHOLDER_HOSTS or host.endswith(".example")


def _bool(value: str) -> bool:
    return value.strip().lower() in TRUTHY


def inspect_database(path: Path) -> dict[str, object]:
    state: dict[str, object] = {
        "exists": path.is_file(),
        "schemaVersion": 0,
        "integrityOk": False,
        "foreignKeysOk": False,
        "legacyPlanDrafts": 0,
        "activePlans": 0,
        "invalidActivePlans": 0,
        "poolTables": 0,
        "poolTablesMissingRates": 0,
        "availableMenuItems": 0,
        "activeInventoryItems": 0,
        "invalidRecipes": 0,
    }
    if not path.is_file():
        return state

    try:
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            version = connection.execute(
                "SELECT COALESCE(MAX(CAST(version AS INTEGER)),0) FROM schema_migrations"
            ).fetchone()[0]
            state["schemaVersion"] = int(version or 0)
            state["integrityOk"] = connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
            state["foreignKeysOk"] = not connection.execute("PRAGMA foreign_key_check").fetchall()

            state["legacyPlanDrafts"] = int(connection.execute(
                "SELECT COUNT(*) FROM membership_plans WHERE "
                "(id='plan-basic-monthly' AND name='1 Month' AND price_paise=120000 AND duration_months=1) OR "
                "(id='plan-pro-monthly' AND name='3 Months' AND price_paise=300000 AND duration_months=3) OR "
                "(id='plan-elite-monthly' AND name='1 Year' AND price_paise=1000000 AND duration_months=12)"
            ).fetchone()[0])
            state["activePlans"] = int(connection.execute(
                "SELECT COUNT(*) FROM membership_plans WHERE status='active'"
            ).fetchone()[0])
            state["invalidActivePlans"] = int(connection.execute(
                "SELECT COUNT(*) FROM membership_plans "
                "WHERE status='active' AND (price_paise<=0 OR currency!='INR' OR duration_months<=0)"
            ).fetchone()[0])

            state["poolTables"] = int(connection.execute(
                "SELECT COUNT(*) FROM pool_tables"
            ).fetchone()[0])
            state["poolTablesMissingRates"] = int(connection.execute(
                "SELECT COUNT(*) FROM pool_tables "
                "WHERE status!='disabled' AND (default_rate_paise IS NULL OR default_rate_paise<=0)"
            ).fetchone()[0])

            state["availableMenuItems"] = int(connection.execute(
                "SELECT COUNT(*) FROM kitchen_menu_items WHERE status='available'"
            ).fetchone()[0])
            state["activeInventoryItems"] = int(connection.execute(
                "SELECT COUNT(*) FROM kitchen_inventory_items WHERE status='active'"
            ).fetchone()[0])
            state["invalidRecipes"] = int(connection.execute(
                "SELECT COUNT(*) FROM kitchen_recipes r "
                "LEFT JOIN kitchen_menu_items m ON m.id=r.menu_item_id "
                "LEFT JOIN kitchen_inventory_items i ON i.id=r.inventory_item_id "
                "WHERE m.id IS NULL OR i.id IS NULL OR i.status!='active' OR r.quantity_milli<=0"
            ).fetchone()[0])
        finally:
            connection.close()
    except (sqlite3.Error, OSError):
        state["readError"] = True
    return state


def inspect_backup_marker(
    path: Path,
    *,
    expected_remote: str,
    max_age_seconds: int,
    now: int | None = None,
) -> dict[str, object]:
    state: dict[str, object] = {
        "exists": path.is_file(),
        "valid": False,
        "fresh": False,
        "remoteMatches": False,
    }
    if not path.is_file():
        return state
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        verified_at = int(payload.get("verifiedAt") or 0)
        archive_sha = str(payload.get("archiveSha256") or "").strip().lower()
        remote_path = str(payload.get("remotePath") or "").strip()
        current = int(time.time()) if now is None else int(now)
        age = max(0, current - verified_at)
        expected_prefix = expected_remote.rstrip("/") + "/" if expected_remote else ""
        state.update({
            "valid": verified_at > 0 and bool(re.fullmatch(r"[0-9a-f]{64}", archive_sha)),
            "fresh": verified_at > 0 and age <= max_age_seconds,
            "remoteMatches": bool(expected_prefix) and remote_path.startswith(expected_prefix),
            "ageSeconds": age,
        })
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        state["readError"] = True
    return state


def validate(
    values: dict[str, str],
    *,
    stage: str,
    customer_config_text: str = "",
    path_exists=lambda value: Path(value).is_file(),
    database_state: dict[str, object] | None = None,
    backup_state: dict[str, object] | None = None,
) -> dict[str, object]:
    blockers: list[str] = []
    checks: list[dict[str, object]] = []

    def check(code: str, ok: bool, detail: str) -> None:
        checks.append({"code": code, "ok": bool(ok), "detail": detail})
        if not ok:
            blockers.append(code)

    check("production_env", values.get("GRAVITY_ENV") == "production", "GRAVITY_ENV must be production")
    check("loopback_admin", values.get("GRAVITY_HOST", "127.0.0.1") == "127.0.0.1", "Admin backend must bind to 127.0.0.1")

    ports: list[int] = []
    ports_ok = True
    for key, default in (
        ("GRAVITY_PORT", "8897"),
        ("NEW_GYM_MEMBER_GATEWAY_PORT", "8898"),
        ("NEW_GYM_PUBLIC_PORT", "8899"),
    ):
        try:
            port = int(values.get(key, default))
            ports.append(port)
            ports_ok = ports_ok and 1024 <= port <= 65535
        except ValueError:
            ports_ok = False
    check("isolated_ports", ports_ok and len(set(ports)) == 3, "Admin/member/public ports must be distinct valid high ports")

    check(
        "member_backend_loopback",
        values.get("NEW_GYM_MEMBER_BACKEND", "http://127.0.0.1:8897").startswith("http://127.0.0.1:"),
        "Member gateway backend must stay on loopback",
    )
    new_gym_paths = all(
        "new-gym" in values.get(key, "")
        and "gravity/" not in values.get(key, "").replace("\\", "/").lower()
        for key in ("GRAVITY_DATA_DIR", "GRAVITY_LOG_DIR", "GRAVITY_BACKUP_DIR")
    )
    check("isolated_runtime_paths", new_gym_paths, "Runtime data/log/backup paths must be New Gym-specific")

    secret = values.get("SECRET_KEY", "")
    check("secret_key", len(secret.encode("utf-8")) >= 32, "SECRET_KEY must contain at least 32 bytes")

    admin_origin = values.get("APP_BASE_URL", "")
    check("admin_https", _https_origin(admin_origin), "APP_BASE_URL must be an HTTPS origin")

    if stage == "launch":
        business_name = values.get("BUSINESS_NAME", "").strip()
        check(
            "business_name",
            bool(business_name) and business_name.casefold() != "new gym",
            "Replace the New Gym placeholder with the verified business name",
        )
        check("business_address", bool(values.get("BUSINESS_ADDRESS", "").strip()), "Business address is required")
        check(
            "owner_contact",
            bool(values.get("OWNER_PHONE", "").strip() or values.get("OWNER_EMAIL", "").strip()),
            "Owner phone or email is required",
        )
        check("admin_final_origin", not _is_placeholder_origin(admin_origin), "Replace the placeholder admin hostname")

        member_origins = [
            item.strip().rstrip("/")
            for item in values.get("NEW_GYM_MEMBER_ALLOWED_ORIGINS", "").split(",")
            if item.strip()
        ]
        origins_ok = bool(member_origins) and all(_https_origin(item) and not _is_placeholder_origin(item) for item in member_origins)
        check("member_final_origin", origins_ok, "Configure the final public HTTPS customer origin")

        check(
            "membership_pricing_confirmed",
            _bool(values.get("NEW_GYM_MEMBERSHIP_PRICING_CONFIRMED", "false")),
            "Owner must confirm membership pricing before launch",
        )
        check(
            "pool_rates_confirmed",
            _bool(values.get("NEW_GYM_POOL_RATES_CONFIRMED", "false")),
            "Owner must confirm all three pool rates before launch",
        )
        check(
            "kitchen_setup_confirmed",
            _bool(values.get("NEW_GYM_KITCHEN_SETUP_CONFIRMED", "false")),
            "Owner must confirm menu, recipes and opening stock before launch",
        )

        firebase_fields = (
            values.get("FIREBASE_PROJECT_ID", "").strip(),
            values.get("FIREBASE_WEB_API_KEY", "").strip(),
            values.get("FIREBASE_AUTH_DOMAIN", "").strip(),
            values.get("FIREBASE_APP_ID", "").strip(),
        )
        firebase_ok = all(firebase_fields) and not any(
            marker in " ".join(firebase_fields).casefold() for marker in GRAVITY_MARKERS
        )
        check("firebase_new_project", firebase_ok, "Configure a dedicated New Gym Firebase project")
        service_account = values.get("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
        check(
            "firebase_service_account",
            bool(service_account) and path_exists(service_account),
            "Dedicated Firebase service-account file must exist",
        )

        token_file = values.get("CLOUDFLARED_TOKEN_FILE", "").strip()
        check(
            "cloudflare_token",
            bool(token_file) and path_exists(token_file),
            "Dedicated New Gym Cloudflare token file must exist",
        )
        backup_remote = values.get("NEW_GYM_BACKUP_REMOTE", "").strip()
        require_backup = _bool(values.get("NEW_GYM_REQUIRE_OFFDEVICE_BACKUP", "true"))
        check(
            "offdevice_backup",
            (not require_backup) or (bool(backup_remote) and ":" in backup_remote),
            "Configure a dedicated rclone remote:path for off-device backup",
        )
        if require_backup:
            marker_ok = (
                backup_state is not None
                and bool(backup_state.get("exists"))
                and bool(backup_state.get("valid"))
                and bool(backup_state.get("fresh"))
                and bool(backup_state.get("remoteMatches"))
                and not backup_state.get("readError")
            )
            check(
                "offdevice_backup_fresh",
                marker_ok,
                "A recent verified off-device backup marker matching the configured remote is required",
            )

        config_lower = customer_config_text.casefold()
        no_live_gravity = not any(marker in config_lower for marker in GRAVITY_MARKERS)
        check("customer_no_gravity_live_values", no_live_gravity, "Customer config must not contain Gravity live values")
        customer_ready = bool(customer_config_text)
        for pattern in (
            r"name:\s*['\"]new gym['\"]",
            r"phoneDisplay:\s*['\"]\s*['\"]",
            r"whatsappNumber:\s*['\"]\s*['\"]",
            r"address:\s*['\"]\s*['\"]",
            r"memberGatewayBase:\s*['\"]\s*['\"]",
            r"projectId:\s*['\"]\s*['\"]",
        ):
            if re.search(pattern, customer_config_text, re.IGNORECASE):
                customer_ready = False
                break
        check(
            "customer_runtime_config",
            customer_ready,
            "Fill customer gym-config.js with verified identity/contact/gateway/Firebase values",
        )

        if database_state is not None:
            check(
                "database_exists",
                bool(database_state.get("exists")) and not database_state.get("readError"),
                "Production New Gym database must exist and be readable",
            )
            check(
                "database_schema",
                int(database_state.get("schemaVersion") or 0) >= MINIMUM_SCHEMA_VERSION,
                f"Database must be migrated through schema {MINIMUM_SCHEMA_VERSION:03d}",
            )
            check(
                "database_integrity",
                bool(database_state.get("integrityOk")) and bool(database_state.get("foreignKeysOk")),
                "SQLite quick_check and foreign-key check must pass",
            )
            check(
                "membership_plan_data",
                int(database_state.get("activePlans") or 0) > 0
                and int(database_state.get("invalidActivePlans") or 0) == 0
                and int(database_state.get("legacyPlanDrafts") or 0) == 0,
                "Configure at least one real active membership plan and replace all copied Gravity default plan signatures",
            )
            check(
                "pool_rate_data",
                int(database_state.get("poolTables") or 0) == 3
                and int(database_state.get("poolTablesMissingRates") or 0) == 0,
                "All three pool tables must exist with positive hourly rates",
            )
            check(
                "kitchen_live_data",
                int(database_state.get("availableMenuItems") or 0) > 0
                and int(database_state.get("activeInventoryItems") or 0) > 0
                and int(database_state.get("invalidRecipes") or 0) == 0,
                "Confirmed kitchen setup requires an available menu, active stock and valid recipes",
            )

    return {
        "stage": stage,
        "ready": not blockers,
        "blockers": blockers,
        "checks": checks,
    }


def main() -> int:
    parser = ArgumentParser(description="Fail-closed preflight for the isolated New Gym deployment.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--stage", choices=("install", "launch"), default="install")
    parser.add_argument("--customer-config")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    if not config_path.is_file():
        print(json.dumps({"stage": args.stage, "ready": False, "blockers": ["config_missing"], "checks": []}))
        return 2

    values = load_env(config_path)
    project_root = Path(__file__).resolve().parents[3]
    customer_config_path = (
        Path(args.customer_config).expanduser()
        if args.customer_config
        else project_root / "customer-website" / "web" / "js" / "gym-config.js"
    )
    customer_text = customer_config_path.read_text(encoding="utf-8") if customer_config_path.is_file() else ""
    database_state = None
    backup_state = None
    if args.stage == "launch":
        configured_database = values.get("NEW_GYM_MEMBER_DATABASE", "").strip()
        if configured_database:
            database_path = Path(configured_database).expanduser()
        else:
            database_path = Path(values.get("GRAVITY_DATA_DIR", "")).expanduser() / "gravity.sqlite3"
        database_state = inspect_database(database_path)

        if _bool(values.get("NEW_GYM_REQUIRE_OFFDEVICE_BACKUP", "true")):
            marker_path = Path(
                values.get(
                    "NEW_GYM_OFFDEVICE_BACKUP_MARKER",
                    "~/.local/state/new-gym/offdevice-backup.json",
                )
            ).expanduser()
            try:
                max_age = int(values.get("NEW_GYM_BACKUP_MAX_AGE_SECONDS", "86400"))
            except ValueError:
                max_age = 0
            if max_age <= 0:
                backup_state = {
                    "exists": marker_path.is_file(),
                    "valid": False,
                    "fresh": False,
                    "remoteMatches": False,
                    "readError": True,
                }
            else:
                backup_state = inspect_backup_marker(
                    marker_path,
                    expected_remote=values.get("NEW_GYM_BACKUP_REMOTE", "").strip(),
                    max_age_seconds=max_age,
                )
    result = validate(
        values,
        stage=args.stage,
        customer_config_text=customer_text,
        database_state=database_state,
        backup_state=backup_state,
    )
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
