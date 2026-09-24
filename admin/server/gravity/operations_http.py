from __future__ import annotations

from http import HTTPStatus
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .admin import AdminCsrfInvalid, AdminForbidden, AdminSessionInvalid
from .admin_software import (
    AdminSoftwareConflict,
    AdminSoftwareNotFound,
    AdminSoftwareValidationError,
)

OPERATIONS_JSON_LIMIT = 32_768


def _json(handler: Any, status: HTTPStatus, payload: dict[str, object], request_id: str, send_body: bool) -> HTTPStatus:
    handler._json_response(status, payload, request_id=request_id, send_body=send_body)
    return status


def _session(handler: Any):
    token = handler._cookie_value(handler.server.settings.admin_session_cookie_name)
    return handler.server.admin_service.resolve_session(token)


def _authenticated(handler: Any, request_id: str, send_body: bool):
    try:
        return _session(handler), None
    except AdminSessionInvalid:
        return None, _json(handler, HTTPStatus.UNAUTHORIZED, {"error": "admin_unauthenticated"}, request_id, send_body)


def _require_write(handler: Any, session, permission: str) -> None:
    if not handler._same_origin():
        raise AdminForbidden("Invalid request origin")
    handler.server.admin_service.require_permission(session, permission)
    values = handler.headers.get_all("X-CSRF-Token", [])
    if len(values) != 1:
        raise AdminCsrfInvalid("Administrator CSRF verification failed")
    cookie = handler._cookie_value(handler.server.settings.admin_csrf_cookie_name)
    handler.server.admin_service.verify_csrf(session, values[0], cookie)


def _error(handler: Any, error: Exception, request_id: str, send_body: bool) -> HTTPStatus:
    if isinstance(error, AdminSessionInvalid):
        return _json(handler, HTTPStatus.UNAUTHORIZED, {"error": "admin_unauthenticated"}, request_id, send_body)
    if isinstance(error, (AdminCsrfInvalid, AdminForbidden)):
        return _json(handler, HTTPStatus.FORBIDDEN, {"error": "admin_forbidden"}, request_id, send_body)
    if isinstance(error, AdminSoftwareNotFound):
        return _json(handler, HTTPStatus.NOT_FOUND, {"error": "operations_not_found"}, request_id, send_body)
    if isinstance(error, AdminSoftwareConflict):
        return _json(handler, HTTPStatus.CONFLICT, {"error": "operations_conflict", "message": str(error)}, request_id, send_body)
    if isinstance(error, AdminSoftwareValidationError):
        return _json(
            handler, HTTPStatus.UNPROCESSABLE_ENTITY,
            {"error": "operations_validation", "fields": error.fields},
            request_id, send_body,
        )
    raise error


