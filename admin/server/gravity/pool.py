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

POOL_STATUSES = {"available", "occupied", "reserved", "cleaning", "disabled"}
RESERVATION_STATUSES = {"reserved", "checked_in", "completed", "cancelled", "no_show"}
PAYMENT_METHODS = {"cash", "upi", "card", "bank_transfer", "other"}


def _clean_optional_text(value: object, *, field: str, maximum: int = 160) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise AdminSoftwareValidationError({field: "Must be text"})
    cleaned = " ".join(value.strip().split())
    if not cleaned or len(cleaned) > maximum or "\x00" in cleaned:
        raise AdminSoftwareValidationError({field: f"Must be 1-{maximum} characters"})
    return cleaned


def _money(value: object, *, field: str, allow_none: bool = False) -> int | None:
    if value in (None, "") and allow_none:
        return None
    try:
        amount = int(value)
    except (TypeError, ValueError) as error:
        raise AdminSoftwareValidationError({field: "Must be an amount in paise"}) from error
    if amount < 0:
        raise AdminSoftwareValidationError({field: "Must be zero or greater"})
    return amount


def _timestamp(value: object, *, field: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise AdminSoftwareValidationError({field: "Must be a valid timestamp"}) from error
    if result <= 0:
        raise AdminSoftwareValidationError({field: "Must be a valid timestamp"})
    return result


def _phone(value: object) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise AdminSoftwareValidationError({"phone": "Must be a phone number"})
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) == 10 and digits[0] in "6789":
        return "+91" + digits
    if len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
        return "+" + digits
    raise AdminSoftwareValidationError({"phone": "Enter a valid Indian mobile number"})


