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
    recipes: [],
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
  await page.route('**/api/admin/operations/report*', (route) => {
    const report = {
      date: '2026-09-24',
      timezone: 'Asia/Kolkata',
      generatedAt: Math.floor(Date.now() / 1000),
      summary: {
        completedPoolSessions: 1,
        poolMinutes: 60,
        poolBilledPaise: 12000,
        poolPaidPaise: 12000,
        kitchenOrders: 2,
        kitchenSalesPaise: 24000,
        kitchenPaidPaise: 16000,
        operationsSalesPaise: 36000,
        settledRevenuePaise: 28000,
        outstandingPaise: 8000,
        activePoolSessions: 1,
        openKitchenOrders: 1,
        lowStockItems: 1,
      },
      poolTables: [
        { id: 'pool-private-1', name: 'Private Table', type: 'private', sessions: 1, minutes: 60, billedPaise: 12000, paidPaise: 12000 },
        { id: 'pool-common-1', name: 'Common Table 1', type: 'common', sessions: 0, minutes: 0, billedPaise: 0, paidPaise: 0 },
        { id: 'pool-common-2', name: 'Common Table 2', type: 'common', sessions: 0, minutes: 0, billedPaise: 0, paidPaise: 0 },
      ],
      reservations: { reserved: 2, checked_in: 1, completed: 1 },
      kitchenStatuses: { new: 1, served: 1 },
      topKitchenItems: [
        { name: 'Cold Coffee', quantity: 3, salesPaise: 24000 },
      ],
      paymentMethods: [
        { method: 'upi', amountPaise: 28000 },
      ],
      lowStock: [
        { id: 'stock-milk', name: 'Milk', unit: 'litre', quantityMilli: 1500, lowStockMilli: 2000 },
      ],
    };
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ report }) });
  });

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
    if (path.startsWith('/api/admin/pool/reservations/') && method === 'PATCH') {
      const reservationId = path.split('/').pop();
      const reservation = state.reservations.find((item) => item.id === reservationId);
      if (!reservation) {
        return route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ error: 'not_found' }) });
      }
      const payload = request.postDataJSON();
      if (payload.status) {
        reservation.status = payload.status;
      } else {
        Object.assign(reservation, payload);
        const table = state.tables.find((item) => item.id === reservation.tableId);
        reservation.tableName = table?.name || reservation.tableId;
        if (reservation.ratePaisePerHour == null) {
          reservation.ratePaisePerHour = table?.defaultRatePaise ?? null;
        }
      }
      reservation.updatedAt = Math.floor(Date.now() / 1000);
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ reservation }) });
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
    if (path === '/api/admin/kitchen/recipes' && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ recipes: state.recipes }) });
    }
    if (path === '/api/admin/kitchen/recipes' && method === 'POST') {
      const payload = request.postDataJSON();
      const menu = state.menu.find((item) => item.id === payload.menuItemId);
      const inventory = state.inventory.find((item) => item.id === payload.inventoryItemId);
      state.recipes = state.recipes.filter((item) => !(
        item.menuItemId === payload.menuItemId && item.inventoryItemId === payload.inventoryItemId
      ));
      const recipe = {
        menuItemId: payload.menuItemId,
        menuName: menu?.name || payload.menuItemId,
        inventoryItemId: payload.inventoryItemId,
        inventoryName: inventory?.name || payload.inventoryItemId,
        unit: inventory?.unit || '',
        quantityMilli: payload.quantityMilli,
        removed: payload.quantityMilli === 0,
      };
      if (payload.quantityMilli > 0) state.recipes.push(recipe);
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ recipe }) });
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
        paymentMethod: null,
        paidAt: null,
        paymentVoidReason: null,
        paymentVoidedAt: null,
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
    if (path.startsWith('/api/admin/kitchen/orders/') && method === 'PATCH') {
      const orderId = path.split('/').pop();
      const order = state.orders.find((item) => item.id === orderId);
      if (!order) {
        return route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ error: 'not_found' }) });
      }
      const patch = request.postDataJSON();
      if (patch.paymentStatus === 'paid') {
        order.paymentStatus = 'paid';
        order.paymentMethod = patch.paymentMethod || order.paymentMethod;
        order.paidAt = Math.floor(Date.now() / 1000);
        order.paymentVoidReason = null;
        order.paymentVoidedAt = null;
      } else if (patch.paymentStatus === 'void') {
        order.paymentStatus = 'void';
        order.paidAt = null;
        order.paymentVoidReason = patch.paymentVoidReason;
        order.paymentVoidedAt = Math.floor(Date.now() / 1000);
      } else if (patch.paymentStatus) {
        order.paymentStatus = patch.paymentStatus;
      }
      if (patch.paymentMethod !== undefined && patch.paymentStatus !== 'void') {
        order.paymentMethod = patch.paymentMethod;
      }
      if (patch.status) {
        order.status = patch.status;
        if (patch.status === 'cancelled') {
          order.cancelReason = patch.cancelReason;
          order.cancelledAt = Math.floor(Date.now() / 1000);
          order.paymentStatus = 'void';
          order.paidAt = null;
        }
      }
      order.updatedAt = Math.floor(Date.now() / 1000);
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ order }) });
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

  await page.locator('#poolReservationsBody').getByRole('button', { name: 'Edit' }).click();
  await expect(page.locator('#poolReservationSubmit')).toHaveText('Update reservation');
  await page.locator('#poolReservationTable').selectOption('pool-common-2');
  await page.locator('#poolReservationGuest').fill('Reserved Guest Updated');
  await page.locator('#poolReservationRate').fill('');
  await page.locator('#poolReservationStart').fill('2026-09-25T19:00');
  await page.locator('#poolReservationEnd').fill('2026-09-25T20:00');
  await page.locator('#poolReservationSubmit').click();
  await expect(page.locator('#poolReservationsBody')).toContainText('Reserved Guest Updated');
  await expect(page.locator('#poolReservationsBody')).toContainText('Common Table 2');
  await expect(page.locator('#poolReservationSubmit')).toHaveText('Create reservation');

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

