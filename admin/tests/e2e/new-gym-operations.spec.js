const { test, expect } = require('@playwright/test');

function adminIdentity() {
  return {
    id: 'new-gym-owner',
    username: 'owner',
    role: 'owner',
    permissions: ['*'],
  };
}

async function mockAdminShell(page) {
  await page.route('**/api/admin/session', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      configured: true,
      bootstrapRequired: false,
      authenticated: true,
      admin: adminIdentity(),
    }),
  }));
  await page.route('**/api/admin/dashboard', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      customers: { total: 0, active: 0, disabled: 0 },
      admins: { owner: 1 },
      recentAudit: [],
    }),
  }));
}

function operationState() {
  const now = Math.floor(Date.now() / 1000);
  return {
    tables: [
      {
        id: 'pool-private-1',
        name: 'Private Table',
        type: 'private',
        status: 'available',
        defaultRatePaise: 12000,
        activeSession: null,
        nextReservation: null,
      },
      {
        id: 'pool-common-1',
        name: 'Common Table 1',
        type: 'common',
        status: 'occupied',
        defaultRatePaise: 10000,
        activeSession: {
          id: 'session-active',
          tableId: 'pool-common-1',
          guestName: 'Active Guest',
          ratePaisePerHour: 10000,
          startedAt: now - 1200,
          endedAt: null,
          elapsedSeconds: 1200,
          status: 'active',
          amountPaise: null,
          paymentStatus: 'unpaid',
        },
        nextReservation: null,
      },
      {
        id: 'pool-common-2',
        name: 'Common Table 2',
        type: 'common',
        status: 'available',
        defaultRatePaise: 10000,
        activeSession: null,
        nextReservation: null,
      },
    ],
    reservations: [],
    sessions: [
      {
        id: 'session-completed',
        tableId: 'pool-private-1',
        tableName: 'Private Table',
        tableType: 'private',
        guestName: 'Billing Guest',
        ratePaisePerHour: 12000,
        startedAt: now - 3600,
        endedAt: now,
        elapsedSeconds: 3600,
        status: 'completed',
        amountPaise: 12000,
        paymentStatus: 'unpaid',
        paymentMethod: null,
      },
    ],
    menu: [
      {
        id: 'menu-coffee',
        name: 'Cold Coffee',
        category: 'Drinks',
        pricePaise: 8000,
        status: 'available',
        sortOrder: 0,
      },
    ],
    orders: [],
    inventory: [
      {
        id: 'stock-milk',
        name: 'Milk',
        unit: 'litre',
        quantityMilli: 5000,
        lowStockMilli: 2000,
        lowStock: false,
        status: 'active',
        createdAt: now,
        updatedAt: now,
      },
    ],
    billPaid: false,
  };
}

