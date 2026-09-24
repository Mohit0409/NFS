from __future__ import annotations

from typing import Mapping
from uuid import uuid4
import time

from .admin_software import (
    AdminSoftwareConflict,
    AdminSoftwareNotFound,
    AdminSoftwareValidationError,
)
from .database import Database

ORDER_STATUSES = {"new", "preparing", "ready", "served", "cancelled"}
PAYMENT_STATUSES = {"unpaid", "paid", "void"}
INVENTORY_REASONS = {"purchase", "usage", "waste", "adjustment"}
STATUS_TRANSITIONS = {
    "new": {"preparing", "cancelled"},
    "preparing": {"ready", "cancelled"},
    "ready": {"served", "cancelled"},
    "served": set(),
    "cancelled": set(),
}


def _text(value: object, *, field: str, maximum: int, required: bool = False) -> str | None:
    if value in (None, ""):
        if required:
            raise AdminSoftwareValidationError({field: "Required"})
        return None
    if not isinstance(value, str):
        raise AdminSoftwareValidationError({field: "Must be text"})
    cleaned = " ".join(value.strip().split())
    if not cleaned or len(cleaned) > maximum or "\x00" in cleaned:
        raise AdminSoftwareValidationError({field: f"Must be 1-{maximum} characters"})
    return cleaned


def _integer(value: object, *, field: str, minimum: int = 0, maximum: int | None = None) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise AdminSoftwareValidationError({field: "Must be a whole number"}) from error
    if result < minimum or (maximum is not None and result > maximum):
        limit = f" between {minimum} and {maximum}" if maximum is not None else f" at least {minimum}"
        raise AdminSoftwareValidationError({field: f"Must be{limit}"})
    return result


