from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from server.gravity.admin_software import AdminSoftwareConflict, AdminSoftwareValidationError
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

    def test_pool_reservation_can_be_rescheduled_without_overlap(self):
        first = self.pool.create_reservation(
            {
                "tableId": "pool-common-1",
                "guestName": "First Guest",
                "startsAt": self.clock_value + 1800,
                "endsAt": self.clock_value + 3600,
                "ratePaisePerHour": 10000,
            },
            actor_admin_user_id=None,
        )
        second = self.pool.create_reservation(
            {
                "tableId": "pool-common-2",
                "guestName": "Second Guest",
                "startsAt": self.clock_value + 3600,
                "endsAt": self.clock_value + 5400,
                "ratePaisePerHour": 11000,
            },
            actor_admin_user_id=None,
        )

        updated = self.pool.update_reservation(
            first["id"],
            {
                "tableId": "pool-common-2",
                "guestName": "First Guest Updated",
                "startsAt": self.clock_value + 600,
                "endsAt": self.clock_value + 1800,
                "ratePaisePerHour": 11500,
                "note": "Shifted earlier",
            },
            actor_admin_user_id=None,
        )
        self.assertEqual(updated["tableId"], "pool-common-2")
        self.assertEqual(updated["guestName"], "First Guest Updated")
        self.assertEqual(updated["startsAt"], self.clock_value + 600)
        self.assertEqual(updated["endsAt"], self.clock_value + 1800)
        self.assertEqual(updated["ratePaisePerHour"], 11500)
        self.assertEqual(updated["note"], "Shifted earlier")

        with self.assertRaises(AdminSoftwareConflict):
            self.pool.update_reservation(
                first["id"],
                {
                    "tableId": "pool-common-2",
                    "startsAt": second["startsAt"] + 300,
                    "endsAt": second["endsAt"] - 300,
                },
                actor_admin_user_id=None,
            )

    def test_checked_in_pool_reservation_cannot_be_edited(self):
        reservation = self.pool.create_reservation(
            {
                "tableId": "pool-private-1",
                "guestName": "Locked Guest",
                "startsAt": self.clock_value + 300,
                "endsAt": self.clock_value + 3900,
                "ratePaisePerHour": 12000,
            },
            actor_admin_user_id=None,
        )
        self.clock_value += 300
        self.pool.start_session(
            {"reservationId": reservation["id"]},
            actor_admin_user_id=None,
        )
        with self.assertRaises(AdminSoftwareConflict):
            self.pool.update_reservation(
                reservation["id"],
                {"guestName": "Should Not Change"},
                actor_admin_user_id=None,
            )

    def test_combined_pool_kitchen_bill_settles_atomically(self):
        session = self.pool.start_session(
            {
                "tableId": "pool-common-2",
                "ratePaisePerHour": 10000,
                "guestName": "Billing Guest",
            },
            actor_admin_user_id=None,
        )
        item = self.kitchen.create_menu_item(
            {"name": "Protein Shake", "category": "Drinks", "pricePaise": 8000},
            actor_admin_user_id=None,
        )
        order = self.kitchen.create_order(
            {
                "poolSessionId": session["id"],
                "items": [{"menuItemId": item["id"], "quantity": 2}],
            },
            actor_admin_user_id=None,
        )

        self.clock_value += 3600
        completed = self.pool.end_session(session["id"], {}, actor_admin_user_id=None)
        self.assertEqual(completed["amountPaise"], 10000)

        bill = self.pool.get_bill(session["id"])
        self.assertEqual(bill["poolChargePaise"], 10000)
        self.assertEqual(bill["kitchenTotalPaise"], 16000)
        self.assertEqual(bill["grandTotalPaise"], 26000)
        self.assertEqual(bill["duePaise"], 26000)
        self.assertFalse(bill["settlementReady"])

        with self.assertRaises(AdminSoftwareConflict):
            self.pool.settle_session(
                session["id"],
                {"paymentMethod": "cash"},
                actor_admin_user_id=None,
            )

        for status in ("preparing", "ready", "served"):
            self.kitchen.update_order(
                order["id"], {"status": status}, actor_admin_user_id=None
            )

        settled = self.pool.settle_session(
            session["id"],
            {"paymentMethod": "upi"},
            actor_admin_user_id=None,
        )
        self.assertTrue(settled["settlementReady"])
        self.assertEqual(settled["duePaise"], 0)
        self.assertEqual(settled["paidPaise"], 26000)
        self.assertEqual(settled["session"]["paymentStatus"], "paid")
        self.assertEqual(settled["session"]["paymentMethod"], "upi")
        self.assertEqual(settled["kitchenOrders"][0]["paymentStatus"], "paid")
        self.assertEqual(settled["kitchenOrders"][0]["paymentMethod"], "upi")

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


    def test_kitchen_recipe_auto_deducts_inventory_once_when_served(self):
        stock = self.kitchen.create_inventory_item(
            {
                "name": "Milk",
                "unit": "litre",
                "quantityMilli": 5000,
                "lowStockMilli": 1000,
            },
            actor_admin_user_id=None,
        )
        menu = self.kitchen.create_menu_item(
            {"name": "Cold Coffee", "category": "Drinks", "pricePaise": 8000},
            actor_admin_user_id=None,
        )
        recipe = self.kitchen.upsert_recipe(
            {
                "menuItemId": menu["id"],
                "inventoryItemId": stock["id"],
                "quantityMilli": 250,
            },
            actor_admin_user_id=None,
        )
        self.assertEqual(recipe["quantityMilli"], 250)

        order = self.kitchen.create_order(
            {
                "items": [{"menuItemId": menu["id"], "quantity": 2}],
            },
            actor_admin_user_id=None,
        )
        for status in ("preparing", "ready", "served"):
            self.kitchen.update_order(
                order["id"],
                {"status": status},
                actor_admin_user_id=None,
            )

        current = next(item for item in self.kitchen.list_inventory() if item["id"] == stock["id"])
        self.assertEqual(current["quantityMilli"], 4500)

        # Repeating the same terminal state must not deduct a second time.
        self.kitchen.update_order(
            order["id"],
            {"status": "served"},
            actor_admin_user_id=None,
        )
        current = next(item for item in self.kitchen.list_inventory() if item["id"] == stock["id"])
        self.assertEqual(current["quantityMilli"], 4500)

        with self.database.session() as connection:
            usage = connection.execute(
                "SELECT quantity_milli FROM kitchen_order_inventory_usage"
            ).fetchall()
            movements = connection.execute(
                "SELECT delta_milli,reason FROM kitchen_inventory_movements "
                "WHERE item_id=? AND reason='usage'",
                (stock["id"],),
            ).fetchall()
        self.assertEqual([int(row["quantity_milli"]) for row in usage], [500])
        self.assertEqual([(int(row["delta_milli"]), row["reason"]) for row in movements], [(-500, "usage")])

    def test_kitchen_recipe_blocks_serving_if_stock_is_insufficient(self):
        stock = self.kitchen.create_inventory_item(
            {
                "name": "Protein Powder",
                "unit": "kg",
                "quantityMilli": 500,
                "lowStockMilli": 200,
            },
            actor_admin_user_id=None,
        )
        menu = self.kitchen.create_menu_item(
            {"name": "Protein Shake", "category": "Drinks", "pricePaise": 12000},
            actor_admin_user_id=None,
        )
        self.kitchen.upsert_recipe(
            {
                "menuItemId": menu["id"],
                "inventoryItemId": stock["id"],
                "quantityMilli": 600,
            },
            actor_admin_user_id=None,
        )
        order = self.kitchen.create_order(
            {"items": [{"menuItemId": menu["id"], "quantity": 1}]},
            actor_admin_user_id=None,
        )
        for status in ("preparing", "ready"):
            self.kitchen.update_order(
                order["id"],
                {"status": status},
                actor_admin_user_id=None,
            )

        with self.assertRaises(AdminSoftwareConflict):
            self.kitchen.update_order(
                order["id"],
                {"status": "served"},
                actor_admin_user_id=None,
            )

        stored = next(item for item in self.kitchen.list_orders() if item["id"] == order["id"])
        current = next(item for item in self.kitchen.list_inventory() if item["id"] == stock["id"])
        self.assertEqual(stored["status"], "ready")
        self.assertEqual(current["quantityMilli"], 500)

    def test_kitchen_order_cancellation_requires_reason_and_voids_unpaid_order(self):
        menu = self.kitchen.create_menu_item(
            {"name": "Cancelled Coffee", "category": "Drinks", "pricePaise": 8000},
            actor_admin_user_id=None,
        )
        order = self.kitchen.create_order(
            {"items": [{"menuItemId": menu["id"], "quantity": 1}]},
            actor_admin_user_id=None,
        )

        with self.assertRaises(AdminSoftwareValidationError):
            self.kitchen.update_order(
                order["id"],
                {"status": "cancelled"},
                actor_admin_user_id=None,
            )

        cancelled = self.kitchen.update_order(
            order["id"],
            {"status": "cancelled", "cancelReason": "Customer changed order"},
            actor_admin_user_id=None,
        )
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(cancelled["paymentStatus"], "void")
        self.assertIsNone(cancelled["paymentMethod"])
        self.assertEqual(cancelled["cancelReason"], "Customer changed order")
        self.assertEqual(cancelled["cancelledAt"], self.clock_value)

    def test_paid_kitchen_order_cannot_be_cancelled_until_payment_is_voided(self):
        menu = self.kitchen.create_menu_item(
            {"name": "Paid Tea", "category": "Drinks", "pricePaise": 5000},
            actor_admin_user_id=None,
        )
        order = self.kitchen.create_order(
            {"items": [{"menuItemId": menu["id"], "quantity": 1}]},
            actor_admin_user_id=None,
        )
        self.kitchen.update_order(
            order["id"],
            {"paymentStatus": "paid", "paymentMethod": "cash"},
            actor_admin_user_id=None,
        )
        with self.assertRaises(AdminSoftwareConflict):
            self.kitchen.update_order(
                order["id"],
                {"status": "cancelled", "cancelReason": "Customer changed order"},
                actor_admin_user_id=None,
            )
        with self.assertRaises(AdminSoftwareValidationError):
            self.kitchen.update_order(
                order["id"],
                {"paymentStatus": "void"},
                actor_admin_user_id=None,
            )
        with self.assertRaises(AdminSoftwareConflict):
            self.kitchen.update_order(
                order["id"],
                {"paymentStatus": "unpaid"},
                actor_admin_user_id=None,
            )

        voided = self.kitchen.update_order(
            order["id"],
            {
                "paymentStatus": "void",
                "paymentVoidReason": "Cash entry reversed",
            },
            actor_admin_user_id=None,
        )
        self.assertEqual(voided["paymentStatus"], "void")
        self.assertEqual(voided["paymentMethod"], "cash")
        self.assertIsNone(voided["paidAt"])
        self.assertEqual(voided["paymentVoidReason"], "Cash entry reversed")
        self.assertEqual(voided["paymentVoidedAt"], self.clock_value)

        with self.assertRaises(AdminSoftwareConflict):
            self.kitchen.update_order(
                order["id"],
                {"status": "preparing"},
                actor_admin_user_id=None,
            )

        cancelled = self.kitchen.update_order(
            order["id"],
            {"status": "cancelled", "cancelReason": "Customer changed order"},
            actor_admin_user_id=None,
        )
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(cancelled["paymentStatus"], "void")
        self.assertEqual(cancelled["paymentMethod"], "cash")
        self.assertEqual(cancelled["paymentVoidReason"], "Cash entry reversed")

    def test_settled_pool_bill_locks_linked_kitchen_payment_from_void(self):
        session = self.pool.start_session(
            {
                "tableId": "pool-common-2",
                "ratePaisePerHour": 10000,
                "guestName": "Locked Bill Guest",
            },
            actor_admin_user_id=None,
        )
        menu = self.kitchen.create_menu_item(
            {"name": "Locked Coffee", "category": "Drinks", "pricePaise": 7000},
            actor_admin_user_id=None,
        )
        order = self.kitchen.create_order(
            {
                "poolSessionId": session["id"],
                "items": [{"menuItemId": menu["id"], "quantity": 1}],
            },
            actor_admin_user_id=None,
        )
        for status in ("preparing", "ready", "served"):
            self.kitchen.update_order(
                order["id"],
                {"status": status},
                actor_admin_user_id=None,
            )
        self.kitchen.update_order(
            order["id"],
            {"paymentStatus": "paid", "paymentMethod": "upi"},
            actor_admin_user_id=None,
        )
        with self.assertRaises(AdminSoftwareConflict):
            self.kitchen.update_order(
                order["id"],
                {
                    "paymentStatus": "void",
                    "paymentVoidReason": "Served linked order cannot be voided",
                },
                actor_admin_user_id=None,
            )
        self.clock_value += 1800
        self.pool.end_session(session["id"], {}, actor_admin_user_id=None)
        self.pool.settle_session(
            session["id"],
            {"paymentMethod": "upi"},
            actor_admin_user_id=None,
        )

        with self.assertRaises(AdminSoftwareConflict):
            self.kitchen.update_order(
                order["id"],
                {
                    "paymentStatus": "void",
                    "paymentVoidReason": "Should be locked",
                },
                actor_admin_user_id=None,
            )

    def test_voided_unserved_pool_order_blocks_final_settlement_until_cancelled(self):
        session = self.pool.start_session(
            {
                "tableId": "pool-private-1",
                "ratePaisePerHour": 12000,
                "guestName": "Void Block Guest",
            },
            actor_admin_user_id=None,
        )
        menu = self.kitchen.create_menu_item(
            {"name": "Void Block Tea", "category": "Drinks", "pricePaise": 5000},
            actor_admin_user_id=None,
        )
        order = self.kitchen.create_order(
            {
                "poolSessionId": session["id"],
                "items": [{"menuItemId": menu["id"], "quantity": 1}],
            },
            actor_admin_user_id=None,
        )
        self.kitchen.update_order(
            order["id"],
            {"paymentStatus": "paid", "paymentMethod": "cash"},
            actor_admin_user_id=None,
        )
        voided = self.kitchen.update_order(
            order["id"],
            {
                "paymentStatus": "void",
                "paymentVoidReason": "Cash entry reversed",
            },
            actor_admin_user_id=None,
        )
        self.assertEqual(voided["paymentStatus"], "void")

        self.clock_value += 1800
        self.pool.end_session(session["id"], {}, actor_admin_user_id=None)
        bill = self.pool.get_bill(session["id"])
        self.assertFalse(bill["settlementReady"])
        self.assertIn(order["id"], bill["blockingKitchenOrderIds"])
        with self.assertRaises(AdminSoftwareConflict):
            self.pool.settle_session(
                session["id"],
                {"paymentMethod": "cash"},
                actor_admin_user_id=None,
            )

        self.kitchen.update_order(
            order["id"],
            {"status": "cancelled", "cancelReason": "Payment voided; order cancelled"},
            actor_admin_user_id=None,
        )
        bill = self.pool.get_bill(session["id"])
        self.assertTrue(bill["settlementReady"])
        settled = self.pool.settle_session(
            session["id"],
            {"paymentMethod": "cash"},
            actor_admin_user_id=None,
        )
        self.assertEqual(settled["duePaise"], 0)

    def test_cancelling_ready_recipe_order_does_not_consume_inventory(self):
        stock = self.kitchen.create_inventory_item(
            {"name": "Cancellation Milk", "unit": "litre", "quantityMilli": 3000, "lowStockMilli": 500},
            actor_admin_user_id=None,
        )
        menu = self.kitchen.create_menu_item(
            {"name": "Cancellation Shake", "category": "Drinks", "pricePaise": 9000},
            actor_admin_user_id=None,
        )
        self.kitchen.upsert_recipe(
            {
                "menuItemId": menu["id"],
                "inventoryItemId": stock["id"],
                "quantityMilli": 250,
            },
            actor_admin_user_id=None,
        )
        order = self.kitchen.create_order(
            {"items": [{"menuItemId": menu["id"], "quantity": 2}]},
            actor_admin_user_id=None,
        )
        for status in ("preparing", "ready"):
            self.kitchen.update_order(
                order["id"],
                {"status": status},
                actor_admin_user_id=None,
            )
        cancelled = self.kitchen.update_order(
            order["id"],
            {"status": "cancelled", "cancelReason": "Guest left"},
            actor_admin_user_id=None,
        )
        self.assertEqual(cancelled["status"], "cancelled")
        current = next(item for item in self.kitchen.list_inventory() if item["id"] == stock["id"])
        self.assertEqual(current["quantityMilli"], 3000)
        with self.database.session() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM kitchen_order_inventory_usage WHERE inventory_item_id=?",
                    (stock["id"],),
                ).fetchone()[0],
                0,
            )

    def test_kitchen_recipe_can_be_removed_with_zero_quantity(self):
        stock = self.kitchen.create_inventory_item(
            {"name": "Bread", "unit": "piece", "quantityMilli": 10000, "lowStockMilli": 2000},
            actor_admin_user_id=None,
        )
        menu = self.kitchen.create_menu_item(
            {"name": "Sandwich", "category": "Snacks", "pricePaise": 10000},
            actor_admin_user_id=None,
        )
        self.kitchen.upsert_recipe(
            {
                "menuItemId": menu["id"],
                "inventoryItemId": stock["id"],
                "quantityMilli": 2000,
            },
            actor_admin_user_id=None,
        )
        removed = self.kitchen.upsert_recipe(
            {
                "menuItemId": menu["id"],
                "inventoryItemId": stock["id"],
                "quantityMilli": 0,
            },
            actor_admin_user_id=None,
        )
        self.assertTrue(removed["removed"])
        self.assertEqual(self.kitchen.list_recipes(menu_item_id=menu["id"]), [])


if __name__ == "__main__":
    unittest.main()