test('New Gym daily operations report is readable in the browser', async ({ page }) => {
  const state = operationState();
  await mockAdminShell(page);
  await mockOperations(page, state);

  await page.goto('/admin');
  await page.locator('#operationsNav').click();
  await expect(page.locator('#viewTitle')).toHaveText('Operations Report');
  await expect(page.locator('#operationsReportDate')).toHaveValue('2026-09-24');
  await expect(page.locator('#operationsReportSummary')).toContainText('₹360');
  await expect(page.locator('#operationsReportSummary')).toContainText('₹280');
  await expect(page.locator('#operationsReportSummary')).toContainText('₹80');
  await expect(page.locator('#operationsPoolBody')).toContainText('Private Table');
  await expect(page.locator('#operationsKitchenItemsBody')).toContainText('Cold Coffee');
  await expect(page.locator('#operationsPaymentBody')).toContainText('UPI');
  await expect(page.locator('#operationsLowStockBody')).toContainText('1.5 litre');
  await expect(page.locator('#operationsStatusSummary')).toContainText('Reserved');
  await expect(page.locator('#operationsStatusSummary')).toContainText('Served');
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

  const orderCard = page.locator('.kitchen-order-card').filter({ hasText: 'Kitchen Guest' }).first();
  await orderCard.locator('.kitchen-payment-method').selectOption('upi');
  await orderCard.getByRole('button', { name: 'Mark paid' }).click();
  let paidCard = page.locator('.kitchen-order-card').filter({ hasText: 'Kitchen Guest' }).first();
  await expect(paidCard).toContainText('paid · UPI');

  page.once('dialog', async (dialog) => {
    await dialog.accept('Duplicate UPI payment');
  });
  await paidCard.getByRole('button', { name: 'Void payment' }).click();
  let voidedCard = page.locator('.kitchen-order-card').filter({ hasText: 'Kitchen Guest' }).first();
  await expect(voidedCard).toContainText('void · UPI');
  await expect(voidedCard).toContainText('Payment voided: Duplicate UPI payment');
  await expect(voidedCard.getByRole('button', { name: 'Cancel order' })).toBeVisible();

  page.once('dialog', async (dialog) => {
    await dialog.accept('Customer changed order after void');
  });
  await voidedCard.getByRole('button', { name: 'Cancel order' }).click();
  const voidCancelledCard = page.locator('.kitchen-order-card').filter({ hasText: 'Kitchen Guest' }).first();
  await expect(voidCancelledCard).toContainText('cancelled');
  await expect(voidCancelledCard).toContainText('Cancelled: Customer changed order after void');
  await expect(voidCancelledCard).toContainText('Payment voided: Duplicate UPI payment');

  await page.locator('#kitchenCustomerName').fill('Cancel Guest');
  await page.locator('[data-menu-id="menu-coffee"]').fill('1');
  await page.locator('#kitchenOrderForm button[type="submit"]').click();
  const cancelCard = page.locator('.kitchen-order-card').filter({ hasText: 'Cancel Guest' }).first();
  page.once('dialog', async (dialog) => {
    await dialog.accept('Customer changed order');
  });
  await cancelCard.getByRole('button', { name: 'Cancel order' }).click();
  const cancelledCard = page.locator('.kitchen-order-card').filter({ hasText: 'Cancel Guest' }).first();
  await expect(cancelledCard).toContainText('cancelled');
  await expect(cancelledCard).toContainText('Cancelled: Customer changed order');
  await expect(cancelledCard).toContainText('void');

  await page.locator('#kitchenInventoryName').fill('Bread');
  await page.locator('#kitchenInventoryUnit').fill('piece');
  await page.locator('#kitchenInventoryQuantity').fill('10');
  await page.locator('#kitchenInventoryLowStock').fill('3');
  await page.locator('#kitchenInventoryCreateForm button[type="submit"]').click();
  await expect(page.locator('#kitchenInventoryBody')).toContainText('Bread');

  await page.locator('#kitchenRecipeMenuItem').selectOption('menu-coffee');
  await page.locator('#kitchenRecipeInventoryItem').selectOption('stock-milk');
  await page.locator('#kitchenRecipeQuantity').fill('0.25');
  await page.locator('#kitchenRecipeForm button[type="submit"]').click();
  await expect(page.locator('#kitchenRecipesBody')).toContainText('Cold Coffee');
  await expect(page.locator('#kitchenRecipesBody')).toContainText('Milk');
  await expect(page.locator('#kitchenRecipesBody')).toContainText('0.25 litre');

  await page.locator('#kitchenInventoryAdjustItem').selectOption('stock-milk');
  await page.locator('#kitchenInventoryDelta').fill('-3.5');
  await page.locator('#kitchenInventoryReason').selectOption('usage');
  await page.locator('#kitchenInventoryAdjustForm button[type="submit"]').click();
  await expect(page.locator('#kitchenInventoryBody')).toContainText('1.5 litre');
  await expect(page.locator('#kitchenInventoryBody')).toContainText('low stock');
});
