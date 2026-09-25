#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json
import time

from server.gravity.config import Settings
from server.gravity.database import Database

ADMIN_ROOT = Path(__file__).resolve().parents[2]

DEMO_PLANS = (
    ("demo-women-founding-12m", "women-founding-12m", "Women · Founding 12 Months", 2199900, 12, 10),
    ("demo-men-founding-12m", "men-founding-12m", "Men · Founding 12 Months", 2799900, 12, 20),
    ("demo-student-1m", "student-1m", "Student · 1 Month", 199900, 1, 30),
    ("demo-student-3m", "student-3m", "Student · 3 Months", 549900, 3, 31),
    ("demo-student-6m", "student-6m", "Student · 6 Months", 999900, 6, 32),
    ("demo-couple-3m", "couple-3m", "Couple · 3 Months", 1100000, 3, 40),
    ("demo-couple-6m", "couple-6m", "Couple · 6 Months", 2000000, 6, 41),
    ("demo-couple-12m", "couple-12m", "Couple · 12 Months", 4800000, 12, 42),
    ("demo-women-1m", "women-regular-1m", "Women Regular · 1 Month", 249900, 1, 50),
    ("demo-women-3m", "women-regular-3m", "Women Regular · 3 Months", 600000, 3, 51),
    ("demo-women-6m", "women-regular-6m", "Women Regular · 6 Months", 1080000, 6, 52),
    ("demo-women-12m", "women-regular-12m", "Women Regular · 12 Months", 2400000, 12, 53),
    ("demo-men-1m", "men-regular-1m", "Men Regular · 1 Month", 299900, 1, 60),
    ("demo-men-3m", "men-regular-3m", "Men Regular · 3 Months", 750000, 3, 61),
    ("demo-men-6m", "men-regular-6m", "Men Regular · 6 Months", 1350000, 6, 62),
    ("demo-men-12m", "men-regular-12m", "Men Regular · 12 Months", 3000000, 12, 63),
)

DEMO_MENU = (
    ("demo-menu-water", "Mineral Water", "Drinks", 2000, 10),
    ("demo-menu-tea", "Tea", "Drinks", 3000, 20),
    ("demo-menu-cold-coffee", "Cold Coffee", "Drinks", 9000, 30),
    ("demo-menu-protein-shake", "Protein Shake", "Fitness", 15000, 40),
    ("demo-menu-sandwich", "Grilled Sandwich", "Snacks", 12000, 50),
)

DEMO_STOCK = (
    ("demo-stock-milk", "Milk", "litre", 20000, 5000),
    ("demo-stock-coffee", "Coffee Powder", "kg", 2000, 500),
    ("demo-stock-protein", "Protein Powder", "kg", 3000, 750),
    ("demo-stock-bread", "Bread", "piece", 40000, 10000),
)

DEMO_RECIPES = (
    ("demo-menu-tea", "demo-stock-milk", 100),
    ("demo-menu-cold-coffee", "demo-stock-milk", 250),
    ("demo-menu-cold-coffee", "demo-stock-coffee", 20),
    ("demo-menu-protein-shake", "demo-stock-milk", 300),
    ("demo-menu-protein-shake", "demo-stock-protein", 30),
    ("demo-menu-sandwich", "demo-stock-bread", 2000),
)


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


def seed(database: Database) -> dict[str, object]:
    migrated = database.migrate()
    now = int(time.time())
    with database.session() as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "INSERT INTO app_metadata(key,value,updated_at) VALUES('owner_demo_mode','1',strftime('%Y-%m-%dT%H:%M:%fZ','now')) "
            "ON CONFLICT(key) DO UPDATE SET value='1',updated_at=excluded.updated_at"
        )
        connection.execute(
            "INSERT INTO app_metadata(key,value,updated_at) VALUES('owner_demo_notice','Dummy operational values; replace after owner approval',strftime('%Y-%m-%dT%H:%M:%fZ','now')) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at"
        )
        connection.execute("UPDATE pool_tables SET default_rate_paise=30000,updated_at=? WHERE id='pool-private-1'", (now,))
        connection.execute("UPDATE pool_tables SET default_rate_paise=20000,updated_at=? WHERE id IN ('pool-common-1','pool-common-2')", (now,))

        for plan_id, code, name, price, months, sort_order in DEMO_PLANS:
            connection.execute(
                "INSERT INTO membership_plans(id,code,name,description,price_paise,currency,duration_months,status,sort_order,created_at,updated_at) "
                "VALUES(?,?,?,?,?,'INR',?,'active',?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET code=excluded.code,name=excluded.name,description=excluded.description,"
                "price_paise=excluded.price_paise,duration_months=excluded.duration_months,status='active',"
                "sort_order=excluded.sort_order,updated_at=excluded.updated_at",
                (plan_id, code, name, "Owner-demo plan from the current Need For Strength poster; confirm before production.", price, months, sort_order, now, now),
            )

        for item_id, name, category, price, sort_order in DEMO_MENU:
            connection.execute(
                "INSERT INTO kitchen_menu_items(id,name,category,price_paise,status,sort_order,created_at,updated_at) "
                "VALUES(?,?,?,?,'available',?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET name=excluded.name,category=excluded.category,price_paise=excluded.price_paise,"
                "status='available',sort_order=excluded.sort_order,updated_at=excluded.updated_at",
                (item_id, name, category, price, sort_order, now, now),
            )

        for item_id, name, unit, quantity, low_stock in DEMO_STOCK:
            connection.execute(
                "INSERT INTO kitchen_inventory_items(id,name,unit,quantity_milli,low_stock_milli,status,created_at,updated_at) "
                "VALUES(?,?,?,?,?,'active',?,?) "
                "ON CONFLICT(id) DO UPDATE SET name=excluded.name,unit=excluded.unit,low_stock_milli=excluded.low_stock_milli,"
                "status='active',updated_at=excluded.updated_at",
                (item_id, name, unit, quantity, low_stock, now, now),
            )

        for menu_id, inventory_id, quantity_milli in DEMO_RECIPES:
            connection.execute(
                "INSERT INTO kitchen_recipes(menu_item_id,inventory_item_id,quantity_milli,created_at,updated_at) "
                "VALUES(?,?,?,?,?) ON CONFLICT(menu_item_id,inventory_item_id) DO UPDATE SET "
                "quantity_milli=excluded.quantity_milli,updated_at=excluded.updated_at",
                (menu_id, inventory_id, quantity_milli, now, now),
            )
        connection.commit()

    return {
        "migrationsApplied": migrated,
        "demoPlans": len(DEMO_PLANS),
        "demoMenuItems": len(DEMO_MENU),
        "poolPrivateRatePaise": 30000,
        "poolCommonRatePaise": 20000,
        "ownerDemoMode": True,
    }


def main() -> int:
    parser = ArgumentParser(description="Seed Need For Strength owner-demo operational data.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    values = load_env(Path(args.config).expanduser())
    Settings.load(root_dir=ADMIN_ROOT, environ=values)
    database_path = Path(
        values.get("NEW_GYM_MEMBER_DATABASE")
        or str(Path(values["GRAVITY_DATA_DIR"]).expanduser() / "gravity.sqlite3")
    ).expanduser()
    database = Database(database_path, ADMIN_ROOT / "server" / "migrations")
    print(json.dumps(seed(database), separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
