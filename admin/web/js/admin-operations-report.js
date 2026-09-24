(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const core = () => window.GravityAdminCore;

  function money(paise) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(Number(paise || 0) / 100);
  }

  function stock(milli, unit) {
    const value = Number(milli || 0) / 1000;
    return `${value.toLocaleString('en-IN', { maximumFractionDigits: 3 })} ${unit || ''}`.trim();
  }

  function stat(label, value, hint = '') {
    const item = document.createElement('article');
    item.className = 'software-stat';
    const name = document.createElement('span');
    name.textContent = label;
    const amount = document.createElement('strong');
    amount.textContent = value;
    item.append(name, amount);
    if (hint) {
      const note = document.createElement('small');
      note.textContent = hint;
      item.append(note);
    }
    return item;
  }

  function emptyRow(message, colspan) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = colspan;
    cell.className = 'empty';
    cell.textContent = message;
    row.append(cell);
    return row;
  }

  function renderSummary(report) {
    const summary = report.summary || {};
    const root = $('operationsReportSummary');
    root.replaceChildren(
      stat('Operations Sales', money(summary.operationsSalesPaise), 'Pool billed + kitchen sales'),
      stat('Settled Revenue', money(summary.settledRevenuePaise), 'Payments settled this day'),
      stat('Outstanding', money(summary.outstandingPaise), 'Selected-day unpaid components'),
      stat('Pool Sessions', String(summary.completedPoolSessions ?? 0), `${summary.poolMinutes ?? 0} minutes completed`),
      stat('Kitchen Orders', String(summary.kitchenOrders ?? 0), money(summary.kitchenSalesPaise)),
      stat('Active Pool Now', String(summary.activePoolSessions ?? 0)),
      stat('Open Kitchen Now', String(summary.openKitchenOrders ?? 0)),
      stat('Low Stock Now', String(summary.lowStockItems ?? 0)),
    );
  }

  function renderPool(rows) {
    const body = $('operationsPoolBody');
    body.replaceChildren();
    for (const item of rows || []) {
      const row = document.createElement('tr');
      row.innerHTML = '<td></td><td></td><td></td><td></td><td></td>';
      row.children[0].textContent = item.name;
      row.children[1].textContent = String(item.sessions || 0);
      row.children[2].textContent = String(item.minutes || 0);
      row.children[3].textContent = money(item.billedPaise);
      row.children[4].textContent = money(item.paidPaise);
      body.append(row);
    }
    if (!body.children.length) body.append(emptyRow('No pool tables found.', 5));
  }

  function renderTopItems(rows) {
    const body = $('operationsKitchenItemsBody');
    body.replaceChildren();
    for (const item of rows || []) {
      const row = document.createElement('tr');
      row.innerHTML = '<td></td><td></td><td></td>';
      row.children[0].textContent = item.name;
      row.children[1].textContent = String(item.quantity || 0);
      row.children[2].textContent = money(item.salesPaise);
      body.append(row);
    }
    if (!body.children.length) body.append(emptyRow('No kitchen sales for this date.', 3));
  }

  function paymentLabel(method) {
    const labels = {
      cash: 'Cash',
      upi: 'UPI',
      card: 'Card',
      bank_transfer: 'Bank transfer',
      other: 'Other',
      unspecified: 'Unspecified',
    };
    return labels[method] || method || 'Unspecified';
  }

  function renderPayments(rows) {
    const body = $('operationsPaymentBody');
    body.replaceChildren();
    for (const item of rows || []) {
      const row = document.createElement('tr');
      row.innerHTML = '<td></td><td></td>';
      row.children[0].textContent = paymentLabel(item.method);
      row.children[1].textContent = money(item.amountPaise);
      body.append(row);
    }
    if (!body.children.length) body.append(emptyRow('No settled operations payments for this date.', 2));
  }

  function renderLowStock(rows) {
    const body = $('operationsLowStockBody');
    body.replaceChildren();
    for (const item of rows || []) {
      const row = document.createElement('tr');
      row.innerHTML = '<td></td><td></td><td></td>';
      row.children[0].textContent = item.name;
      row.children[1].textContent = stock(item.quantityMilli, item.unit);
      row.children[2].textContent = stock(item.lowStockMilli, item.unit);
      body.append(row);
    }
    if (!body.children.length) body.append(emptyRow('No low-stock items.', 3));
  }

  function statusCard(group, label, value) {
    const card = document.createElement('article');
    card.className = 'operations-status-card';
    const type = document.createElement('span');
    type.textContent = group;
    const name = document.createElement('strong');
    name.textContent = label;
    const count = document.createElement('em');
    count.textContent = String(value || 0);
    card.append(type, name, count);
    return card;
  }

  function renderStatuses(report) {
    const root = $('operationsStatusSummary');
    root.replaceChildren();
    const reservations = report.reservations || {};
    const kitchen = report.kitchenStatuses || {};
    const reservationLabels = [
      ['reserved', 'Reserved'],
      ['checked_in', 'Checked in'],
      ['completed', 'Completed'],
      ['cancelled', 'Cancelled'],
      ['no_show', 'No-show'],
    ];
    const kitchenLabels = [
      ['new', 'New'],
      ['preparing', 'Preparing'],
      ['ready', 'Ready'],
      ['served', 'Served'],
      ['cancelled', 'Cancelled'],
    ];
    for (const [key, label] of reservationLabels) {
      root.append(statusCard('POOL BOOKING', label, reservations[key] || 0));
    }
    for (const [key, label] of kitchenLabels) {
      root.append(statusCard('KITCHEN', label, kitchen[key] || 0));
    }
  }

  async function render() {
    const dateInput = $('operationsReportDate');
    if (!dateInput) return;
    $('operationsView').setAttribute('aria-busy', 'true');
    try {
      const query = dateInput.value ? `?date=${encodeURIComponent(dateInput.value)}` : '';
      const data = await core().api(`/api/admin/operations/report${query}`);
      const report = data.report || {};
      if (!dateInput.value && report.date) dateInput.value = report.date;
      renderSummary(report);
      renderPool(report.poolTables || []);
      renderTopItems(report.topKitchenItems || []);
      renderPayments(report.paymentMethods || []);
      renderLowStock(report.lowStock || []);
      renderStatuses(report);
    } catch (error) {
      core().flash(error.data?.message || error.message || 'Operations report is unavailable.', 'error');
    } finally {
      $('operationsView').setAttribute('aria-busy', 'false');
    }
  }

  $('refreshOperationsReport')?.addEventListener('click', () => { void render(); });
  $('operationsReportDate')?.addEventListener('change', () => { void render(); });

  window.NewGymOperationsReport = { renderWorkspace: render };
})();