async function mockOperations(page, state) {
  await page.route('**/api/admin/pool/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (path === '/api/admin/pool/tables' && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ tables: state.tables }) });
    }
    if (path.startsWith('/api/admin/pool/tables/') && method === 'PATCH') {
      const table = state.tables.find((item) => path.endsWith(item.id));
      const patch = request.postDataJSON();
      table.defaultRatePaise = patch.defaultRatePaise;
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ table }) });
    }
    if (path === '/api/admin/pool/reservations' && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ reservations: state.reservations }) });
    }
    if (path === '/api/admin/pool/reservations' && method === 'POST') {
      const payload = request.postDataJSON();
      const table = state.tables.find((item) => item.id === payload.tableId);
      const reservation = {
        id: 'reservation-browser',
        tableId: payload.tableId,
        tableName: table?.name || payload.tableId,
        guestName: payload.guestName,
        phone: payload.phone,
        startsAt: payload.startsAt,
        endsAt: payload.endsAt,
        status: 'reserved',
        ratePaisePerHour: payload.ratePaisePerHour ?? table?.defaultRatePaise ?? null,
        note: payload.note,
        createdAt: Math.floor(Date.now() / 1000),
        updatedAt: Math.floor(Date.now() / 1000),
      };
      state.reservations.push(reservation);
      return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ reservation }) });
    }
    if (path === '/api/admin/pool/sessions' && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ sessions: state.sessions }) });
    }
    if (path === '/api/admin/pool/sessions/session-completed/bill' && method === 'GET') {
      const bill = {
        session: {
          ...state.sessions[0],
          paymentStatus: state.billPaid ? 'paid' : 'unpaid',
          paymentMethod: state.billPaid ? 'upi' : null,
        },
        tableName: 'Private Table',
        poolChargePaise: 12000,
        kitchenTotalPaise: 16000,
        grandTotalPaise: 28000,
        paidPaise: state.billPaid ? 28000 : 0,
        duePaise: state.billPaid ? 0 : 28000,
        settlementReady: true,
        unservedKitchenOrderIds: [],
        kitchenOrders: [{
          id: 'order-bill',
          status: 'served',
          paymentStatus: state.billPaid ? 'paid' : 'unpaid',
          totalPaise: 16000,
          paymentMethod: state.billPaid ? 'upi' : null,
          paidAt: state.billPaid ? Math.floor(Date.now() / 1000) : null,
          customerName: 'Billing Guest',
        }],
      };
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ bill }) });
    }
    if (path === '/api/admin/pool/sessions/session-completed/settle' && method === 'POST') {
      state.billPaid = true;
      state.sessions[0].paymentStatus = 'paid';
      state.sessions[0].paymentMethod = request.postDataJSON().paymentMethod;
      const bill = {
        session: state.sessions[0],
        tableName: 'Private Table',
        poolChargePaise: 12000,
        kitchenTotalPaise: 16000,
        grandTotalPaise: 28000,
        paidPaise: 28000,
        duePaise: 0,
        settlementReady: true,
        unservedKitchenOrderIds: [],
        kitchenOrders: [{
          id: 'order-bill',
          status: 'served',
          paymentStatus: 'paid',
          totalPaise: 16000,
          paymentMethod: state.sessions[0].paymentMethod,
          paidAt: Math.floor(Date.now() / 1000),
          customerName: 'Billing Guest',
        }],
      };
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ bill }) });
    }
    return route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ error: 'not_found' }) });
  });

  await page.route('**/api/admin/kitchen/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (path === '/api/admin/kitchen/menu' && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: state.menu }) });
    }
    if (path === '/api/admin/kitchen/orders' && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ orders: state.orders }) });
    }
    if (path === '/api/admin/kitchen/orders' && method === 'POST') {
      const payload = request.postDataJSON();
      const order = {
        id: 'order-browser',
        poolSessionId: payload.poolSessionId,
        customerId: null,
        customerName: payload.customerName,
        status: 'new',
        paymentStatus: 'unpaid',
        totalPaise: 8000,
        note: payload.note,
        createdAt: Math.floor(Date.now() / 1000),
        updatedAt: Math.floor(Date.now() / 1000),
        items: [{
          id: 'line-browser',
          menuItemId: 'menu-coffee',
          name: 'Cold Coffee',
          unitPricePaise: 8000,
          quantity: 1,
          lineTotalPaise: 8000,
        }],
      };
      state.orders.unshift(order);
      return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ order }) });
    }
    if (path === '/api/admin/kitchen/inventory' && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: state.inventory }) });
    }
    if (path === '/api/admin/kitchen/inventory' && method === 'POST') {
      const payload = request.postDataJSON();
      const item = {
        id: 'stock-bread',
        name: payload.name,
        unit: payload.unit,
        quantityMilli: payload.quantityMilli,
        lowStockMilli: payload.lowStockMilli,
        lowStock: payload.quantityMilli <= payload.lowStockMilli,
        status: 'active',
        createdAt: Math.floor(Date.now() / 1000),
        updatedAt: Math.floor(Date.now() / 1000),
      };
      state.inventory.push(item);
      return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ item }) });
    }
    if (path === '/api/admin/kitchen/inventory/stock-milk/adjust' && method === 'POST') {
      const payload = request.postDataJSON();
      const item = state.inventory.find((entry) => entry.id === 'stock-milk');
      item.quantityMilli += payload.deltaMilli;
      item.lowStock = item.quantityMilli <= item.lowStockMilli;
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ item }) });
    }
    return route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ error: 'not_found' }) });
  });
}

