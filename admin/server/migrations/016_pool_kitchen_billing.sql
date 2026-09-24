-- New Gym operations v3: combined pool + kitchen settlement.

ALTER TABLE pool_sessions
ADD COLUMN payment_status TEXT NOT NULL DEFAULT 'unpaid'
  CHECK(payment_status IN ('unpaid','paid','void'));

ALTER TABLE pool_sessions
ADD COLUMN payment_method TEXT
  CHECK(payment_method IS NULL OR payment_method IN ('cash','upi','card','bank_transfer','other'));

ALTER TABLE pool_sessions
ADD COLUMN paid_at INTEGER;

ALTER TABLE kitchen_orders
ADD COLUMN payment_method TEXT
  CHECK(payment_method IS NULL OR payment_method IN ('cash','upi','card','bank_transfer','other'));

ALTER TABLE kitchen_orders
ADD COLUMN paid_at INTEGER;

CREATE INDEX pool_sessions_payment_idx
ON pool_sessions(payment_status, ended_at DESC);
