#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import sqlite3


GRAVITY_MARKERS = (
    "gravityfitnessnmh",
    "gravity-authe",
    "917999526112",
    "foyer-amenity-staff.ngrok-free.dev",
)
PLAN_IDS = {
    "oneMonth": "plan-basic-monthly",
    "threeMonths": "plan-pro-monthly",
    "oneYear": "plan-elite-monthly",
}


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


def first_origin(values: dict[str, str]) -> str:
    for item in values.get("NEW_GYM_MEMBER_ALLOWED_ORIGINS", "").split(","):
        origin = item.strip().rstrip("/")
        if origin:
            return origin
    return ""


def phone_href(value: str) -> str:
    cleaned = re.sub(r"[^0-9+]", "", value.strip())
    return f"tel:{cleaned}" if cleaned else ""


def whatsapp_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def initials(name: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", name)
    if not words:
        return "NG"
    return "".join(word[0].upper() for word in words[:3])


def load_membership_prices(database_path: Path) -> dict[str, int | None]:
    prices: dict[str, int | None] = {
        "trial": None,
        "oneMonth": None,
        "threeMonths": None,
        "oneYear": None,
    }
    if not database_path.is_file():
        return prices
    try:
        connection = sqlite3.connect(f"file:{database_path.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                "SELECT id,price_paise,status FROM membership_plans "
                "WHERE id IN (?,?,?)",
                tuple(PLAN_IDS.values()),
            ).fetchall()
        finally:
            connection.close()
    except sqlite3.Error:
        return prices
    by_id = {row["id"]: row for row in rows}
    for public_key, plan_id in PLAN_IDS.items():
        row = by_id.get(plan_id)
        if row is not None and row["status"] == "active" and int(row["price_paise"]) > 0:
            prices[public_key] = int(row["price_paise"])
    return prices


def build_config(values: dict[str, str], prices: dict[str, int | None]) -> dict[str, object]:
    name = values.get("BUSINESS_NAME", "").strip() or "New Gym"
    phone = values.get("OWNER_PHONE", "").strip()
    whatsapp = values.get("OWNER_WHATSAPP", "").strip() or phone
    site_url = values.get("NEW_GYM_PUBLIC_SITE_URL", "").strip().rstrip("/") or first_origin(values)
    return {
        "name": name,
        "shortName": values.get("BUSINESS_SHORT_NAME", "").strip() or initials(name),
        "city": values.get("BUSINESS_CITY", "").strip(),
        "phoneDisplay": phone,
        "phoneHref": phone_href(phone),
        "whatsappNumber": whatsapp_digits(whatsapp),
        "address": values.get("BUSINESS_ADDRESS", "").strip(),
        "openingHours": values.get("BUSINESS_OPENING_HOURS", "").strip(),
        "instagramUrl": values.get("BUSINESS_INSTAGRAM", "").strip(),
        "mapUrl": values.get("BUSINESS_MAP_URL", "").strip(),
        "mapEmbedUrl": values.get("BUSINESS_MAP_EMBED_URL", "").strip(),
        "siteUrl": site_url,
        "memberGatewayBase": site_url,
        "membershipPricesPaise": prices,
        "firebase": {
            "apiKey": values.get("FIREBASE_WEB_API_KEY", "").strip(),
            "authDomain": values.get("FIREBASE_AUTH_DOMAIN", "").strip(),
            "projectId": values.get("FIREBASE_PROJECT_ID", "").strip(),
            "appId": values.get("FIREBASE_APP_ID", "").strip(),
        },
        "analyticsFirebase": {
            "apiKey": values.get("FIREBASE_ANALYTICS_WEB_API_KEY", "").strip(),
            "authDomain": values.get("FIREBASE_ANALYTICS_AUTH_DOMAIN", "").strip(),
            "projectId": values.get("FIREBASE_ANALYTICS_PROJECT_ID", "").strip(),
            "storageBucket": values.get("FIREBASE_ANALYTICS_STORAGE_BUCKET", "").strip(),
            "messagingSenderId": values.get("FIREBASE_ANALYTICS_MESSAGING_SENDER_ID", "").strip(),
            "appId": values.get("FIREBASE_ANALYTICS_APP_ID", "").strip(),
            "measurementId": values.get("FIREBASE_ANALYTICS_MEASUREMENT_ID", "").strip(),
        },
    }


def validate_complete(config: dict[str, object]) -> list[str]:
    blockers: list[str] = []
    if str(config["name"]).strip().casefold() == "new gym":
        blockers.append("business_name")
    for key in ("city", "phoneDisplay", "whatsappNumber", "address", "openingHours", "siteUrl", "memberGatewayBase"):
        if not str(config.get(key) or "").strip():
            blockers.append(key)
    site_url = str(config.get("siteUrl") or "")
    parsed = urlparse(site_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/"):
        blockers.append("siteUrl_https_origin")
    firebase = config.get("firebase") or {}
    for key in ("apiKey", "authDomain", "projectId", "appId"):
        if not str(firebase.get(key) or "").strip():
            blockers.append(f"firebase_{key}")
    prices = config.get("membershipPricesPaise") or {}
    for key in ("oneMonth", "threeMonths", "oneYear"):
        if not isinstance(prices.get(key), int) or prices[key] <= 0:
            blockers.append(f"membership_{key}")
    serialized = json.dumps(config, ensure_ascii=False).casefold()
    if any(marker in serialized for marker in GRAVITY_MARKERS):
        blockers.append("gravity_live_value")
    return blockers


def render(config: dict[str, object]) -> str:
    payload = json.dumps(config, ensure_ascii=False, indent=2)
    return (
        "(function () {\n"
        "  'use strict';\n\n"
        f"  window.NEW_GYM_CONFIG = Object.freeze({payload});\n"
        "})();\n"
    )


def main() -> int:
    parser = ArgumentParser(description="Render New Gym customer config from protected production settings.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--database")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    values = load_env(Path(args.config).expanduser())
    database_path = (
        Path(args.database).expanduser()
        if args.database
        else Path(
            values.get("NEW_GYM_MEMBER_DATABASE")
            or (str(Path(values.get("GRAVITY_DATA_DIR", "")).expanduser() / "gravity.sqlite3"))
        )
    )
    config = build_config(values, load_membership_prices(database_path))
    blockers = validate_complete(config) if args.require_complete else []
    if blockers:
        print(json.dumps({"ready": False, "blockers": blockers}, separators=(",", ":"), sort_keys=True))
        return 2

    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(config), encoding="utf-8")
    print(json.dumps({"ready": True, "output": str(output)}, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
