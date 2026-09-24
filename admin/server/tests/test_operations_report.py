from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from server.gravity.admin import ROLE_PERMISSIONS
from server.gravity.admin_software import AdminSoftwareValidationError
from server.gravity.config import Settings
from server.gravity.database import Database
from server.gravity.kitchen import KitchenService
from server.gravity.operations_report import OperationsReportService
from server.gravity.pool import PoolService


ROOT = Path(__file__).resolve().parents[2]


class _AuditStub:
    def _audit(self, connection, admin_user_id, action, **kwargs):
        return None


class OperationsReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        runtime = Path(self.temporary.name)
        self.settings = Settings.load(
            root_dir=ROOT,
            environ={
                "BUSINESS_NAME": "New Gym",
                "BUSINESS_TIMEZONE": "Asia/Kolkata",
            },
        )
        self.database = Database(
            runtime / "new-gym.sqlite3",
            ROOT / "server" / "migrations",
        )
        self.database.migrate()
        self.clock_value = int(
            datetime(2026, 9, 24, 12, 0, tzinfo=timezone(timedelta(hours=5, minutes=30))).timestamp()
        )
        clock = lambda: self.clock_value
        audit = _AuditStub()
        self.pool = PoolService(self.database, audit, clock=clock)
        self.kitchen = KitchenService(self.database, audit, clock=clock)
        self.report = OperationsReportService(
            self.database,
            self.settings,
            clock=clock,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_daily_report_combines_pool_kitchen_settlements_and_stock(self):
        self.pool.update_table(
            "pool-private-1",
            {"defaultRatePaise": 12000},
            actor_admin_user_id=None,
        )
        reservation = self.pool.create_reservation(
            {
                "tableId": "pool-common-1",
                "guestName": "Evening Booking",
                "startsAt": self.clock_value + 3600,
                "endsAt": self.clock_value + 7200,
                "ratePaisePerHour": 10000,
            },
            actor_admin_user_id=None,
        )
        self.assertEqual(reservation["status"], "reserved")

        session = self.pool.start_session(
            {
                "tableId": "pool-private-1",
                "guestName": "Report Guest",
            },
            actor_admin_user_id=None,
        )
        menu = self.kitchen.create_menu_item(
            {
                "name": "Cold Coffee",
                "category": "Drinks",
                "pricePaise": 8000,
            },
            actor_admin_user_id=None,
        )
        order = self.kitchen.create_order(
            {
                "poolSessionId": session["id"],
                "customerName": "Report Guest",
                "items": [{"menuItemId": menu["id"], "quantity": 2}],
            },
            actor_admin_user_id=None,
        )
        self.kitchen.create_inventory_item(
            {
                "name": "Milk",
                "unit": "litre",
                "quantityMilli": 1000,
                "lowStockMilli": 2000,
            },
            actor_admin_user_id=None,
        )

        self.clock_value += 1800
        ended = self.pool.end_session(
            session["id"],
            {},
            actor_admin_user_id=None,
        )
        self.assertEqual(ended["amountPaise"], 6000)

        for status in ("preparing", "ready", "served"):
            self.kitchen.update_order(
                order["id"],
                {"status": status},
                actor_admin_user_id=None,
            )
        settled = self.pool.settle_session(
            session["id"],
            {"paymentMethod": "upi"},
            actor_admin_user_id=None,
        )
        self.assertEqual(settled["duePaise"], 0)

        result = self.report.daily("2026-09-24")
        summary = result["summary"]
        self.assertEqual(result["timezone"], "Asia/Kolkata")
        self.assertEqual(summary["completedPoolSessions"], 1)
        self.assertEqual(summary["poolMinutes"], 30)
        self.assertEqual(summary["poolBilledPaise"], 6000)
        self.assertEqual(summary["kitchenOrders"], 1)
        self.assertEqual(summary["kitchenSalesPaise"], 16000)
        self.assertEqual(summary["operationsSalesPaise"], 22000)
        self.assertEqual(summary["settledRevenuePaise"], 22000)
        self.assertEqual(summary["outstandingPaise"], 0)
        self.assertEqual(summary["activePoolSessions"], 0)
        self.assertEqual(summary["openKitchenOrders"], 0)
        self.assertEqual(summary["lowStockItems"], 1)

        private = next(
            row for row in result["poolTables"] if row["id"] == "pool-private-1"
        )
        self.assertEqual(private["sessions"], 1)
        self.assertEqual(private["minutes"], 30)
        self.assertEqual(private["billedPaise"], 6000)

        self.assertEqual(result["reservations"]["reserved"], 1)
        self.assertEqual(result["kitchenStatuses"]["served"], 1)
        self.assertEqual(
            result["topKitchenItems"][0],
            {"name": "Cold Coffee", "quantity": 2, "salesPaise": 16000},
        )
        self.assertEqual(
            result["paymentMethods"],
            [{"method": "upi", "amountPaise": 22000}],
        )
        self.assertEqual(result["lowStock"][0]["name"], "Milk")

    def test_standalone_kitchen_paid_at_is_reported_as_settled_revenue(self):
        menu = self.kitchen.create_menu_item(
            {"name": "Water", "category": "Drinks", "pricePaise": 2000},
            actor_admin_user_id=None,
        )
        order = self.kitchen.create_order(
            {
                "customerName": "Walk-in",
                "items": [{"menuItemId": menu["id"], "quantity": 1}],
            },
            actor_admin_user_id=None,
        )
        paid = self.kitchen.update_order(
            order["id"],
            {"paymentStatus": "paid", "paymentMethod": "cash"},
            actor_admin_user_id=None,
        )
        self.assertEqual(paid["paymentStatus"], "paid")
        self.assertEqual(paid["paymentMethod"], "cash")
        self.assertEqual(paid["paidAt"], self.clock_value)

        result = self.report.daily("2026-09-24")
        self.assertEqual(result["summary"]["settledRevenuePaise"], 2000)
        self.assertEqual(
            result["paymentMethods"],
            [{"method": "cash", "amountPaise": 2000}],
        )

    def test_report_rejects_invalid_date_and_roles_are_correct(self):
        with self.assertRaises(AdminSoftwareValidationError):
            self.report.daily("24-09-2026")

        self.assertIn("operations.report", ROLE_PERMISSIONS["admin"])
        self.assertIn("operations.report", ROLE_PERMISSIONS["reception"])
        self.assertNotIn("operations.report", ROLE_PERMISSIONS["trainer"])
        self.assertIn("pool.manage", ROLE_PERMISSIONS["admin"])
        self.assertIn("kitchen.manage", ROLE_PERMISSIONS["admin"])


if __name__ == "__main__":
    unittest.main()
