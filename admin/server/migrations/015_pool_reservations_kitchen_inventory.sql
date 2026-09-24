-- New Gym operations v2: pool reservations and kitchen inventory.

CREATE TABLE pool_reservations (
    id TEXT PRIMARY KEY,
    table_id TEXT NOT NULL REFERENCES pool_tables(id) ON DELETE RESTRICT,
    customer_id TEXT REFERENCES customers(id) ON DELETE SET NULL,
    guest_name TEXT,
    phone_e164 TEXT,
    starts_at INTEGER NOT NULL,
    ends_at INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'reserved'
      CHECK(status IN ('reserved','checked_in','completed','cancelled','no_show')),
    rate_paise_per_hour INTEGER CHECK(rate_paise_per_hour IS NULL OR rate_paise_per_hour >= 0),
    note TEXT,
    created_by_admin_user_id TEXT REFERENCES admin_users(id) ON DELETE SET NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    CHECK(ends_at > starts_at)
);
CREATE INDEX pool_reservations_table_time_idx
ON pool_reservations(table_id, starts_at, ends_at);
CREATE INDEX pool_reservations_status_time_idx
ON pool_reservations(status, starts_at);

ALTER TABLE pool_sessions
ADD COLUMN reservation_id TEXT REFERENCES pool_reservations(id) ON DELETE SET NULL;

CREATE INDEX pool_sessions_reservation_idx
ON pool_sessions(reservation_id);

CREATE TABLE kitchen_inventory_items (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    unit TEXT NOT NULL,
    quantity_milli INTEGER NOT NULL DEFAULT 0 CHECK(quantity_milli >= 0),
    low_stock_milli INTEGER NOT NULL DEFAULT 0 CHECK(low_stock_milli >= 0),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','inactive')),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE kitchen_inventory_movements (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL REFERENCES kitchen_inventory_items(id) ON DELETE RESTRICT,
    delta_milli INTEGER NOT NULL CHECK(delta_milli != 0),
    quantity_after_milli INTEGER NOT NULL CHECK(quantity_after_milli >= 0),
    reason TEXT NOT NULL CHECK(reason IN ('purchase','usage','waste','adjustment')),
    note TEXT,
    created_by_admin_user_id TEXT REFERENCES admin_users(id) ON DELETE SET NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX kitchen_inventory_movements_item_idx
ON kitchen_inventory_movements(item_id, created_at DESC);
