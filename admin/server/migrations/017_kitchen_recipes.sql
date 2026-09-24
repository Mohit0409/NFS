-- New Gym operations v4: kitchen recipes and idempotent inventory consumption.

CREATE TABLE kitchen_recipes (
    menu_item_id TEXT NOT NULL REFERENCES kitchen_menu_items(id) ON DELETE CASCADE,
    inventory_item_id TEXT NOT NULL REFERENCES kitchen_inventory_items(id) ON DELETE RESTRICT,
    quantity_milli INTEGER NOT NULL CHECK(quantity_milli > 0),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY(menu_item_id, inventory_item_id)
);

CREATE TABLE kitchen_order_inventory_usage (
    order_item_id TEXT NOT NULL REFERENCES kitchen_order_items(id) ON DELETE RESTRICT,
    inventory_item_id TEXT NOT NULL REFERENCES kitchen_inventory_items(id) ON DELETE RESTRICT,
    quantity_milli INTEGER NOT NULL CHECK(quantity_milli > 0),
    created_at INTEGER NOT NULL,
    PRIMARY KEY(order_item_id, inventory_item_id)
);

CREATE INDEX kitchen_recipes_inventory_idx
ON kitchen_recipes(inventory_item_id);

CREATE INDEX kitchen_order_inventory_usage_inventory_idx
ON kitchen_order_inventory_usage(inventory_item_id, created_at DESC);