test('New Gym pool reservation and combined bill work in the browser', async ({ page }) => {
  const state = operationState();
  await mockAdminShell(page);
  await mockOperations(page, state);

  await page.goto('/admin');
  await expect(page.locator('#app')).toBeVisible();
  await expect(page.locator('[data-gym-name]').first()).toHaveText('New Gym');

  await page.locator('#poolNav').click();
  await expect(page.locator('#viewTitle')).toHaveText('Pool');
  await expect(page.locator('.pool-table-card')).toHaveCount(3);
  await expect(page.locator('#poolReservationForm')).toBeVisible();

  await page.locator('#poolReservationTable').selectOption('pool-private-1');
  await page.locator('#poolReservationGuest').fill('Reserved Guest');
  await page.locator('#poolReservationPhone').fill('9876543210');
  await page.locator('#poolReservationStart').fill('2026-09-25T20:00');
  await page.locator('#poolReservationEnd').fill('2026-09-25T21:00');
  await page.locator('#poolReservationForm button[type="submit"]').click();

  await expect(page.locator('#poolReservationsBody')).toContainText('Reserved Guest');
  await expect(page.locator('#poolReservationsBody')).toContainText('Private Table');

  await page.getByRole('button', { name: 'View bill' }).click();
  await expect(page.locator('#poolBillDialog')).toBeVisible();
  await expect(page.locator('#poolBillSummary')).toContainText('₹120.00');
  await expect(page.locator('#poolBillSummary')).toContainText('₹160.00');
  await expect(page.locator('#poolBillSummary')).toContainText('₹280.00');

  await page.locator('#poolBillPaymentMethod').selectOption('upi');
  await page.locator('#settlePoolBill').click();
  await expect(page.locator('#poolBillSummary')).toContainText('₹0.00');
  await expect(page.locator('#settlePoolBill')).toBeHidden();
});

test('New Gym kitchen order and inventory flows work in the browser', async ({ page }) => {
  const state = operationState();
  await mockAdminShell(page);
  await mockOperations(page, state);

  await page.goto('/admin');
  await page.locator('#kitchenNav').click();
  await expect(page.locator('#viewTitle')).toHaveText('Kitchen');
  await expect(page.locator('#kitchenMenuBody')).toContainText('Cold Coffee');
  await expect(page.locator('#kitchenInventoryBody')).toContainText('Milk');

  await page.locator('#kitchenPoolSession').selectOption('session-active');
  await page.locator('#kitchenCustomerName').fill('Kitchen Guest');
  await page.locator('[data-menu-id="menu-coffee"]').fill('1');
  await page.locator('#kitchenOrderForm button[type="submit"]').click();
  await expect(page.locator('#kitchenOrdersGrid')).toContainText('Kitchen Guest');
  await expect(page.locator('#kitchenOrdersGrid')).toContainText('Cold Coffee');

  await page.locator('#kitchenInventoryName').fill('Bread');
  await page.locator('#kitchenInventoryUnit').fill('piece');
  await page.locator('#kitchenInventoryQuantity').fill('10');
  await page.locator('#kitchenInventoryLowStock').fill('3');
  await page.locator('#kitchenInventoryCreateForm button[type="submit"]').click();
  await expect(page.locator('#kitchenInventoryBody')).toContainText('Bread');

  await page.locator('#kitchenInventoryAdjustItem').selectOption('stock-milk');
  await page.locator('#kitchenInventoryDelta').fill('-3.5');
  await page.locator('#kitchenInventoryReason').selectOption('usage');
  await page.locator('#kitchenInventoryAdjustForm button[type="submit"]').click();
  await expect(page.locator('#kitchenInventoryBody')).toContainText('1.5 litre');
  await expect(page.locator('#kitchenInventoryBody')).toContainText('low stock');
});