class KitchenService:
    def __init__(self, database: Database, admin_service, *, clock=time.time) -> None:
        self.database = database
        self.admin_service = admin_service
        self.clock = clock

    def _now(self) -> int:
        return int(self.clock())

    @staticmethod
    def _menu_payload(row) -> dict[str, object]:
        return {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "pricePaise": int(row["price_paise"]),
            "status": row["status"],
            "sortOrder": int(row["sort_order"]),
        }

    def list_menu(self, *, include_unavailable: bool = True) -> list[dict[str, object]]:
        where = "" if include_unavailable else "WHERE status='available'"
        with self.database.session() as connection:
            rows = connection.execute(
                f"SELECT * FROM kitchen_menu_items {where} ORDER BY category,sort_order,name"
            ).fetchall()
        return [self._menu_payload(row) for row in rows]

    def create_menu_item(self, payload: Mapping[str, object], *, actor_admin_user_id: str) -> dict[str, object]:
        name = _text(payload.get("name"), field="name", maximum=100, required=True)
        category = _text(payload.get("category"), field="category", maximum=60, required=True)
        price = _integer(payload.get("pricePaise"), field="pricePaise", minimum=0)
        status = str(payload.get("status") or "available").strip().casefold()
        if status not in {"available", "unavailable"}:
            raise AdminSoftwareValidationError({"status": "Choose available or unavailable"})
        sort_order = _integer(payload.get("sortOrder", 0), field="sortOrder", minimum=-10000, maximum=10000)
        item_id = uuid4().hex
        now = self._now()
        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO kitchen_menu_items(id,name,category,price_paise,status,sort_order,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (item_id, name, category, price, status, sort_order, now, now),
            )
            self.admin_service._audit(
                connection, actor_admin_user_id, "kitchen_menu_item_created",
                target_type="kitchen_menu_item", target_id=item_id,
                metadata={"pricePaise": price, "status": status},
            )
            connection.commit()
            row = connection.execute("SELECT * FROM kitchen_menu_items WHERE id=?", (item_id,)).fetchone()
        return self._menu_payload(row)

    def update_menu_item(self, item_id: str, payload: Mapping[str, object], *, actor_admin_user_id: str) -> dict[str, object]:
        now = self._now()
        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM kitchen_menu_items WHERE id=?", (item_id,)).fetchone()
            if row is None:
                raise AdminSoftwareNotFound("Kitchen menu item not found")
            name = row["name"] if "name" not in payload else _text(payload.get("name"), field="name", maximum=100, required=True)
            category = row["category"] if "category" not in payload else _text(payload.get("category"), field="category", maximum=60, required=True)
            price = int(row["price_paise"]) if "pricePaise" not in payload else _integer(payload.get("pricePaise"), field="pricePaise", minimum=0)
            status = row["status"]
            if "status" in payload:
                status = str(payload.get("status") or "").strip().casefold()
                if status not in {"available", "unavailable"}:
                    raise AdminSoftwareValidationError({"status": "Choose available or unavailable"})
            sort_order = int(row["sort_order"]) if "sortOrder" not in payload else _integer(payload.get("sortOrder"), field="sortOrder", minimum=-10000, maximum=10000)
            connection.execute(
                "UPDATE kitchen_menu_items SET name=?,category=?,price_paise=?,status=?,sort_order=?,updated_at=? WHERE id=?",
                (name, category, price, status, sort_order, now, item_id),
            )
            self.admin_service._audit(
                connection, actor_admin_user_id, "kitchen_menu_item_updated",
                target_type="kitchen_menu_item", target_id=item_id,
                metadata={"pricePaise": price, "status": status},
            )
            connection.commit()
            updated = connection.execute("SELECT * FROM kitchen_menu_items WHERE id=?", (item_id,)).fetchone()
        return self._menu_payload(updated)

    def _order_payload(self, connection, row) -> dict[str, object]:
        items = connection.execute(
            "SELECT * FROM kitchen_order_items WHERE order_id=? ORDER BY rowid", (row["id"],)
        ).fetchall()
        return {
            "id": row["id"],
            "poolSessionId": row["pool_session_id"],
            "customerId": row["customer_id"],
            "customerName": row["customer_name"],
            "status": row["status"],
            "paymentStatus": row["payment_status"],
            "totalPaise": int(row["total_paise"]),
            "note": row["note"],
            "createdAt": int(row["created_at"]),
            "updatedAt": int(row["updated_at"]),
            "items": [
                {
                    "id": item["id"],
                    "menuItemId": item["menu_item_id"],
                    "name": item["item_name_snapshot"],
                    "unitPricePaise": int(item["unit_price_paise"]),
                    "quantity": int(item["quantity"]),
                    "lineTotalPaise": int(item["line_total_paise"]),
                }
                for item in items
            ],
        }

    def list_orders(self, *, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        try:
            limit = min(max(int(limit), 1), 500)
        except (TypeError, ValueError):
            limit = 100
        params: list[object] = []
        where = ""
        if status:
            normalized = str(status).strip().casefold()
            if normalized not in ORDER_STATUSES:
                raise AdminSoftwareValidationError({"status": "Invalid kitchen order status"})
            where = "WHERE status=?"
            params.append(normalized)
        params.append(limit)
        with self.database.session() as connection:
            rows = connection.execute(
                f"SELECT * FROM kitchen_orders {where} ORDER BY created_at DESC LIMIT ?", tuple(params)
            ).fetchall()
            return [self._order_payload(connection, row) for row in rows]

    def create_order(self, payload: Mapping[str, object], *, actor_admin_user_id: str) -> dict[str, object]:
        raw_items = payload.get("items")
        if not isinstance(raw_items, list) or not raw_items:
            raise AdminSoftwareValidationError({"items": "Add at least one menu item"})
        if len(raw_items) > 50:
            raise AdminSoftwareValidationError({"items": "Maximum 50 line items per order"})
        pool_session_id = str(payload.get("poolSessionId") or "").strip() or None
        customer_id = str(payload.get("customerId") or "").strip() or None
        customer_name = _text(payload.get("customerName"), field="customerName", maximum=80)
        note = _text(payload.get("note"), field="note", maximum=500)
        now = self._now()
        order_id = uuid4().hex
        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if pool_session_id:
                pool = connection.execute(
                    "SELECT customer_id FROM pool_sessions WHERE id=? AND status='active'", (pool_session_id,)
                ).fetchone()
                if pool is None:
                    raise AdminSoftwareConflict("Pool session is not active")
                if not customer_id and pool["customer_id"]:
                    customer_id = pool["customer_id"]
            if customer_id:
                customer = connection.execute(
                    "SELECT display_name FROM customers WHERE id=? AND status!='deleted'", (customer_id,)
                ).fetchone()
                if customer is None:
                    raise AdminSoftwareNotFound("Customer not found")
                if not customer_name:
                    customer_name = customer["display_name"]
            prepared: list[tuple[str, object, int]] = []
            total = 0
            for index, raw in enumerate(raw_items):
                if not isinstance(raw, Mapping):
                    raise AdminSoftwareValidationError({"items": f"Line {index + 1} is invalid"})
                item_id = str(raw.get("menuItemId") or "").strip()
                quantity = _integer(raw.get("quantity", 1), field=f"items[{index}].quantity", minimum=1, maximum=100)
                menu = connection.execute(
                    "SELECT * FROM kitchen_menu_items WHERE id=?", (item_id,)
                ).fetchone()
                if menu is None:
                    raise AdminSoftwareNotFound("Kitchen menu item not found")
                if menu["status"] != "available":
                    raise AdminSoftwareConflict(f"{menu['name']} is unavailable")
                line_total = int(menu["price_paise"]) * quantity
                total += line_total
                prepared.append((uuid4().hex, menu, quantity))
            connection.execute(
                "INSERT INTO kitchen_orders(id,pool_session_id,customer_id,customer_name,status,payment_status,"
                "total_paise,note,created_by_admin_user_id,created_at,updated_at) "
                "VALUES(?,?,?,?, 'new','unpaid',?,?,?,?,?)",
                (order_id, pool_session_id, customer_id, customer_name, total, note, actor_admin_user_id, now, now),
            )
            for line_id, menu, quantity in prepared:
                connection.execute(
                    "INSERT INTO kitchen_order_items(id,order_id,menu_item_id,item_name_snapshot,unit_price_paise,"
                    "quantity,line_total_paise) VALUES(?,?,?,?,?,?,?)",
                    (line_id, order_id, menu["id"], menu["name"], int(menu["price_paise"]), quantity, int(menu["price_paise"]) * quantity),
                )
            self.admin_service._audit(
                connection, actor_admin_user_id, "kitchen_order_created",
                target_type="kitchen_order", target_id=order_id,
                metadata={"poolSessionId": pool_session_id, "totalPaise": total, "itemCount": len(prepared)},
            )
            connection.commit()
            row = connection.execute("SELECT * FROM kitchen_orders WHERE id=?", (order_id,)).fetchone()
            return self._order_payload(connection, row)

    def update_order(self, order_id: str, payload: Mapping[str, object], *, actor_admin_user_id: str) -> dict[str, object]:
        now = self._now()
        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM kitchen_orders WHERE id=?", (order_id,)).fetchone()
            if row is None:
                raise AdminSoftwareNotFound("Kitchen order not found")
            status = row["status"]
            if "status" in payload:
                requested = str(payload.get("status") or "").strip().casefold()
                if requested not in ORDER_STATUSES:
                    raise AdminSoftwareValidationError({"status": "Invalid kitchen order status"})
                if requested != status and requested not in STATUS_TRANSITIONS[status]:
                    raise AdminSoftwareConflict(f"Cannot move order from {status} to {requested}")
                status = requested
            payment = row["payment_status"]
            if "paymentStatus" in payload:
                payment = str(payload.get("paymentStatus") or "").strip().casefold()
                if payment not in PAYMENT_STATUSES:
                    raise AdminSoftwareValidationError({"paymentStatus": "Invalid payment status"})
                if status == "cancelled" and payment == "paid":
                    raise AdminSoftwareConflict("Cancelled order cannot be marked paid")
            connection.execute(
                "UPDATE kitchen_orders SET status=?,payment_status=?,updated_at=? WHERE id=?",
                (status, payment, now, order_id),
            )
            self.admin_service._audit(
                connection, actor_admin_user_id, "kitchen_order_updated",
                target_type="kitchen_order", target_id=order_id,
                metadata={"status": status, "paymentStatus": payment},
            )
            connection.commit()
            updated = connection.execute("SELECT * FROM kitchen_orders WHERE id=?", (order_id,)).fetchone()
            return self._order_payload(connection, updated)

    @staticmethod
    def _inventory_payload(row) -> dict[str, object]:
        quantity = int(row["quantity_milli"])
        low_stock = int(row["low_stock_milli"])
        return {
            "id": row["id"],
            "name": row["name"],
            "unit": row["unit"],
            "quantityMilli": quantity,
            "lowStockMilli": low_stock,
            "lowStock": quantity <= low_stock,
            "status": row["status"],
            "createdAt": int(row["created_at"]),
            "updatedAt": int(row["updated_at"]),
        }

    def list_inventory(self, *, include_inactive: bool = True) -> list[dict[str, object]]:
        where = "" if include_inactive else "WHERE status='active'"
        with self.database.session() as connection:
            rows = connection.execute(
                f"SELECT * FROM kitchen_inventory_items {where} ORDER BY name COLLATE NOCASE"
            ).fetchall()
        return [self._inventory_payload(row) for row in rows]

    def create_inventory_item(
        self,
        payload: Mapping[str, object],
        *,
        actor_admin_user_id: str,
    ) -> dict[str, object]:
        name = _text(payload.get("name"), field="name", maximum=100, required=True)
        unit = _text(payload.get("unit"), field="unit", maximum=30, required=True)
        quantity = _integer(
            payload.get("quantityMilli", 0),
            field="quantityMilli",
            minimum=0,
            maximum=1_000_000_000_000,
        )
        low_stock = _integer(
            payload.get("lowStockMilli", 0),
            field="lowStockMilli",
            minimum=0,
            maximum=1_000_000_000_000,
        )
        now = self._now()
        item_id = uuid4().hex
        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT 1 FROM kitchen_inventory_items WHERE name=? COLLATE NOCASE",
                (name,),
            ).fetchone()
            if existing:
                raise AdminSoftwareConflict("Kitchen inventory item already exists")
            connection.execute(
                "INSERT INTO kitchen_inventory_items("
                "id,name,unit,quantity_milli,low_stock_milli,status,created_at,updated_at"
                ") VALUES(?,?,?,?,?,'active',?,?)",
                (item_id, name, unit, quantity, low_stock, now, now),
            )
            if quantity:
                connection.execute(
                    "INSERT INTO kitchen_inventory_movements("
                    "id,item_id,delta_milli,quantity_after_milli,reason,note,"
                    "created_by_admin_user_id,created_at"
                    ") VALUES(?,?,?,?, 'adjustment',?,?,?)",
                    (
                        uuid4().hex,
                        item_id,
                        quantity,
                        quantity,
                        "Initial stock",
                        actor_admin_user_id,
                        now,
                    ),
                )
            self.admin_service._audit(
                connection,
                actor_admin_user_id,
                "kitchen_inventory_item_created",
                target_type="kitchen_inventory_item",
                target_id=item_id,
                metadata={"quantityMilli": quantity, "lowStockMilli": low_stock, "unit": unit},
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM kitchen_inventory_items WHERE id=?", (item_id,)
            ).fetchone()
        return self._inventory_payload(row)

    def adjust_inventory(
        self,
        item_id: str,
        payload: Mapping[str, object],
        *,
        actor_admin_user_id: str,
    ) -> dict[str, object]:
        delta = _integer(
            payload.get("deltaMilli"),
            field="deltaMilli",
            minimum=-1_000_000_000_000,
            maximum=1_000_000_000_000,
        )
        if delta == 0:
            raise AdminSoftwareValidationError({"deltaMilli": "Stock change cannot be zero"})
        reason = str(payload.get("reason") or "").strip().casefold()
        if reason not in INVENTORY_REASONS:
            raise AdminSoftwareValidationError(
                {"reason": "Choose purchase, usage, waste, or adjustment"}
            )
        note = _text(payload.get("note"), field="note", maximum=300)
        now = self._now()
        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM kitchen_inventory_items WHERE id=?", (item_id,)
            ).fetchone()
            if row is None:
                raise AdminSoftwareNotFound("Kitchen inventory item not found")
            if row["status"] != "active":
                raise AdminSoftwareConflict("Kitchen inventory item is inactive")
            new_quantity = int(row["quantity_milli"]) + delta
            if new_quantity < 0:
                raise AdminSoftwareConflict("Stock cannot go below zero")
            connection.execute(
                "UPDATE kitchen_inventory_items SET quantity_milli=?,updated_at=? WHERE id=?",
                (new_quantity, now, item_id),
            )
            connection.execute(
                "INSERT INTO kitchen_inventory_movements("
                "id,item_id,delta_milli,quantity_after_milli,reason,note,"
                "created_by_admin_user_id,created_at"
                ") VALUES(?,?,?,?,?,?,?,?)",
                (
                    uuid4().hex,
                    item_id,
                    delta,
                    new_quantity,
                    reason,
                    note,
                    actor_admin_user_id,
                    now,
                ),
            )
            self.admin_service._audit(
                connection,
                actor_admin_user_id,
                "kitchen_inventory_adjusted",
                target_type="kitchen_inventory_item",
                target_id=item_id,
                metadata={"deltaMilli": delta, "quantityAfterMilli": new_quantity, "reason": reason},
            )
            connection.commit()
            updated = connection.execute(
                "SELECT * FROM kitchen_inventory_items WHERE id=?", (item_id,)
            ).fetchone()
        return self._inventory_payload(updated)
