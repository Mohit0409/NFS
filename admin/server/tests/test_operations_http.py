from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import json
import time
import unittest

from server.gravity.admin import _totp_code
from server.gravity.config import Settings
from server.gravity.http import create_server


ROOT = Path(__file__).resolve().parents[2]
TEST_SECRET = "new-gym-operations-http-secret-key-long-enough"


@contextmanager
def running_server():
    with TemporaryDirectory() as temporary:
        runtime = Path(temporary)
        base = Settings.load(
            root_dir=ROOT,
            environ={
                "SECRET_KEY": TEST_SECRET,
                "GRAVITY_PORT": "0",
                "GRAVITY_LOG_LEVEL": "CRITICAL",
            },
        )
        settings = replace(
            base,
            data_dir=runtime / "data",
            log_dir=runtime / "logs",
            backup_dir=runtime / "backups",
            database_path=runtime / "data" / "new-gym.sqlite3",
            host="127.0.0.1",
            port=0,
        )
        server = create_server(settings)
        actual_base = f"http://127.0.0.1:{server.server_port}"
        server.settings = replace(server.settings, app_base_url=actual_base)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server, actual_base
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def request_json(base, path, *, method="GET", body=None, headers=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        base + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        response = urlopen(request, timeout=5)
        return response.status, json.loads(response.read() or b"{}")
    except HTTPError as error:
        return error.code, json.loads(error.read() or b"{}")


def owner_headers(server, base):
    owner = server.admin_service.bootstrap_owner("owner", "NewGym!Owner123")
    challenge = server.admin_service.begin_login(
        {"username": "owner", "password": "NewGym!Owner123"}, "127.0.0.1"
    )
    issue = server.admin_service.verify_second_factor(
        challenge.challenge_token,
        _totp_code(owner.totp_secret, int(time.time()) // 30),
        remote_addr="127.0.0.1",
        user_agent="NewGymOperationsHttpTest/1.0",
        request_id="new-gym-operations-http",
    )
    settings = server.settings
    return {
        "Cookie": (
            f"{settings.admin_session_cookie_name}={issue.session_token}; "
            f"{settings.admin_csrf_cookie_name}={issue.csrf_token}"
        ),
        "Origin": base,
        "X-CSRF-Token": issue.csrf_token,
    }


class OperationsHttpTests(unittest.TestCase):
    def test_pool_and_kitchen_workflow_is_authenticated_and_linked(self):
        with running_server() as (server, base):
            status, payload = request_json(base, "/api/admin/pool/tables")
            self.assertEqual((status, payload), (401, {"error": "admin_unauthenticated"}))

            headers = owner_headers(server, base)
            status, payload = request_json(base, "/api/admin/pool/tables", headers=headers)
            self.assertEqual(status, 200)
            self.assertEqual(len(payload["tables"]), 3)

            no_csrf = dict(headers)
            no_csrf.pop("X-CSRF-Token")
            status, payload = request_json(
                base,
                "/api/admin/pool/tables/pool-private-1",
                method="PATCH",
                body={"defaultRatePaise": 12000},
                headers=no_csrf,
            )
            self.assertEqual((status, payload), (403, {"error": "admin_forbidden"}))

            status, payload = request_json(
                base,
                "/api/admin/pool/tables/pool-private-1",
                method="PATCH",
                body={"defaultRatePaise": 12000},
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["table"]["defaultRatePaise"], 12000)

            status, payload = request_json(
                base,
                "/api/admin/pool/sessions",
                method="POST",
                body={"tableId": "pool-private-1", "guestName": "Walk-in"},
                headers=headers,
            )
            self.assertEqual(status, 201)
            pool_session_id = payload["session"]["id"]

            status, payload = request_json(
                base,
                "/api/admin/kitchen/menu",
                method="POST",
                body={"name": "Cold Coffee", "category": "Drinks", "pricePaise": 8000},
                headers=headers,
            )
            self.assertEqual(status, 201)
            menu_item_id = payload["item"]["id"]

            status, payload = request_json(
                base,
                "/api/admin/kitchen/orders",
                method="POST",
                body={
                    "poolSessionId": pool_session_id,
                    "customerName": "Walk-in",
                    "items": [{"menuItemId": menu_item_id, "quantity": 2}],
                },
                headers=headers,
            )
            self.assertEqual(status, 201)
            order = payload["order"]
            self.assertEqual(order["poolSessionId"], pool_session_id)
            self.assertEqual(order["totalPaise"], 16000)

            order_id = order["id"]
            for expected in ("preparing", "ready", "served"):
                status, payload = request_json(
                    base,
                    f"/api/admin/kitchen/orders/{order_id}",
                    method="PATCH",
                    body={"status": expected},
                    headers=headers,
                )
                self.assertEqual(status, 200)
                self.assertEqual(payload["order"]["status"], expected)

            status, payload = request_json(
                base,
                f"/api/admin/pool/sessions/{pool_session_id}/end",
                method="POST",
                body={"amountPaise": 6000},
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["session"]["status"], "completed")
            self.assertEqual(payload["session"]["amountPaise"], 6000)

            status, payload = request_json(
                base,
                f"/api/admin/pool/sessions/{pool_session_id}/bill",
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["bill"]["poolChargePaise"], 6000)
            self.assertEqual(payload["bill"]["kitchenTotalPaise"], 16000)
            self.assertEqual(payload["bill"]["grandTotalPaise"], 22000)
            self.assertEqual(payload["bill"]["duePaise"], 22000)
            self.assertTrue(payload["bill"]["settlementReady"])

            status, payload = request_json(
                base,
                f"/api/admin/pool/sessions/{pool_session_id}/settle",
                method="POST",
                body={"paymentMethod": "cash"},
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["bill"]["duePaise"], 0)
            self.assertEqual(payload["bill"]["paidPaise"], 22000)
            self.assertEqual(payload["bill"]["session"]["paymentStatus"], "paid")
            self.assertEqual(payload["bill"]["session"]["paymentMethod"], "cash")

            status, payload = request_json(
                base,
                "/api/admin/operations/report",
                headers=headers,
            )
            self.assertEqual(status, 200)
            report = payload["report"]
            self.assertEqual(report["summary"]["completedPoolSessions"], 1)
            self.assertEqual(report["summary"]["poolBilledPaise"], 6000)
            self.assertEqual(report["summary"]["kitchenSalesPaise"], 16000)
            self.assertEqual(report["summary"]["settledRevenuePaise"], 22000)
            self.assertEqual(report["summary"]["outstandingPaise"], 0)

    def test_invalid_pool_and_kitchen_inputs_fail_closed(self):
        with running_server() as (server, base):
            headers = owner_headers(server, base)

            status, payload = request_json(
                base,
                "/api/admin/pool/sessions",
                method="POST",
                body={"tableId": "pool-common-1"},
                headers=headers,
            )
            self.assertEqual(status, 422)
            self.assertEqual(payload["error"], "operations_validation")

            status, payload = request_json(
                base,
                "/api/admin/kitchen/orders",
                method="POST",
                body={"items": []},
                headers=headers,
            )
            self.assertEqual(status, 422)
            self.assertEqual(payload["error"], "operations_validation")

            status, payload = request_json(
                base,
                "/api/admin/kitchen/menu",
                method="POST",
                body={"name": "Tea", "category": "Drinks", "pricePaise": 5000},
                headers=headers,
            )
            self.assertEqual(status, 201)
            menu_id = payload["item"]["id"]
            status, payload = request_json(
                base,
                "/api/admin/kitchen/orders",
                method="POST",
                body={"items": [{"menuItemId": menu_id, "quantity": 1}]},
                headers=headers,
            )
            self.assertEqual(status, 201)
            order_id = payload["order"]["id"]

            status, payload = request_json(
                base,
                f"/api/admin/kitchen/orders/{order_id}",
                method="PATCH",
                body={"status": "cancelled"},
                headers=headers,
            )
            self.assertEqual(status, 422)
            self.assertEqual(payload["error"], "operations_validation")

            status, payload = request_json(
                base,
                f"/api/admin/kitchen/orders/{order_id}",
                method="PATCH",
                body={"status": "cancelled", "cancelReason": "Customer changed order"},
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["order"]["status"], "cancelled")
            self.assertEqual(payload["order"]["paymentStatus"], "void")
            self.assertEqual(payload["order"]["cancelReason"], "Customer changed order")
            self.assertIsNotNone(payload["order"]["cancelledAt"])

            status, payload = request_json(
                base,
                "/api/admin/kitchen/orders",
                method="POST",
                body={"items": [{"menuItemId": menu_id, "quantity": 1}]},
                headers=headers,
            )
            self.assertEqual(status, 201)
            paid_order_id = payload["order"]["id"]

            status, payload = request_json(
                base,
                f"/api/admin/kitchen/orders/{paid_order_id}",
                method="PATCH",
                body={"paymentStatus": "paid", "paymentMethod": "upi"},
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["order"]["paymentStatus"], "paid")

            status, payload = request_json(
                base,
                f"/api/admin/kitchen/orders/{paid_order_id}",
                method="PATCH",
                body={"paymentStatus": "void"},
                headers=headers,
            )
            self.assertEqual(status, 422)
            self.assertEqual(payload["error"], "operations_validation")

            status, payload = request_json(
                base,
                f"/api/admin/kitchen/orders/{paid_order_id}",
                method="PATCH",
                body={
                    "paymentStatus": "void",
                    "paymentVoidReason": "UPI payment reversed",
                },
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["order"]["paymentStatus"], "void")
            self.assertEqual(payload["order"]["paymentMethod"], "upi")
            self.assertEqual(payload["order"]["paymentVoidReason"], "UPI payment reversed")
            self.assertIsNotNone(payload["order"]["paymentVoidedAt"])


    def test_pool_reservation_and_inventory_http_workflows(self):
        with running_server() as (server, base):
            headers = owner_headers(server, base)
            now = int(time.time())

            status, payload = request_json(
                base,
                "/api/admin/pool/reservations",
                method="POST",
                body={
                    "tableId": "pool-common-1",
                    "guestName": "Reserved Guest",
                    "phone": "9876543210",
                    "startsAt": now + 600,
                    "endsAt": now + 4200,
                    "ratePaisePerHour": 10000,
                },
                headers=headers,
            )
            self.assertEqual(status, 201)
            reservation = payload["reservation"]
            self.assertEqual(reservation["status"], "reserved")

            status, payload = request_json(
                base,
                "/api/admin/pool/reservations?status=reserved",
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertTrue(any(item["id"] == reservation["id"] for item in payload["reservations"]))

            status, payload = request_json(
                base,
                f"/api/admin/pool/reservations/{reservation['id']}",
                method="PATCH",
                body={
                    "tableId": "pool-common-2",
                    "guestName": "Reserved Guest Updated",
                    "phone": "9123456789",
                    "startsAt": now + 900,
                    "endsAt": now + 4500,
                    "ratePaisePerHour": 11000,
                    "note": "Rescheduled by reception",
                },
                headers=headers,
            )
            self.assertEqual(status, 200)
            reservation = payload["reservation"]
            self.assertEqual(reservation["tableId"], "pool-common-2")
            self.assertEqual(reservation["guestName"], "Reserved Guest Updated")
            self.assertEqual(reservation["phone"], "+919123456789")
            self.assertEqual(reservation["startsAt"], now + 900)
            self.assertEqual(reservation["endsAt"], now + 4500)
            self.assertEqual(reservation["ratePaisePerHour"], 11000)
            self.assertEqual(reservation["note"], "Rescheduled by reception")

            status, payload = request_json(
                base,
                "/api/admin/pool/sessions",
                method="POST",
                body={"reservationId": reservation["id"]},
                headers=headers,
            )
            self.assertEqual(status, 201)
            self.assertEqual(payload["session"]["reservationId"], reservation["id"])

            status, payload = request_json(
                base,
                "/api/admin/kitchen/inventory",
                method="POST",
                body={
                    "name": "Milk",
                    "unit": "litre",
                    "quantityMilli": 5000,
                    "lowStockMilli": 2000,
                },
                headers=headers,
            )
            self.assertEqual(status, 201)
            stock_id = payload["item"]["id"]
            self.assertFalse(payload["item"]["lowStock"])

            status, payload = request_json(
                base,
                "/api/admin/kitchen/menu",
                method="POST",
                body={"name": "Cold Coffee", "category": "Drinks", "pricePaise": 8000},
                headers=headers,
            )
            self.assertEqual(status, 201)
            menu_id = payload["item"]["id"]

            status, payload = request_json(
                base,
                "/api/admin/kitchen/recipes",
                method="POST",
                body={
                    "menuItemId": menu_id,
                    "inventoryItemId": stock_id,
                    "quantityMilli": 250,
                },
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["recipe"]["quantityMilli"], 250)

            status, payload = request_json(
                base,
                f"/api/admin/kitchen/recipes?menuItemId={menu_id}",
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(len(payload["recipes"]), 1)
            self.assertEqual(payload["recipes"][0]["inventoryItemId"], stock_id)

            status, payload = request_json(
                base,
                f"/api/admin/kitchen/inventory/{stock_id}/adjust",
                method="POST",
                body={"deltaMilli": -3500, "reason": "usage"},
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["item"]["quantityMilli"], 1500)
            self.assertTrue(payload["item"]["lowStock"])

            status, payload = request_json(
                base,
                f"/api/admin/kitchen/inventory/{stock_id}/adjust",
                method="POST",
                body={"deltaMilli": -2000, "reason": "usage"},
                headers=headers,
            )
            self.assertEqual(status, 409)
            self.assertEqual(payload["error"], "operations_conflict")


if __name__ == "__main__":
    unittest.main()
