from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from server.gravity.database import Database
from server.gravity.kitchen import KitchenService
from server.gravity.pool import PoolService


ROOT = Path(__file__).resolve().parents[2]


class _AuditStub:
    def _audit(self, connection, admin_user_id, action, **kwargs):
        return None


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        path = Path(self.temporary.name) / "new-gym.sqlite3"
        self.database = Database(path, ROOT / "server" / "migrations")
        self.database.migrate()
        self.clock_value = 1_800_000_000
        clock = lambda: self.clock_value
        self.pool = PoolService(self.database, _AuditStub(), clock=clock)
        self.kitchen = KitchenService(self.database, _AuditStub(), clock=clock)

    def tearDown(self):
        self.temporary.cleanup()

    def test_three_pool_tables_are_seeded(self):
        tables = self.pool.list_tables()
        self.assertEqual(
            {(item["name"], item["type"]) for item in tables},
            {
                ("Private Table", "private"),
                ("Common Table 1", "common"),
                ("Common Table 2", "common"),
            },
        )
        self.assertTrue(all(item["status"] == "available" for item in tables))

    def test_pool_session_start_and_end_updates_table(self):
        self.pool.update_table(
            "pool-private-1",
            {"defaultRatePaise": 12000},
            actor_admin_user_id=None,
        )
        session = self.pool.start_session(
            {"tableId": "pool-private-1", "guestName": "Walk-in"},
            actor_admin_user_id=None,
        )
        self.assertEqual(session["status"], "active")
        self.assertEqual(session["ratePaisePerHour"], 12000)
        table = next(item for item in self.pool.list_tables() if item["id"] == "pool-private-1")
        self.assertEqual(table["status"], "occupied")

        self.clock_value += 1800
        completed = self.pool.end_session(session["id"], {}, actor_admin_user_id=None)
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["elapsedSeconds"], 1800)
        self.assertEqual(completed["amountPaise"], 6000)
        table = next(item for item in self.pool.list_tables() if item["id"] == "pool-private-1")
        self.assertEqual(table["status"], "available")

    def test_kitchen_order_uses_price_snapshot_and_status_flow(self):
        item = self.kitchen.create_menu_item(
            {"name": "Cold Coffee", "category": "Drinks", "pricePaise": 8000},
            actor_admin_user_id=None,
        )
        order = self.kitchen.create_order(
            {
                "customerName": "Walk-in",
                "items": [{"menuItemId": item["id"], "quantity": 2}],
            },
            actor_admin_user_id=None,
        )
        self.assertEqual(order["totalPaise"], 16000)
        self.assertEqual(order["items"][0]["unitPricePaise"], 8000)

        self.kitchen.update_menu_item(
            item["id"],
            {"pricePaise": 9000},
            actor_admin_user_id=None,
        )
        stored = self.kitchen.list_orders()[0]
        self.assertEqual(stored["items"][0]["unitPricePaise"], 8000)
        self.assertEqual(stored["totalPaise"], 16000)

        for status in ("preparing", "ready", "served"):
            stored = self.kitchen.update_order(
                order["id"], {"status": status}, actor_admin_user_id=None
            )
            self.assertEqual(stored["status"], status)

    def test_kitchen_order_can_attach_to_active_pool_session(self):
        session = self.pool.start_session(
            {"tableId": "pool-common-1", "ratePaisePerHour": 10000, "guestName": "Pool Guest"},
            actor_admin_user_id=None,
        )
        item = self.kitchen.create_menu_item(
            {"name": "Water", "category": "Drinks", "pricePaise": 2000},
            actor_admin_user_id=None,
        )
        order = self.kitchen.create_order(
            {
                "poolSessionId": session["id"],
                "items": [{"menuItemId": item["id"], "quantity": 1}],
            },
            actor_admin_user_id=None,
        )
        self.assertEqual(order["poolSessionId"], session["id"])
        self.assertEqual(order["totalPaise"], 2000)


if __name__ == "__main__":
    unittest.main()
