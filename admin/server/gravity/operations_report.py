from __future__ import annotations

from datetime import date, datetime, time as datetime_time, timedelta, timezone
from typing import Callable
from zoneinfo import ZoneInfo
import time

from .admin_software import AdminSoftwareValidationError
from .config import Settings
from .database import Database


class OperationsReportService:
    def __init__(
        self,
        database: Database,
        settings: Settings,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.database = database
        self.settings = settings
        self.clock = clock
        self.timezone = (
            timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")
            if settings.business_timezone == "Asia/Kolkata"
            else ZoneInfo(settings.business_timezone)
        )

    def _window(self, requested_date: str | None) -> tuple[str, int, int]:
        if requested_date:
            try:
                report_date = date.fromisoformat(str(requested_date))
            except ValueError as error:
                raise AdminSoftwareValidationError(
                    {"date": "Use YYYY-MM-DD"}
                ) from error
        else:
            report_date = datetime.fromtimestamp(self.clock(), self.timezone).date()

        start_local = datetime.combine(
            report_date,
            datetime_time.min,
            tzinfo=self.timezone,
        )
        end_local = start_local + timedelta(days=1)
        return (
            report_date.isoformat(),
            int(start_local.timestamp()),
            int(end_local.timestamp()),
        )

    @staticmethod
    def _status_counts(rows) -> dict[str, int]:
        return {str(row["status"]): int(row["count"]) for row in rows}

    def daily(self, requested_date: str | None = None) -> dict[str, object]:
        report_date, start_at, end_at = self._window(requested_date)
        generated_at = int(self.clock())

        with self.database.session() as connection:
            pool_summary = connection.execute(
                "SELECT COUNT(*) AS session_count,"
                "COALESCE(SUM(MAX(0,ended_at-started_at)),0) AS seconds_used,"
                "COALESCE(SUM(amount_paise),0) AS billed_paise,"
                "COALESCE(SUM(CASE WHEN payment_status='paid' THEN amount_paise ELSE 0 END),0) AS paid_paise "
                "FROM pool_sessions "
                "WHERE status='completed' AND ended_at>=? AND ended_at<?",
                (start_at, end_at),
            ).fetchone()

            active_pool = connection.execute(
                "SELECT COUNT(*) FROM pool_sessions WHERE status='active'"
            ).fetchone()[0]

            pool_rows = connection.execute(
                "SELECT t.id,t.name,t.table_type,"
                "COUNT(s.id) AS session_count,"
                "COALESCE(SUM(MAX(0,s.ended_at-s.started_at)),0) AS seconds_used,"
                "COALESCE(SUM(s.amount_paise),0) AS billed_paise,"
                "COALESCE(SUM(CASE WHEN s.payment_status='paid' THEN s.amount_paise ELSE 0 END),0) AS paid_paise "
                "FROM pool_tables t "
                "LEFT JOIN pool_sessions s ON s.table_id=t.id "
                "AND s.status='completed' AND s.ended_at>=? AND s.ended_at<? "
                "GROUP BY t.id,t.name,t.table_type "
                "ORDER BY CASE t.table_type WHEN 'private' THEN 0 ELSE 1 END,t.name",
                (start_at, end_at),
            ).fetchall()

            reservation_counts = connection.execute(
                "SELECT status,COUNT(*) AS count FROM pool_reservations "
                "WHERE starts_at>=? AND starts_at<? GROUP BY status",
                (start_at, end_at),
            ).fetchall()

            kitchen_summary = connection.execute(
                "SELECT COUNT(*) AS order_count,COALESCE(SUM(total_paise),0) AS sales_paise,"
                "COALESCE(SUM(CASE WHEN payment_status='paid' THEN total_paise ELSE 0 END),0) AS paid_paise "
                "FROM kitchen_orders "
                "WHERE created_at>=? AND created_at<? "
                "AND status!='cancelled' AND payment_status!='void'",
                (start_at, end_at),
            ).fetchone()

            kitchen_status_counts = connection.execute(
                "SELECT status,COUNT(*) AS count FROM kitchen_orders "
                "WHERE created_at>=? AND created_at<? GROUP BY status",
                (start_at, end_at),
            ).fetchall()

            open_kitchen = connection.execute(
                "SELECT COUNT(*) FROM kitchen_orders "
                "WHERE status IN ('new','preparing','ready')"
            ).fetchone()[0]

            top_items = connection.execute(
                "SELECT oi.item_name_snapshot AS name,"
                "SUM(oi.quantity) AS quantity,"
                "SUM(oi.line_total_paise) AS sales_paise "
                "FROM kitchen_order_items oi "
                "JOIN kitchen_orders o ON o.id=oi.order_id "
                "WHERE o.created_at>=? AND o.created_at<? "
                "AND o.status!='cancelled' AND o.payment_status!='void' "
                "GROUP BY oi.item_name_snapshot "
                "ORDER BY sales_paise DESC,quantity DESC,name COLLATE NOCASE "
                "LIMIT 10",
                (start_at, end_at),
            ).fetchall()

            low_stock = connection.execute(
                "SELECT id,name,unit,quantity_milli,low_stock_milli "
                "FROM kitchen_inventory_items "
                "WHERE status='active' AND quantity_milli<=low_stock_milli "
                "ORDER BY quantity_milli ASC,name COLLATE NOCASE"
            ).fetchall()

            settled_pool = connection.execute(
                "SELECT COALESCE(SUM(amount_paise),0) FROM pool_sessions "
                "WHERE payment_status='paid' AND paid_at>=? AND paid_at<?",
                (start_at, end_at),
            ).fetchone()[0]
            settled_kitchen = connection.execute(
                "SELECT COALESCE(SUM(total_paise),0) FROM kitchen_orders "
                "WHERE payment_status='paid' AND paid_at>=? AND paid_at<?",
                (start_at, end_at),
            ).fetchone()[0]

            outstanding_pool = connection.execute(
                "SELECT COALESCE(SUM(amount_paise),0) FROM pool_sessions "
                "WHERE status='completed' AND payment_status='unpaid' "
                "AND ended_at>=? AND ended_at<?",
                (start_at, end_at),
            ).fetchone()[0]
            outstanding_kitchen = connection.execute(
                "SELECT COALESCE(SUM(total_paise),0) FROM kitchen_orders "
                "WHERE created_at>=? AND created_at<? "
                "AND status!='cancelled' AND payment_status='unpaid'",
                (start_at, end_at),
            ).fetchone()[0]

            payment_methods = connection.execute(
                "SELECT method,SUM(amount_paise) AS amount_paise FROM ("
                "SELECT COALESCE(payment_method,'unspecified') AS method,amount_paise "
                "FROM pool_sessions WHERE payment_status='paid' AND paid_at>=? AND paid_at<? "
                "UNION ALL "
                "SELECT COALESCE(payment_method,'unspecified') AS method,total_paise AS amount_paise "
                "FROM kitchen_orders WHERE payment_status='paid' AND paid_at>=? AND paid_at<?"
                ") GROUP BY method ORDER BY amount_paise DESC,method",
                (start_at, end_at, start_at, end_at),
            ).fetchall()

        pool_billed = int(pool_summary["billed_paise"] or 0)
        pool_paid = int(pool_summary["paid_paise"] or 0)
        kitchen_sales = int(kitchen_summary["sales_paise"] or 0)
        kitchen_paid = int(kitchen_summary["paid_paise"] or 0)
        settled_revenue = int(settled_pool or 0) + int(settled_kitchen or 0)
        outstanding = int(outstanding_pool or 0) + int(outstanding_kitchen or 0)

        return {
            "date": report_date,
            "timezone": self.settings.business_timezone,
            "generatedAt": generated_at,
            "window": {"startAt": start_at, "endAt": end_at},
            "summary": {
                "completedPoolSessions": int(pool_summary["session_count"] or 0),
                "poolMinutes": int(round(int(pool_summary["seconds_used"] or 0) / 60)),
                "poolBilledPaise": pool_billed,
                "poolPaidPaise": pool_paid,
                "kitchenOrders": int(kitchen_summary["order_count"] or 0),
                "kitchenSalesPaise": kitchen_sales,
                "kitchenPaidPaise": kitchen_paid,
                "operationsSalesPaise": pool_billed + kitchen_sales,
                "settledRevenuePaise": settled_revenue,
                "outstandingPaise": outstanding,
                "activePoolSessions": int(active_pool or 0),
                "openKitchenOrders": int(open_kitchen or 0),
                "lowStockItems": len(low_stock),
            },
            "poolTables": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "type": row["table_type"],
                    "sessions": int(row["session_count"] or 0),
                    "minutes": int(round(int(row["seconds_used"] or 0) / 60)),
                    "billedPaise": int(row["billed_paise"] or 0),
                    "paidPaise": int(row["paid_paise"] or 0),
                }
                for row in pool_rows
            ],
            "reservations": self._status_counts(reservation_counts),
            "kitchenStatuses": self._status_counts(kitchen_status_counts),
            "topKitchenItems": [
                {
                    "name": row["name"],
                    "quantity": int(row["quantity"] or 0),
                    "salesPaise": int(row["sales_paise"] or 0),
                }
                for row in top_items
            ],
            "paymentMethods": [
                {
                    "method": row["method"],
                    "amountPaise": int(row["amount_paise"] or 0),
                }
                for row in payment_methods
            ],
            "lowStock": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "unit": row["unit"],
                    "quantityMilli": int(row["quantity_milli"]),
                    "lowStockMilli": int(row["low_stock_milli"]),
                }
                for row in low_stock
            ],
        }