def _pool_tables(handler: Any, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    handler.server.admin_service.require_permission(session, "pool.read")
    return _json(handler, HTTPStatus.OK, {"tables": handler.server.pool_service.list_tables()}, request_id, send_body)


def _pool_table_update(handler: Any, table_id: str, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    _require_write(handler, session, "pool.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    table = handler.server.pool_service.update_table(
        table_id, payload, actor_admin_user_id=session.admin_user_id
    )
    return _json(handler, HTTPStatus.OK, {"table": table}, request_id, send_body)


def _pool_sessions(handler: Any, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    if handler.command in {"GET", "HEAD"}:
        handler.server.admin_service.require_permission(session, "pool.read")
        params = parse_qs(urlsplit(handler.path).query)
        rows = handler.server.pool_service.list_sessions(
            status=params.get("status", [""])[0] or None,
            limit=params.get("limit", ["100"])[0],
        )
        return _json(handler, HTTPStatus.OK, {"sessions": rows}, request_id, send_body)
    _require_write(handler, session, "pool.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    item = handler.server.pool_service.start_session(
        payload, actor_admin_user_id=session.admin_user_id
    )
    return _json(handler, HTTPStatus.CREATED, {"session": item}, request_id, send_body)


def _pool_end(handler: Any, session_id: str, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    _require_write(handler, session, "pool.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    item = handler.server.pool_service.end_session(
        session_id, payload, actor_admin_user_id=session.admin_user_id
    )
    return _json(handler, HTTPStatus.OK, {"session": item}, request_id, send_body)


def _pool_bill(handler: Any, session_id: str, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    handler.server.admin_service.require_permission(session, "pool.read")
    bill = handler.server.pool_service.get_bill(session_id)
    return _json(handler, HTTPStatus.OK, {"bill": bill}, request_id, send_body)


def _pool_settle(handler: Any, session_id: str, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    _require_write(handler, session, "pool.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    bill = handler.server.pool_service.settle_session(
        session_id, payload, actor_admin_user_id=session.admin_user_id
    )
    return _json(handler, HTTPStatus.OK, {"bill": bill}, request_id, send_body)


def _pool_reservations(handler: Any, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    if handler.command in {"GET", "HEAD"}:
        handler.server.admin_service.require_permission(session, "pool.read")
        params = parse_qs(urlsplit(handler.path).query)
        rows = handler.server.pool_service.list_reservations(
            status=params.get("status", [""])[0] or None,
            from_at=params.get("fromAt", [""])[0] or None,
            to_at=params.get("toAt", [""])[0] or None,
            limit=params.get("limit", ["100"])[0],
        )
        return _json(handler, HTTPStatus.OK, {"reservations": rows}, request_id, send_body)
    _require_write(handler, session, "pool.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    item = handler.server.pool_service.create_reservation(
        payload, actor_admin_user_id=session.admin_user_id
    )
    return _json(handler, HTTPStatus.CREATED, {"reservation": item}, request_id, send_body)


def _pool_reservation_update(
    handler: Any,
    reservation_id: str,
    request_id: str,
    send_body: bool,
) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    _require_write(handler, session, "pool.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    item = handler.server.pool_service.update_reservation_status(
        reservation_id,
        str(payload.get("status") or ""),
        actor_admin_user_id=session.admin_user_id,
    )
    return _json(handler, HTTPStatus.OK, {"reservation": item}, request_id, send_body)


def _kitchen_menu(handler: Any, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    if handler.command in {"GET", "HEAD"}:
        handler.server.admin_service.require_permission(session, "kitchen.read")
        return _json(handler, HTTPStatus.OK, {"items": handler.server.kitchen_service.list_menu()}, request_id, send_body)
    _require_write(handler, session, "kitchen.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    item = handler.server.kitchen_service.create_menu_item(
        payload, actor_admin_user_id=session.admin_user_id
    )
    return _json(handler, HTTPStatus.CREATED, {"item": item}, request_id, send_body)


def _kitchen_menu_update(handler: Any, item_id: str, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    _require_write(handler, session, "kitchen.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    item = handler.server.kitchen_service.update_menu_item(
        item_id, payload, actor_admin_user_id=session.admin_user_id
    )
    return _json(handler, HTTPStatus.OK, {"item": item}, request_id, send_body)


def _kitchen_orders(handler: Any, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    if handler.command in {"GET", "HEAD"}:
        handler.server.admin_service.require_permission(session, "kitchen.read")
        params = parse_qs(urlsplit(handler.path).query)
        rows = handler.server.kitchen_service.list_orders(
            status=params.get("status", [""])[0] or None,
            limit=params.get("limit", ["100"])[0],
        )
        return _json(handler, HTTPStatus.OK, {"orders": rows}, request_id, send_body)
    _require_write(handler, session, "kitchen.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    order = handler.server.kitchen_service.create_order(
        payload, actor_admin_user_id=session.admin_user_id
    )
    return _json(handler, HTTPStatus.CREATED, {"order": order}, request_id, send_body)


def _kitchen_order_update(handler: Any, order_id: str, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    _require_write(handler, session, "kitchen.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    order = handler.server.kitchen_service.update_order(
        order_id, payload, actor_admin_user_id=session.admin_user_id
    )
    return _json(handler, HTTPStatus.OK, {"order": order}, request_id, send_body)


def _kitchen_inventory(handler: Any, request_id: str, send_body: bool) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    if handler.command in {"GET", "HEAD"}:
        handler.server.admin_service.require_permission(session, "kitchen.read")
        rows = handler.server.kitchen_service.list_inventory()
        return _json(handler, HTTPStatus.OK, {"items": rows}, request_id, send_body)
    _require_write(handler, session, "kitchen.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    item = handler.server.kitchen_service.create_inventory_item(
        payload, actor_admin_user_id=session.admin_user_id
    )
    return _json(handler, HTTPStatus.CREATED, {"item": item}, request_id, send_body)


def _kitchen_inventory_adjust(
    handler: Any,
    item_id: str,
    request_id: str,
    send_body: bool,
) -> HTTPStatus:
    session, failure = _authenticated(handler, request_id, send_body)
    if session is None:
        return failure
    _require_write(handler, session, "kitchen.manage")
    payload = handler._json_body(maximum=OPERATIONS_JSON_LIMIT)
    item = handler.server.kitchen_service.adjust_inventory(
        item_id, payload, actor_admin_user_id=session.admin_user_id
    )
    return _json(handler, HTTPStatus.OK, {"item": item}, request_id, send_body)


def handle_operations_request(handler: Any, path: str, request_id: str, send_body: bool) -> HTTPStatus | None:
    if not (path.startswith("/api/admin/pool") or path.startswith("/api/admin/kitchen")):
        return None
    try:
        if path == "/api/admin/pool/tables":
            if handler.command in {"GET", "HEAD"}:
                return _pool_tables(handler, request_id, send_body)
            return handler._method_not_allowed({"GET", "HEAD"}, request_id, send_body)
        if path.startswith("/api/admin/pool/tables/"):
            table_id = path.removeprefix("/api/admin/pool/tables/").strip("/")
            if table_id and "/" not in table_id:
                if handler.command == "PATCH":
                    return _pool_table_update(handler, table_id, request_id, send_body)
                return handler._method_not_allowed({"PATCH"}, request_id, send_body)
        if path == "/api/admin/pool/reservations":
            if handler.command in {"GET", "HEAD", "POST"}:
                return _pool_reservations(handler, request_id, send_body)
            return handler._method_not_allowed({"GET", "HEAD", "POST"}, request_id, send_body)
        if path.startswith("/api/admin/pool/reservations/"):
            reservation_id = path.removeprefix("/api/admin/pool/reservations/").strip("/")
            if reservation_id and "/" not in reservation_id:
                if handler.command == "PATCH":
                    return _pool_reservation_update(handler, reservation_id, request_id, send_body)
                return handler._method_not_allowed({"PATCH"}, request_id, send_body)
        if path == "/api/admin/pool/sessions":
            if handler.command in {"GET", "HEAD", "POST"}:
                return _pool_sessions(handler, request_id, send_body)
            return handler._method_not_allowed({"GET", "HEAD", "POST"}, request_id, send_body)
        if path.startswith("/api/admin/pool/sessions/") and path.endswith("/bill"):
            session_id = path.removeprefix("/api/admin/pool/sessions/").removesuffix("/bill").strip("/")
            if session_id and "/" not in session_id:
                if handler.command in {"GET", "HEAD"}:
                    return _pool_bill(handler, session_id, request_id, send_body)
                return handler._method_not_allowed({"GET", "HEAD"}, request_id, send_body)
        if path.startswith("/api/admin/pool/sessions/") and path.endswith("/settle"):
            session_id = path.removeprefix("/api/admin/pool/sessions/").removesuffix("/settle").strip("/")
            if session_id and "/" not in session_id:
                if handler.command == "POST":
                    return _pool_settle(handler, session_id, request_id, send_body)
                return handler._method_not_allowed({"POST"}, request_id, send_body)
        if path.startswith("/api/admin/pool/sessions/") and path.endswith("/end"):
            session_id = path.removeprefix("/api/admin/pool/sessions/").removesuffix("/end").strip("/")
            if session_id and "/" not in session_id:
                if handler.command == "POST":
                    return _pool_end(handler, session_id, request_id, send_body)
                return handler._method_not_allowed({"POST"}, request_id, send_body)
        if path == "/api/admin/kitchen/inventory":
            if handler.command in {"GET", "HEAD", "POST"}:
                return _kitchen_inventory(handler, request_id, send_body)
            return handler._method_not_allowed({"GET", "HEAD", "POST"}, request_id, send_body)
        if path.startswith("/api/admin/kitchen/inventory/") and path.endswith("/adjust"):
            item_id = path.removeprefix("/api/admin/kitchen/inventory/").removesuffix("/adjust").strip("/")
            if item_id and "/" not in item_id:
                if handler.command == "POST":
                    return _kitchen_inventory_adjust(handler, item_id, request_id, send_body)
                return handler._method_not_allowed({"POST"}, request_id, send_body)
        if path == "/api/admin/kitchen/menu":
            if handler.command in {"GET", "HEAD", "POST"}:
                return _kitchen_menu(handler, request_id, send_body)
            return handler._method_not_allowed({"GET", "HEAD", "POST"}, request_id, send_body)
        if path.startswith("/api/admin/kitchen/menu/"):
            item_id = path.removeprefix("/api/admin/kitchen/menu/").strip("/")
            if item_id and "/" not in item_id:
                if handler.command == "PATCH":
                    return _kitchen_menu_update(handler, item_id, request_id, send_body)
                return handler._method_not_allowed({"PATCH"}, request_id, send_body)
        if path == "/api/admin/kitchen/orders":
            if handler.command in {"GET", "HEAD", "POST"}:
                return _kitchen_orders(handler, request_id, send_body)
            return handler._method_not_allowed({"GET", "HEAD", "POST"}, request_id, send_body)
        if path.startswith("/api/admin/kitchen/orders/"):
            order_id = path.removeprefix("/api/admin/kitchen/orders/").strip("/")
            if order_id and "/" not in order_id:
                if handler.command == "PATCH":
                    return _kitchen_order_update(handler, order_id, request_id, send_body)
                return handler._method_not_allowed({"PATCH"}, request_id, send_body)
        return _json(handler, HTTPStatus.NOT_FOUND, {"error": "not_found"}, request_id, send_body)
    except (
        AdminSessionInvalid,
        AdminCsrfInvalid,
        AdminForbidden,
        AdminSoftwareNotFound,
        AdminSoftwareConflict,
        AdminSoftwareValidationError,
    ) as error:
        return _error(handler, error, request_id, send_body)