class PoolService:
    def __init__(self, database: Database, admin_service, *, clock=time.time) -> None:
        self.database = database
        self.admin_service = admin_service
        self.clock = clock

    def _now(self) -> int:
        return int(self.clock())

    def _session_payload(self, row, *, now: int | None = None) -> dict[str, object]:
        current = self._now() if now is None else now
        ended = int(row["ended_at"]) if row["ended_at"] is not None else None
        elapsed = max(0, (ended or current) - int(row["started_at"]))
        keys = set(row.keys())
        return {
            "id": row["id"],
            "tableId": row["table_id"],
            "reservationId": row["reservation_id"] if "reservation_id" in keys else None,
            "customerId": row["customer_id"],
            "guestName": row["guest_name"],
            "ratePaisePerHour": int(row["rate_paise_per_hour"]),
            "startedAt": int(row["started_at"]),
            "endedAt": ended,
            "elapsedSeconds": elapsed,
            "status": row["status"],
            "amountPaise": int(row["amount_paise"]) if row["amount_paise"] is not None else None,
            "paymentStatus": row["payment_status"] if "payment_status" in keys else "unpaid",
            "paymentMethod": row["payment_method"] if "payment_method" in keys else None,
            "paidAt": int(row["paid_at"]) if "paid_at" in keys and row["paid_at"] is not None else None,
            "note": row["note"],
        }

    @staticmethod
    def _reservation_payload(row) -> dict[str, object]:
        keys = set(row.keys())
        return {
            "id": row["id"],
            "tableId": row["table_id"],
            "tableName": row["table_name"] if "table_name" in keys else None,
            "customerId": row["customer_id"],
            "guestName": row["guest_name"],
            "phone": row["phone_e164"],
            "startsAt": int(row["starts_at"]),
            "endsAt": int(row["ends_at"]),
            "status": row["status"],
            "ratePaisePerHour": int(row["rate_paise_per_hour"]) if row["rate_paise_per_hour"] is not None else None,
            "note": row["note"],
            "createdAt": int(row["created_at"]),
            "updatedAt": int(row["updated_at"]),
        }

    def list_tables(self) -> list[dict[str, object]]:
        now = self._now()
        with self.database.session() as connection:
            tables = connection.execute(
                "SELECT * FROM pool_tables ORDER BY CASE table_type WHEN 'private' THEN 0 ELSE 1 END, name"
            ).fetchall()
            active = connection.execute(
                "SELECT * FROM pool_sessions WHERE status='active' ORDER BY started_at"
            ).fetchall()
            upcoming = connection.execute(
                "SELECT r.*,t.name AS table_name FROM pool_reservations r "
                "JOIN pool_tables t ON t.id=r.table_id "
                "WHERE r.status='reserved' AND r.ends_at>? ORDER BY r.starts_at",
                (now,),
            ).fetchall()
        sessions = {row["table_id"]: self._session_payload(row, now=now) for row in active}
        next_reservations: dict[str, dict[str, object]] = {}
        for row in upcoming:
            next_reservations.setdefault(row["table_id"], self._reservation_payload(row))
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "type": row["table_type"],
                "status": row["status"],
                "defaultRatePaise": int(row["default_rate_paise"]) if row["default_rate_paise"] is not None else None,
                "activeSession": sessions.get(row["id"]),
                "nextReservation": next_reservations.get(row["id"]),
            }
            for row in tables
        ]

    def list_sessions(self, *, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        try:
            limit = min(max(int(limit), 1), 500)
        except (TypeError, ValueError):
            limit = 100
        params: list[object] = []
        where = ""
        if status:
            normalized = str(status).strip().casefold()
            if normalized not in {"active", "completed", "cancelled"}:
                raise AdminSoftwareValidationError({"status": "Invalid pool session status"})
            where = "WHERE s.status=?"
            params.append(normalized)
        params.append(limit)
        with self.database.session() as connection:
            rows = connection.execute(
                f"SELECT s.*,t.name AS table_name,t.table_type FROM pool_sessions s "
                f"JOIN pool_tables t ON t.id=s.table_id {where} ORDER BY s.started_at DESC LIMIT ?",
                tuple(params),
            ).fetchall()
        result = []
        for row in rows:
            item = self._session_payload(row)
            item["tableName"] = row["table_name"]
            item["tableType"] = row["table_type"]
            result.append(item)
        return result

    def _bill_payload(self, connection, row, *, now: int | None = None) -> dict[str, object]:
        current = self._now() if now is None else now
        session = self._session_payload(row, now=current)
        if row["status"] == "active":
            pool_charge = int(round(int(row["rate_paise_per_hour"]) * int(session["elapsedSeconds"]) / 3600))
        else:
            pool_charge = int(row["amount_paise"] or 0)

        kitchen_rows = connection.execute(
            "SELECT id,status,payment_status,total_paise,payment_method,paid_at,customer_name,created_at "
            "FROM kitchen_orders WHERE pool_session_id=? AND status!='cancelled' "
            "AND payment_status!='void' ORDER BY created_at",
            (row["id"],),
        ).fetchall()
        kitchen_total = sum(int(item["total_paise"]) for item in kitchen_rows)
        kitchen_paid = sum(
            int(item["total_paise"]) for item in kitchen_rows if item["payment_status"] == "paid"
        )
        pool_paid = pool_charge if row["payment_status"] == "paid" else 0
        grand_total = pool_charge + kitchen_total
        paid_total = pool_paid + kitchen_paid
        due = max(0, grand_total - paid_total)
        unserved = [item["id"] for item in kitchen_rows if item["status"] != "served"]
        return {
            "session": session,
            "tableName": row["table_name"] if "table_name" in row.keys() else row["table_id"],
            "poolChargePaise": pool_charge,
            "kitchenTotalPaise": kitchen_total,
            "grandTotalPaise": grand_total,
            "paidPaise": paid_total,
            "duePaise": due,
            "settlementReady": row["status"] == "completed" and not unserved,
            "unservedKitchenOrderIds": unserved,
            "kitchenOrders": [
                {
                    "id": item["id"],
                    "status": item["status"],
                    "paymentStatus": item["payment_status"],
                    "totalPaise": int(item["total_paise"]),
                    "paymentMethod": item["payment_method"],
                    "paidAt": int(item["paid_at"]) if item["paid_at"] is not None else None,
                    "customerName": item["customer_name"],
                }
                for item in kitchen_rows
            ],
        }

    def get_bill(self, session_id: str) -> dict[str, object]:
        with self.database.session() as connection:
            row = connection.execute(
                "SELECT s.*,t.name AS table_name FROM pool_sessions s "
                "JOIN pool_tables t ON t.id=s.table_id WHERE s.id=?",
                (session_id,),
            ).fetchone()
            if row is None:
                raise AdminSoftwareNotFound("Pool session not found")
            return self._bill_payload(connection, row)

    def settle_session(
        self,
        session_id: str,
        payload: Mapping[str, object],
        *,
        actor_admin_user_id: str,
    ) -> dict[str, object]:
        method = str(payload.get("paymentMethod") or "").strip().casefold()
        if method not in PAYMENT_METHODS:
            raise AdminSoftwareValidationError(
                {"paymentMethod": "Choose cash, UPI, card, bank transfer, or other"}
            )
        now = self._now()
        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT s.*,t.name AS table_name FROM pool_sessions s "
                "JOIN pool_tables t ON t.id=s.table_id WHERE s.id=?",
                (session_id,),
            ).fetchone()
            if row is None:
                raise AdminSoftwareNotFound("Pool session not found")
            if row["status"] != "completed":
                raise AdminSoftwareConflict("End the pool session before settling the final bill")

            blockers = connection.execute(
                "SELECT id FROM kitchen_orders WHERE pool_session_id=? "
                "AND status!='cancelled' AND payment_status!='void' AND status!='served' LIMIT 1",
                (session_id,),
            ).fetchone()
            if blockers:
                raise AdminSoftwareConflict(
                    "Finish or cancel all kitchen orders before settling the final bill"
                )

            connection.execute(
                "UPDATE pool_sessions SET payment_status='paid',payment_method=?,paid_at=? "
                "WHERE id=? AND payment_status!='paid'",
                (method, now, session_id),
            )
            connection.execute(
                "UPDATE kitchen_orders SET payment_status='paid',payment_method=?,paid_at=?,updated_at=? "
                "WHERE pool_session_id=? AND status='served' AND payment_status='unpaid'",
                (method, now, now, session_id),
            )
            self.admin_service._audit(
                connection,
                actor_admin_user_id,
                "pool_kitchen_bill_settled",
                target_type="pool_session",
                target_id=session_id,
                metadata={"paymentMethod": method},
            )
            connection.commit()
            settled = connection.execute(
                "SELECT s.*,t.name AS table_name FROM pool_sessions s "
                "JOIN pool_tables t ON t.id=s.table_id WHERE s.id=?",
                (session_id,),
            ).fetchone()
            return self._bill_payload(connection, settled, now=now)

    def list_reservations(
        self,
        *,
        status: str | None = None,
        from_at: object | None = None,
        to_at: object | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        try:
            limit = min(max(int(limit), 1), 500)
        except (TypeError, ValueError):
            limit = 100
        clauses: list[str] = []
        params: list[object] = []
        if status:
            normalized = str(status).strip().casefold()
            if normalized not in RESERVATION_STATUSES:
                raise AdminSoftwareValidationError({"status": "Invalid reservation status"})
            clauses.append("r.status=?")
            params.append(normalized)
        if from_at not in (None, ""):
            clauses.append("r.ends_at>=?")
            params.append(_timestamp(from_at, field="fromAt"))
        if to_at not in (None, ""):
            clauses.append("r.starts_at<=?")
            params.append(_timestamp(to_at, field="toAt"))
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)
        with self.database.session() as connection:
            rows = connection.execute(
                f"SELECT r.*,t.name AS table_name FROM pool_reservations r "
                f"JOIN pool_tables t ON t.id=r.table_id {where} "
                f"ORDER BY CASE WHEN r.status='reserved' THEN 0 ELSE 1 END,r.starts_at DESC LIMIT ?",
                tuple(params),
            ).fetchall()
        return [self._reservation_payload(row) for row in rows]

    def create_reservation(self, payload: Mapping[str, object], *, actor_admin_user_id: str) -> dict[str, object]:
        table_id = str(payload.get("tableId") or "").strip()
        if not table_id:
            raise AdminSoftwareValidationError({"tableId": "Select a pool table"})
        starts_at = _timestamp(payload.get("startsAt"), field="startsAt")
        ends_at = _timestamp(payload.get("endsAt"), field="endsAt")
        now = self._now()
        errors: dict[str, str] = {}
        if starts_at < now - 300:
            errors["startsAt"] = "Reservation start cannot be in the past"
        if ends_at <= starts_at:
            errors["endsAt"] = "End time must be after start time"
        if ends_at - starts_at > 24 * 60 * 60:
            errors["endsAt"] = "Reservation cannot exceed 24 hours"
        if errors:
            raise AdminSoftwareValidationError(errors)
        guest_name = _clean_optional_text(payload.get("guestName"), field="guestName", maximum=80)
        phone = _phone(payload.get("phone"))
        note = _clean_optional_text(payload.get("note"), field="note", maximum=500)
        customer_id = str(payload.get("customerId") or "").strip() or None
        reservation_id = uuid4().hex

        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            table = connection.execute("SELECT * FROM pool_tables WHERE id=?", (table_id,)).fetchone()
            if table is None:
                raise AdminSoftwareNotFound("Pool table not found")
            if table["status"] == "disabled":
                raise AdminSoftwareConflict("This pool table is disabled")
            if customer_id:
                customer = connection.execute(
                    "SELECT display_name,phone_e164 FROM customers WHERE id=? AND status!='deleted'",
                    (customer_id,),
                ).fetchone()
                if customer is None:
                    raise AdminSoftwareNotFound("Customer not found")
                if not guest_name:
                    guest_name = customer["display_name"]
                if not phone:
                    phone = customer["phone_e164"]
            if not guest_name and not customer_id:
                raise AdminSoftwareValidationError({"guestName": "Enter a guest name or select a member"})
            overlap = connection.execute(
                "SELECT 1 FROM pool_reservations "
                "WHERE table_id=? AND status IN ('reserved','checked_in') "
                "AND starts_at < ? AND ends_at > ? LIMIT 1",
                (table_id, ends_at, starts_at),
            ).fetchone()
            if overlap:
                raise AdminSoftwareConflict("This table already has a reservation in that time window")
            raw_rate = payload.get("ratePaisePerHour", table["default_rate_paise"])
            rate = _money(raw_rate, field="ratePaisePerHour", allow_none=True)
            connection.execute(
                "INSERT INTO pool_reservations("
                "id,table_id,customer_id,guest_name,phone_e164,starts_at,ends_at,status,"
                "rate_paise_per_hour,note,created_by_admin_user_id,created_at,updated_at"
                ") VALUES(?,?,?,?,?,?,?,'reserved',?,?,?,?,?)",
                (
                    reservation_id, table_id, customer_id, guest_name, phone, starts_at, ends_at,
                    rate, note, actor_admin_user_id, now, now,
                ),
            )
            self.admin_service._audit(
                connection,
                actor_admin_user_id,
                "pool_reservation_created",
                target_type="pool_reservation",
                target_id=reservation_id,
                metadata={"tableId": table_id, "startsAt": starts_at, "endsAt": ends_at},
            )
            connection.commit()
            row = connection.execute(
                "SELECT r.*,t.name AS table_name FROM pool_reservations r "
                "JOIN pool_tables t ON t.id=r.table_id WHERE r.id=?",
                (reservation_id,),
            ).fetchone()
        return self._reservation_payload(row)

    def update_reservation_status(
        self,
        reservation_id: str,
        status: str,
        *,
        actor_admin_user_id: str,
    ) -> dict[str, object]:
        requested = str(status or "").strip().casefold()
        if requested not in {"cancelled", "no_show"}:
            raise AdminSoftwareValidationError({"status": "Choose cancelled or no_show"})
        now = self._now()
        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM pool_reservations WHERE id=?", (reservation_id,)
            ).fetchone()
            if row is None:
                raise AdminSoftwareNotFound("Pool reservation not found")
            if row["status"] != "reserved":
                raise AdminSoftwareConflict("Only an upcoming reservation can be cancelled or marked no-show")
            connection.execute(
                "UPDATE pool_reservations SET status=?,updated_at=? WHERE id=?",
                (requested, now, reservation_id),
            )
            self.admin_service._audit(
                connection,
                actor_admin_user_id,
                f"pool_reservation_{requested}",
                target_type="pool_reservation",
                target_id=reservation_id,
                metadata={"tableId": row["table_id"]},
            )
            connection.commit()
            updated = connection.execute(
                "SELECT r.*,t.name AS table_name FROM pool_reservations r "
                "JOIN pool_tables t ON t.id=r.table_id WHERE r.id=?",
                (reservation_id,),
            ).fetchone()
        return self._reservation_payload(updated)

    def update_table(self, table_id: str, payload: Mapping[str, object], *, actor_admin_user_id: str) -> dict[str, object]:
        now = self._now()
        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM pool_tables WHERE id=?", (table_id,)).fetchone()
            if row is None:
                raise AdminSoftwareNotFound("Pool table not found")
            name = row["name"]
            if "name" in payload:
                name = _clean_optional_text(payload.get("name"), field="name", maximum=60)
                if not name:
                    raise AdminSoftwareValidationError({"name": "Name is required"})
            rate = row["default_rate_paise"]
            if "defaultRatePaise" in payload:
                rate = _money(payload.get("defaultRatePaise"), field="defaultRatePaise", allow_none=True)
            status = row["status"]
            if "status" in payload:
                requested = str(payload.get("status") or "").strip().casefold()
                if requested not in POOL_STATUSES - {"occupied"}:
                    raise AdminSoftwareValidationError({"status": "Choose available, reserved, cleaning, or disabled"})
                active = connection.execute(
                    "SELECT 1 FROM pool_sessions WHERE table_id=? AND status='active' LIMIT 1", (table_id,)
                ).fetchone()
                if active:
                    raise AdminSoftwareConflict("End the active session before changing table status")
                status = requested
            connection.execute(
                "UPDATE pool_tables SET name=?,default_rate_paise=?,status=?,updated_at=? WHERE id=?",
                (name, rate, status, now, table_id),
            )
            self.admin_service._audit(
                connection, actor_admin_user_id, "pool_table_updated",
                target_type="pool_table", target_id=table_id,
                metadata={"status": status, "defaultRatePaise": rate},
            )
            connection.commit()
        return next(item for item in self.list_tables() if item["id"] == table_id)

    def start_session(self, payload: Mapping[str, object], *, actor_admin_user_id: str) -> dict[str, object]:
        reservation_id = str(payload.get("reservationId") or "").strip() or None
        table_id = str(payload.get("tableId") or "").strip()
        guest_name = _clean_optional_text(payload.get("guestName"), field="guestName", maximum=80)
        note = _clean_optional_text(payload.get("note"), field="note", maximum=500)
        customer_id = str(payload.get("customerId") or "").strip() or None
        now = self._now()

        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            reservation = None
            if reservation_id:
                reservation = connection.execute(
                    "SELECT * FROM pool_reservations WHERE id=?", (reservation_id,)
                ).fetchone()
                if reservation is None:
                    raise AdminSoftwareNotFound("Pool reservation not found")
                if reservation["status"] != "reserved":
                    raise AdminSoftwareConflict("Reservation is not available for check-in")
                if table_id and table_id != reservation["table_id"]:
                    raise AdminSoftwareConflict("Reservation belongs to a different pool table")
                table_id = reservation["table_id"]
                customer_id = customer_id or reservation["customer_id"]
                guest_name = guest_name or reservation["guest_name"]
                note = note or reservation["note"]

            if not table_id:
                raise AdminSoftwareValidationError({"tableId": "Select a pool table"})
            table = connection.execute("SELECT * FROM pool_tables WHERE id=?", (table_id,)).fetchone()
            if table is None:
                raise AdminSoftwareNotFound("Pool table not found")
            if table["status"] in {"occupied", "cleaning", "disabled"}:
                raise AdminSoftwareConflict(f"{table['name']} is not available")
            existing = connection.execute(
                "SELECT 1 FROM pool_sessions WHERE table_id=? AND status='active' LIMIT 1", (table_id,)
            ).fetchone()
            if existing:
                raise AdminSoftwareConflict("This table already has an active session")

            fallback_rate = reservation["rate_paise_per_hour"] if reservation is not None else table["default_rate_paise"]
            raw_rate = payload.get("ratePaisePerHour", fallback_rate)
            if raw_rate in (None, ""):
                raise AdminSoftwareValidationError({"ratePaisePerHour": "Set the hourly rate before starting"})
            rate = _money(raw_rate, field="ratePaisePerHour")
            if customer_id:
                customer = connection.execute(
                    "SELECT 1 FROM customers WHERE id=? AND status!='deleted'", (customer_id,)
                ).fetchone()
                if customer is None:
                    raise AdminSoftwareNotFound("Customer not found")

            session_id = uuid4().hex
            connection.execute(
                "INSERT INTO pool_sessions("
                "id,table_id,reservation_id,customer_id,guest_name,rate_paise_per_hour,"
                "started_at,status,note,created_by_admin_user_id,created_at"
                ") VALUES(?,?,?,?,?,?,?,'active',?,?,?)",
                (
                    session_id, table_id, reservation_id, customer_id, guest_name, rate,
                    now, note, actor_admin_user_id, now,
                ),
            )
            connection.execute(
                "UPDATE pool_tables SET status='occupied',updated_at=? WHERE id=?", (now, table_id)
            )
            if reservation_id:
                connection.execute(
                    "UPDATE pool_reservations SET status='checked_in',updated_at=? WHERE id=?",
                    (now, reservation_id),
                )
            self.admin_service._audit(
                connection, actor_admin_user_id, "pool_session_started",
                target_type="pool_session", target_id=session_id,
                metadata={
                    "tableId": table_id,
                    "reservationId": reservation_id,
                    "ratePaisePerHour": rate,
                },
            )
            connection.commit()
            row = connection.execute("SELECT * FROM pool_sessions WHERE id=?", (session_id,)).fetchone()
        return self._session_payload(row, now=now)

    def end_session(self, session_id: str, payload: Mapping[str, object], *, actor_admin_user_id: str) -> dict[str, object]:
        now = self._now()
        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM pool_sessions WHERE id=?", (session_id,)).fetchone()
            if row is None:
                raise AdminSoftwareNotFound("Pool session not found")
            if row["status"] != "active":
                raise AdminSoftwareConflict("Pool session is already closed")
            elapsed = max(0, now - int(row["started_at"]))
            if payload.get("amountPaise") not in (None, ""):
                amount = _money(payload.get("amountPaise"), field="amountPaise")
            else:
                amount = int(round(int(row["rate_paise_per_hour"]) * elapsed / 3600))
            connection.execute(
                "UPDATE pool_sessions SET ended_at=?,status='completed',amount_paise=?,ended_by_admin_user_id=? WHERE id=?",
                (now, amount, actor_admin_user_id, session_id),
            )
            connection.execute(
                "UPDATE pool_tables SET status='available',updated_at=? WHERE id=?", (now, row["table_id"])
            )
            if row["reservation_id"]:
                connection.execute(
                    "UPDATE pool_reservations SET status='completed',updated_at=? "
                    "WHERE id=? AND status='checked_in'",
                    (now, row["reservation_id"]),
                )
            self.admin_service._audit(
                connection, actor_admin_user_id, "pool_session_completed",
                target_type="pool_session", target_id=session_id,
                metadata={"tableId": row["table_id"], "elapsedSeconds": elapsed, "amountPaise": amount},
            )
            connection.commit()
            completed = connection.execute("SELECT * FROM pool_sessions WHERE id=?", (session_id,)).fetchone()
        return self._session_payload(completed, now=now)
