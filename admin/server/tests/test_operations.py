from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from server.gravity.admin_software import AdminSoftwareConflict
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


    def test_pool_reservation_blocks_overlap_and_completes_with_session(self):
        reservation = self.pool.create_reservation(
            {
                "tableId": "pool-private-1",
                "guestName": "Booked Guest",
                "phone": "9876543210",
                "startsAt": self.clock_value + 600,
                "endsAt": self.clock_value + 4200,
                "ratePaisePerHour": 12000,
            },
            actor_admin_user_id=None,
        )
        self.assertEqual(reservation["status"], "reserved")
        self.assertEqual(reservation["phone"], "+919876543210")

        with self.assertRaises(AdminSoftwareConflict):
            self.pool.create_reservation(
                {
                    "tableId": "pool-private-1",
                    "guestName": "Overlap",
                    "startsAt": self.clock_value + 1200,
                    "endsAt": self.clock_value + 2400,
                    "ratePaisePerHour": 12000,
                },
                actor_admin_user_id=None,
            )

        self.clock_value += 600
        session = self.pool.start_session(
            {"reservationId": reservation["id"]},
            actor_admin_user_id=None,
        )
        self.assertEqual(session["reservationId"], reservation["id"])
        self.assertEqual(session["guestName"], "Booked Guest")

        checked_in = next(
            item for item in self.pool.list_reservations() if item["id"] == reservation["id"]
        )
        self.assertEqual(checked_in["status"], "checked_in")

        self.clock_value += 1800
        self.pool.end_session(session["id"], {}, actor_admin_user_id=None)
        completed = next(
            item for item in self.pool.list_reservations() if item["id"] == reservation["id"]
        )
        self.assertEqual(completed["status"], "completed")

    def test_kitchen_inventory_tracks_low_stock_and_never_goes_negative(self):
        item = self.kitchen.create_inventory_item(
            {
                "name": "Milk",
                "unit": "litre",
                "quantityMilli": 5000,
                "lowStockMilli": 2000,
            },
            actor_admin_user_id=None,
        )
        self.assertFalse(item["lowStock"])
        self.assertEqual(item["quantityMilli"], 5000)

        adjusted = self.kitchen.adjust_inventory(
            item["id"],
            {"deltaMilli": -3500, "reason": "usage", "note": "Kitchen use"},
            actor_admin_user_id=None,
        )
        self.assertEqual(adjusted["quantityMilli"], 1500)
        self.assertTrue(adjusted["lowStock"])

        with self.assertRaises(AdminSoftwareConflict):
            self.kitchen.adjust_inventory(
                item["id"],
                {"deltaMilli": -2000, "reason": "usage"},
                actor_admin_user_id=None,
            )


if __name__ == "__main__":
    unittest.main()
