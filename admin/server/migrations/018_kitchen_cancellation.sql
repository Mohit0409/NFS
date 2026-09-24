-- New Gym operations v5: audited kitchen order cancellation metadata.

ALTER TABLE kitchen_orders
ADD COLUMN cancel_reason TEXT;

ALTER TABLE kitchen_orders
ADD COLUMN cancelled_at INTEGER;

CREATE INDEX kitchen_orders_cancelled_idx
ON kitchen_orders(status, cancelled_at DESC);
