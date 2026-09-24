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
        return {
            "id": row["id"],
            "tableId": row["table_id"],
            "customerId": row["customer_id"],
            "guestName": row["guest_name"],
            "ratePaisePerHour": int(row["rate_paise_per_hour"]),
            "startedAt": int(row["started_at"]),
            "endedAt": ended,
            "elapsedSeconds": elapsed,
            "status": row["status"],
            "amountPaise": int(row["amount_paise"]) if row["amount_paise"] is not None else None,
            "note": row["note"],
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
        sessions = {row["table_id"]: self._session_payload(row, now=now) for row in active}
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "type": row["table_type"],
                "status": row["status"],
                "defaultRatePaise": int(row["default_rate_paise"]) if row["default_rate_paise"] is not None else None,
                "activeSession": sessions.get(row["id"]),
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
        table_id = str(payload.get("tableId") or "").strip()
        if not table_id:
            raise AdminSoftwareValidationError({"tableId": "Select a pool table"})
        guest_name = _clean_optional_text(payload.get("guestName"), field="guestName", maximum=80)
        note = _clean_optional_text(payload.get("note"), field="note", maximum=500)
        customer_id = str(payload.get("customerId") or "").strip() or None
        now = self._now()
        with self.database.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
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
            raw_rate = payload.get("ratePaisePerHour", table["default_rate_paise"])
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
                "INSERT INTO pool_sessions(id,table_id,customer_id,guest_name,rate_paise_per_hour,"
                "started_at,status,note,created_by_admin_user_id,created_at) VALUES(?,?,?,?,?,?,'active',?,?,?)",
                (session_id, table_id, customer_id, guest_name, rate, now, note, actor_admin_user_id, now),
            )
            connection.execute(
                "UPDATE pool_tables SET status='occupied',updated_at=? WHERE id=?", (now, table_id)
            )
            self.admin_service._audit(
                connection, actor_admin_user_id, "pool_session_started",
                target_type="pool_session", target_id=session_id,
                metadata={"tableId": table_id, "ratePaisePerHour": rate},
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
            self.admin_service._audit(
                connection, actor_admin_user_id, "pool_session_completed",
                target_type="pool_session", target_id=session_id,
                metadata={"tableId": row["table_id"], "elapsedSeconds": elapsed, "amountPaise": amount},
            )
            connection.commit()
            completed = connection.execute("SELECT * FROM pool_sessions WHERE id=?", (session_id,)).fetchone()
        return self._session_payload(completed, now=now)
