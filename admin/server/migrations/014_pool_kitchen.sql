-- New gym operations: pool tables and kitchen management.
CREATE TABLE pool_tables (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    table_type TEXT NOT NULL CHECK(table_type IN ('private','common')),
    status TEXT NOT NULL DEFAULT 'available'
      CHECK(status IN ('available','occupied','reserved','cleaning','disabled')),
    default_rate_paise INTEGER CHECK(default_rate_paise IS NULL OR default_rate_paise >= 0),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE pool_sessions (
    id TEXT PRIMARY KEY,
    table_id TEXT NOT NULL REFERENCES pool_tables(id) ON DELETE RESTRICT,
    customer_id TEXT REFERENCES customers(id) ON DELETE SET NULL,
    guest_name TEXT,
    rate_paise_per_hour INTEGER NOT NULL CHECK(rate_paise_per_hour >= 0),
    started_at INTEGER NOT NULL,
    ended_at INTEGER,
    status TEXT NOT NULL DEFAULT 'active'
      CHECK(status IN ('active','completed','cancelled')),
    amount_paise INTEGER CHECK(amount_paise IS NULL OR amount_paise >= 0),
    note TEXT,
    created_by_admin_user_id TEXT REFERENCES admin_users(id) ON DELETE SET NULL,
    ended_by_admin_user_id TEXT REFERENCES admin_users(id) ON DELETE SET NULL,
    created_at INTEGER NOT NULL
);
CREATE UNIQUE INDEX pool_one_active_session_per_table
ON pool_sessions(table_id) WHERE status='active';
CREATE INDEX pool_sessions_started_idx ON pool_sessions(started_at DESC);

CREATE TABLE kitchen_menu_items (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price_paise INTEGER NOT NULL CHECK(price_paise >= 0),
    status TEXT NOT NULL DEFAULT 'available'
      CHECK(status IN ('available','unavailable')),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE INDEX kitchen_menu_category_idx ON kitchen_menu_items(category, sort_order, name);

CREATE TABLE kitchen_orders (
    id TEXT PRIMARY KEY,
    pool_session_id TEXT REFERENCES pool_sessions(id) ON DELETE SET NULL,
    customer_id TEXT REFERENCES customers(id) ON DELETE SET NULL,
    customer_name TEXT,
    status TEXT NOT NULL DEFAULT 'new'
      CHECK(status IN ('new','preparing','ready','served','cancelled')),
    payment_status TEXT NOT NULL DEFAULT 'unpaid'
      CHECK(payment_status IN ('unpaid','paid','void')),
    total_paise INTEGER NOT NULL DEFAULT 0 CHECK(total_paise >= 0),
    note TEXT,
    created_by_admin_user_id TEXT REFERENCES admin_users(id) ON DELETE SET NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE INDEX kitchen_orders_status_idx ON kitchen_orders(status, created_at DESC);
CREATE INDEX kitchen_orders_pool_idx ON kitchen_orders(pool_session_id, created_at DESC);

CREATE TABLE kitchen_order_items (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES kitchen_orders(id) ON DELETE CASCADE,
    menu_item_id TEXT REFERENCES kitchen_menu_items(id) ON DELETE SET NULL,
    item_name_snapshot TEXT NOT NULL,
    unit_price_paise INTEGER NOT NULL CHECK(unit_price_paise >= 0),
    quantity INTEGER NOT NULL CHECK(quantity > 0 AND quantity <= 100),
    line_total_paise INTEGER NOT NULL CHECK(line_total_paise >= 0)
);
CREATE INDEX kitchen_order_items_order_idx ON kitchen_order_items(order_id);

INSERT INTO pool_tables(id,name,table_type,status,default_rate_paise,created_at,updated_at)
VALUES
('pool-private-1','Private Table','private','available',NULL,strftime('%s','now'),strftime('%s','now')),
('pool-common-1','Common Table 1','common','available',NULL,strftime('%s','now'),strftime('%s','now')),
('pool-common-2','Common Table 2','common','available',NULL,strftime('%s','now'),strftime('%s','now'));
