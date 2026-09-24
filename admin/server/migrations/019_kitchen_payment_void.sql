-- New Gym operations v6: audited standalone kitchen payment void metadata.

ALTER TABLE kitchen_orders
ADD COLUMN payment_void_reason TEXT;

ALTER TABLE kitchen_orders
ADD COLUMN payment_voided_at INTEGER;

CREATE INDEX kitchen_orders_payment_voided_idx
ON kitchen_orders(payment_status, payment_voided_at DESC);
