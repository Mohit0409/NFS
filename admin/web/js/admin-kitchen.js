(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const rupees = (paise) => `₹${(Number(paise || 0) / 100).toFixed(2)}`;
  const quantity = (milli, unit) => `${(Number(milli || 0) / 1000).toLocaleString('en-IN', { maximumFractionDigits: 3 })} ${unit}`;
  const nextStatus = { new: 'preparing', preparing: 'ready', ready: 'served' };

  function core() { return window.GravityAdminCore; }

  async function loadPoolChoices() {
    const select = $('kitchenPoolSession');
    const data = await core().api('/api/admin/pool/tables');
    select.replaceChildren(new Option('No pool table / takeaway', ''));
    for (const table of data.tables || []) {
      if (!table.activeSession) continue;
      select.append(new Option(
        `${table.name} · ${table.activeSession.guestName || 'active session'}`,
        table.activeSession.id,
      ));
    }
  }

  async function addMenuItem(event) {
    event.preventDefault();
    const price = Number($('kitchenMenuPrice').value);
    if (!Number.isFinite(price) || price < 0) {
      core().flash('Enter a valid menu price.', 'error');
      return;
    }
    await core().api('/api/admin/kitchen/menu', {
      method: 'POST',
      body: {
        name: $('kitchenMenuName').value.trim(),
        category: $('kitchenMenuCategory').value.trim(),
        pricePaise: Math.round(price * 100),
      },
    });
    $('kitchenMenuForm').reset();
    core().flash('Menu item added.');
    await render();
  }

  async function toggleItem(item) {
    await core().api(`/api/admin/kitchen/menu/${encodeURIComponent(item.id)}`, {
      method: 'PATCH',
      body: { status: item.status === 'available' ? 'unavailable' : 'available' },
    });
    await render();
  }

  function renderMenu(items) {
    const body = $('kitchenMenuBody');
    body.replaceChildren();
    for (const item of items) {
      const row = document.createElement('tr');
      row.innerHTML = '<td></td><td></td><td></td><td></td><td></td>';
      row.children[0].textContent = item.name;
      row.children[1].textContent = item.category;
      row.children[2].textContent = rupees(item.pricePaise);
      row.children[3].textContent = item.status;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'ghost compact-button';
      button.textContent = item.status === 'available' ? 'Mark unavailable' : 'Make available';
      button.addEventListener('click', () => toggleItem(item).catch((error) => core().flash(error.message, 'error')));
      row.children[4].append(button);
      body.append(row);
    }
    if (!body.children.length) {
      const row = document.createElement('tr');
      row.innerHTML = '<td colspan="5" class="empty">No kitchen menu items yet.</td>';
      body.append(row);
    }

    const builder = $('kitchenOrderItems');
    builder.replaceChildren();
    for (const item of items.filter((entry) => entry.status === 'available')) {
      const label = document.createElement('label');
      label.className = 'kitchen-order-line';
      label.innerHTML = `<span></span><small></small><input type="number" min="0" max="100" value="0" data-menu-id="${item.id}" aria-label="Quantity">`;
      label.querySelector('span').textContent = item.name;
      label.querySelector('small').textContent = rupees(item.pricePaise);
      builder.append(label);
    }
    if (!builder.children.length) builder.textContent = 'Add available menu items before creating an order.';
  }

  async function createOrder(event) {
    event.preventDefault();
    const items = Array.from($('kitchenOrderItems').querySelectorAll('[data-menu-id]'))
      .map((input) => ({ menuItemId: input.dataset.menuId, quantity: Number(input.value || 0) }))
      .filter((item) => item.quantity > 0);
    if (!items.length) {
      core().flash('Select at least one kitchen item.', 'error');
      return;
    }
    await core().api('/api/admin/kitchen/orders', {
      method: 'POST',
      body: {
        poolSessionId: $('kitchenPoolSession').value || null,
        customerName: $('kitchenCustomerName').value.trim() || null,
        note: $('kitchenOrderNote').value.trim() || null,
        items,
      },
    });
    $('kitchenOrderForm').reset();
    core().flash('Kitchen order created.');
    await render();
  }

  async function updateOrder(order, patch) {
    await core().api(`/api/admin/kitchen/orders/${encodeURIComponent(order.id)}`, {
      method: 'PATCH', body: patch,
    });
    await render();
  }

  function orderCard(order) {
    const card = document.createElement('article');
    card.className = 'ops-card kitchen-order-card';
    const lines = (order.items || []).map((item) =>
      `<li><span>${item.quantity} × </span><strong></strong><em>${rupees(item.lineTotalPaise)}</em></li>`
    ).join('');
    card.innerHTML = `
      <div class="ops-card-head">
        <div><span class="ops-kicker">ORDER</span><h3>#${String(order.id).slice(0, 8)}</h3></div>
        <span class="ops-status" data-status="${order.status}">${order.status}</span>
      </div>
      <p class="micro">${order.customerName || (order.poolSessionId ? 'Pool session order' : 'Walk-in order')}</p>
      <ul class="kitchen-lines">${lines}</ul>
      <div class="kitchen-total"><span>Total</span><strong>${rupees(order.totalPaise)}</strong></div>
      <div class="row-actions kitchen-order-actions"></div>
    `;
    const names = card.querySelectorAll('.kitchen-lines strong');
    (order.items || []).forEach((item, index) => { if (names[index]) names[index].textContent = item.name; });
    const actions = card.querySelector('.kitchen-order-actions');
    if (nextStatus[order.status]) {
      const advance = document.createElement('button');
      advance.type = 'button';
      advance.textContent = `Mark ${nextStatus[order.status]}`;
      advance.addEventListener('click', () => updateOrder(order, { status: nextStatus[order.status] }).catch((error) => core().flash(error.data?.message || error.message, 'error')));
      actions.append(advance);
    }
    if (order.paymentStatus === 'unpaid' && order.status !== 'cancelled') {
      const paid = document.createElement('button');
      paid.type = 'button';
      paid.className = 'ghost';
      paid.textContent = 'Mark paid';
      paid.addEventListener('click', () => updateOrder(order, { paymentStatus: 'paid' }).catch((error) => core().flash(error.message, 'error')));
      actions.append(paid);
    } else {
      const badge = document.createElement('span');
      badge.className = 'ops-payment';
      badge.textContent = order.paymentStatus;
      actions.append(badge);
    }
    return card;
  }

  function renderInventory(items) {
    const body = $('kitchenInventoryBody');
    const select = $('kitchenInventoryAdjustItem');
    if (!body || !select) return;
    body.replaceChildren();
    const selected = select.value;
    select.replaceChildren();

    for (const item of items || []) {
      const option = new Option(`${item.name} · ${quantity(item.quantityMilli, item.unit)}`, item.id);
      option.disabled = item.status !== 'active';
      select.append(option);

      const row = document.createElement('tr');
      row.innerHTML = '<td></td><td></td><td></td><td></td>';
      row.children[0].textContent = item.name;
      row.children[1].textContent = quantity(item.quantityMilli, item.unit);
      row.children[2].textContent = quantity(item.lowStockMilli, item.unit);
      const status = document.createElement('span');
      status.className = 'ops-status';
      status.dataset.status = item.lowStock ? 'low-stock' : item.status;
      status.textContent = item.lowStock ? 'low stock' : item.status;
      row.children[3].append(status);
      body.append(row);
    }

    if ([...select.options].some((option) => option.value === selected)) select.value = selected;
    if (!body.children.length) {
      const row = document.createElement('tr');
      row.innerHTML = '<td colspan="4" class="empty">No kitchen stock items yet.</td>';
      body.append(row);
    }
  }

  function decimalToMilli(value, field) {
    const amount = Number(value);
    if (!Number.isFinite(amount) || amount < 0) {
      throw new Error(`Enter a valid ${field}.`);
    }
    return Math.round(amount * 1000);
  }

  async function createInventoryItem(event) {
    event.preventDefault();
    const quantityMilli = decimalToMilli($('kitchenInventoryQuantity').value || '0', 'initial quantity');
    const lowStockMilli = decimalToMilli($('kitchenInventoryLowStock').value || '0', 'low-stock level');
    await core().api('/api/admin/kitchen/inventory', {
      method: 'POST',
      body: {
        name: $('kitchenInventoryName').value.trim(),
        unit: $('kitchenInventoryUnit').value.trim(),
        quantityMilli,
        lowStockMilli,
      },
    });
    $('kitchenInventoryCreateForm').reset();
    $('kitchenInventoryQuantity').value = '0';
    $('kitchenInventoryLowStock').value = '0';
    core().flash('Kitchen stock item added.');
    await render();
  }

  async function adjustInventory(event) {
    event.preventDefault();
    const raw = Number($('kitchenInventoryDelta').value);
    if (!Number.isFinite(raw) || raw === 0) {
      core().flash('Enter a non-zero stock change.', 'error');
      return;
    }
    const deltaMilli = Math.round(raw * 1000);
    if (deltaMilli === 0) {
      core().flash('Stock change is too small.', 'error');
      return;
    }
    await core().api(`/api/admin/kitchen/inventory/${encodeURIComponent($('kitchenInventoryAdjustItem').value)}/adjust`, {
      method: 'POST',
      body: {
        deltaMilli,
        reason: $('kitchenInventoryReason').value,
        note: $('kitchenInventoryNote').value.trim() || null,
      },
    });
    $('kitchenInventoryAdjustForm').reset();
    core().flash('Kitchen stock updated.');
    await render();
  }

  async function render() {
    const root = $('kitchenOrdersGrid');
    if (!root) return;
    const [menuData, orderData, inventoryData] = await Promise.all([
      core().api('/api/admin/kitchen/menu'),
      core().api('/api/admin/kitchen/orders?limit=50'),
      core().api('/api/admin/kitchen/inventory'),
    ]);
    renderMenu(menuData.items || []);
    renderInventory(inventoryData.items || []);
    root.replaceChildren(...(orderData.orders || []).map(orderCard));
    if (!root.children.length) {
      const empty = document.createElement('p');
      empty.className = 'empty';
      empty.textContent = 'No kitchen orders yet.';
      root.append(empty);
    }
    await loadPoolChoices();
  }

  $('kitchenMenuForm')?.addEventListener('submit', (event) => addMenuItem(event).catch((error) => core().flash(error.data?.message || error.message, 'error')));
  $('kitchenOrderForm')?.addEventListener('submit', (event) => createOrder(event).catch((error) => core().flash(error.data?.message || error.message, 'error')));
  $('kitchenInventoryCreateForm')?.addEventListener('submit', (event) => createInventoryItem(event).catch((error) => core().flash(error.data?.message || error.message, 'error')));
  $('kitchenInventoryAdjustForm')?.addEventListener('submit', (event) => adjustInventory(event).catch((error) => core().flash(error.data?.message || error.message, 'error')));

  window.NewGymKitchenAdmin = { renderWorkspace: render };
})();