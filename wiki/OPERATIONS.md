# New Gym Operations

## Pool workflow

1. Set hourly rates for Private Table / Common Table 1 / Common Table 2.
2. For walk-ins, start a table session directly.
3. For bookings, create a reservation with start/end time.
4. Overlapping reservations on the same table are rejected.
5. At arrival, use Check in. The server starts the timed pool session.
6. Kitchen orders can be attached to the active pool session.
7. End the pool session when play finishes.
8. Open Final Bill.
9. The bill combines the fixed pool charge and all non-cancelled/non-void kitchen orders.
10. Settlement is blocked until payable kitchen orders are served.
11. Choose Cash / UPI / Card / Bank transfer / Other and settle once.

## Kitchen workflow

1. Create menu items with category and selling price.
2. Toggle availability when required.
3. Create a walk-in order or attach it to an active pool session.
4. Move order: New -> Preparing -> Ready -> Served.
5. Individual kitchen orders may be marked paid, or pool-linked orders may be settled through the final Pool + Kitchen bill.

## Inventory workflow

1. Add stock item and unit, such as Milk / litre.
2. Enter initial stock and low-stock level.
3. Adjust stock using:
   - purchase
   - usage
   - waste
   - adjustment
4. Stock cannot fall below zero.
5. Every movement is stored with the acting admin and reason.

Automatic recipe deduction is intentionally not active yet.

## Backup rule

Production deployment must configure a dedicated New Gym off-device backup target.
Do not share Gravity's backup path/marker as the New Gym completion marker.

## Safety

- Keep app ports bound to 127.0.0.1.
- Use Cloudflare Access on the admin hostname.
- Never place secrets in Git.
- Do not reuse Gravity Firebase, tunnel token, production database, or admin service names.
