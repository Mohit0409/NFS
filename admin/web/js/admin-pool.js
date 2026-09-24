(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const money = (paise) => paise == null ? 'Not set' : `₹${(Number(paise) / 100).toFixed(0)} / hr`;
  const duration = (seconds) => {
    const total = Math.max(0, Number(seconds || 0));
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    return h ? `${h}h ${m}m` : `${m}m`;
  };
  const dateTime = (seconds) => new Intl.DateTimeFormat('en-IN', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
  }).format(new Date(Number(seconds) * 1000));

  function core() { return window.GravityAdminCore; }

  let editingReservationId = null;

  function toLocalInput(date) {
    const pad = (value) => String(value).padStart(2, '0');
    return [
      date.getFullYear(), '-', pad(date.getMonth() + 1), '-', pad(date.getDate()),
      'T', pad(date.getHours()), ':', pad(date.getMinutes())
    ].join('');
  }

  function setReservationDefaults() {
    const start = $('poolReservationStart');
    const end = $('poolReservationEnd');
    if (!start || !end || start.value || end.value) return;
    const now = new Date();
    const rounded = new Date(Math.ceil(now.getTime() / (15 * 60 * 1000)) * 15 * 60 * 1000);
    const finish = new Date(rounded.getTime() + 60 * 60 * 1000);
    start.value = toLocalInput(rounded);
    end.value = toLocalInput(finish);
  }

  async function saveRate(table, input) {
    const value = input.value.trim();
    const paise = value === '' ? null : Math.round(Number(value) * 100);
    if (value !== '' && (!Number.isFinite(paise) || paise < 0)) {
      core().flash('Enter a valid hourly rate.', 'error');
      return;
    }
    await core().api(`/api/admin/pool/tables/${encodeURIComponent(table.id)}`, {
      method: 'PATCH',
      body: { defaultRatePaise: paise },
    });
    core().flash('Pool rate saved.');
    await render();
  }

  async function start(table, card) {
    const rateInput = card.querySelector('[data-pool-rate]');
    const guestInput = card.querySelector('[data-pool-guest]');
    const raw = rateInput.value.trim();
    const ratePaise = raw === '' ? table.defaultRatePaise : Math.round(Number(raw) * 100);
    if (ratePaise == null || !Number.isFinite(ratePaise) || ratePaise < 0) {
      core().flash('Set an hourly rate before starting the session.', 'error');
      return;
    }
    await core().api('/api/admin/pool/sessions', {
      method: 'POST',
      body: {
        tableId: table.id,
        ratePaisePerHour: ratePaise,
        guestName: guestInput.value.trim() || null,
      },
    });
    core().flash(`${table.name} session started.`);
    await render();
  }

  async function endSession(table) {
    const session = table.activeSession;
    if (!session) return;
    await core().api(`/api/admin/pool/sessions/${encodeURIComponent(session.id)}/end`, {
      method: 'POST',
      body: {},
    });
    core().flash(`${table.name} session completed.`);
    await render();
  }

  function tableCard(table) {
    const card = document.createElement('article');
    card.className = 'ops-card pool-table-card';
    const session = table.activeSession;
    const next = table.nextReservation;
    card.innerHTML = `
      <div class="ops-card-head">
        <div><span class="ops-kicker">${table.type === 'private' ? 'PRIVATE' : 'COMMON'}</span><h3></h3></div>
        <span class="ops-status" data-status="${table.status}">${table.status}</span>
      </div>
      <p class="ops-rate">${money(table.defaultRatePaise)}</p>
      <div class="pool-active" ${session ? '' : 'hidden'}>
        <strong>Session running</strong>
        <span>${session ? duration(session.elapsedSeconds) : ''}</span>
        <small>${session?.guestName || 'Walk-in / member'}</small>
      </div>
      <div class="pool-next-reservation" ${!next || session ? 'hidden' : ''}>
        <small>Next reservation</small>
        <strong>${next ? dateTime(next.startsAt) : ''}</strong>
        <span>${next?.guestName || ''}</span>
      </div>
      <div class="pool-start" ${session ? 'hidden' : ''}>
        <label>Guest / member name<input data-pool-guest maxlength="80" placeholder="Optional"></label>
        <label>Hourly rate ₹<input data-pool-rate type="number" min="0" step="1" value="${table.defaultRatePaise == null ? '' : table.defaultRatePaise / 100}"></label>
      </div>
      <div class="row-actions pool-actions"></div>
    `;
    card.querySelector('h3').textContent = table.name;
    const actions = card.querySelector('.pool-actions');
    if (session) {
      const end = document.createElement('button');
      end.type = 'button';
      end.textContent = 'End session';
      end.addEventListener('click', () => endSession(table).catch((error) => core().flash(error.data?.message || error.message, 'error')));
      actions.append(end);
    } else {
      const startButton = document.createElement('button');
      startButton.type = 'button';
      startButton.textContent = 'Start walk-in';
      startButton.disabled = ['cleaning', 'disabled'].includes(table.status);
      startButton.addEventListener('click', () => start(table, card).catch((error) => core().flash(error.data?.message || error.message, 'error')));
      actions.append(startButton);
      if (core().hasPermission('pool.manage')) {
        const save = document.createElement('button');
        save.type = 'button';
        save.className = 'ghost';
        save.textContent = 'Save rate';
        save.addEventListener('click', () => saveRate(table, card.querySelector('[data-pool-rate]')).catch((error) => core().flash(error.message, 'error')));
        actions.append(save);
      }
    }
    return card;
  }

  function populateReservationTables(tables) {
    const select = $('poolReservationTable');
    if (!select) return;
    const selected = select.value;
    select.replaceChildren();
    for (const table of tables || []) {
      const option = new Option(
        `${table.name}${table.defaultRatePaise == null ? '' : ' · ' + money(table.defaultRatePaise)}`,
        table.id,
      );
      option.disabled = table.status === 'disabled';
      select.append(option);
    }
    if ([...select.options].some((option) => option.value === selected)) select.value = selected;
    setReservationDefaults();
  }

  function resetReservationForm() {
    editingReservationId = null;
    $('poolReservationForm').reset();
    $('poolReservationSubmit').textContent = 'Create reservation';
    $('poolReservationCancelEdit').hidden = true;
    setReservationDefaults();
  }

  function beginReservationEdit(reservation) {
    editingReservationId = reservation.id;
    $('poolReservationTable').value = reservation.tableId;
    $('poolReservationGuest').value = reservation.guestName || '';
    $('poolReservationPhone').value = reservation.phone || '';
    $('poolReservationRate').value = reservation.ratePaisePerHour == null
      ? ''
      : String(reservation.ratePaisePerHour / 100);
    $('poolReservationStart').value = toLocalInput(new Date(Number(reservation.startsAt) * 1000));
    $('poolReservationEnd').value = toLocalInput(new Date(Number(reservation.endsAt) * 1000));
    $('poolReservationNote').value = reservation.note || '';
    $('poolReservationSubmit').textContent = 'Update reservation';
    $('poolReservationCancelEdit').hidden = false;
    $('poolReservationForm').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  async function saveReservation(event) {
    event.preventDefault();
    const startMs = Date.parse($('poolReservationStart').value);
    const endMs = Date.parse($('poolReservationEnd').value);
    if (!Number.isFinite(startMs) || !Number.isFinite(endMs) || endMs <= startMs) {
      core().flash('Choose a valid reservation start and end time.', 'error');
      return;
    }
    const rawRate = $('poolReservationRate').value.trim();
    const ratePaise = rawRate === '' ? null : Math.round(Number(rawRate) * 100);
    if (rawRate !== '' && (!Number.isFinite(ratePaise) || ratePaise < 0)) {
      core().flash('Enter a valid reservation hourly rate.', 'error');
      return;
    }
    const body = {
      tableId: $('poolReservationTable').value,
      guestName: $('poolReservationGuest').value.trim(),
      phone: $('poolReservationPhone').value.trim() || null,
      ratePaisePerHour: ratePaise,
      startsAt: Math.floor(startMs / 1000),
      endsAt: Math.floor(endMs / 1000),
      note: $('poolReservationNote').value.trim() || null,
    };
    const editing = editingReservationId;
    await core().api(
      editing
        ? `/api/admin/pool/reservations/${encodeURIComponent(editing)}`
        : '/api/admin/pool/reservations',
      {
        method: editing ? 'PATCH' : 'POST',
        body,
      },
    );
    resetReservationForm();
    core().flash(editing ? 'Pool reservation updated.' : 'Pool reservation created.');
    await render();
  }

  async function updateReservationStatus(reservation, status) {
    await core().api(`/api/admin/pool/reservations/${encodeURIComponent(reservation.id)}`, {
      method: 'PATCH',
      body: { status },
    });
    core().flash(status === 'cancelled' ? 'Reservation cancelled.' : 'Reservation marked no-show.');
    await render();
  }

  async function checkInReservation(reservation) {
    await core().api('/api/admin/pool/sessions', {
      method: 'POST',
      body: {
        reservationId: reservation.id,
        tableId: reservation.tableId,
      },
    });
    core().flash(`${reservation.tableName} checked in and timer started.`);
    await render();
  }

  async function renderReservations() {
    const data = await core().api('/api/admin/pool/reservations?status=reserved&limit=100');
    const body = $('poolReservationsBody');
    if (!body) return;
    body.replaceChildren();
    for (const item of data.reservations || []) {
      const row = document.createElement('tr');
      row.innerHTML = '<td></td><td></td><td></td><td></td><td></td>';
      row.children[0].textContent = `${dateTime(item.startsAt)} – ${dateTime(item.endsAt)}`;
      row.children[1].textContent = item.tableName || item.tableId;
      row.children[2].textContent = item.guestName || 'Member';
      row.children[3].textContent = item.status;
      const actions = document.createElement('div');
      actions.className = 'row-actions compact-actions';

      const edit = document.createElement('button');
      edit.type = 'button';
      edit.className = 'ghost';
      edit.textContent = 'Edit';
      edit.addEventListener('click', () => beginReservationEdit(item));
      actions.append(edit);

      const checkIn = document.createElement('button');
      checkIn.type = 'button';
      checkIn.textContent = 'Check in';
      checkIn.addEventListener('click', () => checkInReservation(item).catch((error) => core().flash(error.data?.message || error.message, 'error')));
      actions.append(checkIn);

      const cancel = document.createElement('button');
      cancel.type = 'button';
      cancel.className = 'ghost';
      cancel.textContent = 'Cancel';
      cancel.addEventListener('click', () => updateReservationStatus(item, 'cancelled').catch((error) => core().flash(error.data?.message || error.message, 'error')));
      actions.append(cancel);

      const noShow = document.createElement('button');
      noShow.type = 'button';
      noShow.className = 'ghost';
      noShow.textContent = 'No-show';
      noShow.addEventListener('click', () => updateReservationStatus(item, 'no_show').catch((error) => core().flash(error.data?.message || error.message, 'error')));
      actions.append(noShow);

      row.children[4].append(actions);
      body.append(row);
    }
    if (!body.children.length) {
      const row = document.createElement('tr');
      row.innerHTML = '<td colspan="5" class="empty">No upcoming pool reservations.</td>';
      body.append(row);
    }
  }

  let currentBillSessionId = null;
  const currency = (paise) => `₹${(Number(paise || 0) / 100).toFixed(2)}`;

  function renderBill(bill) {
    currentBillSessionId = bill.session.id;
    const summary = $('poolBillSummary');
    summary.replaceChildren();
    const facts = [
      ['Pool', currency(bill.poolChargePaise)],
      ['Kitchen', currency(bill.kitchenTotalPaise)],
      ['Grand total', currency(bill.grandTotalPaise)],
      ['Due', currency(bill.duePaise)],
    ];
    for (const [label, value] of facts) {
      const item = document.createElement('div');
      item.innerHTML = '<span></span><strong></strong>';
      item.querySelector('span').textContent = label;
      item.querySelector('strong').textContent = value;
      summary.append(item);
    }

    $('poolBillTitle').textContent = `${bill.tableName} · Final bill`;
    const body = $('poolBillKitchenBody');
    body.replaceChildren();
    for (const order of bill.kitchenOrders || []) {
      const row = document.createElement('tr');
      row.innerHTML = '<td></td><td></td><td></td><td></td>';
      row.children[0].textContent = `#${String(order.id).slice(0, 8)}`;
      row.children[1].textContent = order.status;
      row.children[2].textContent = order.paymentStatus;
      row.children[3].textContent = currency(order.totalPaise);
      body.append(row);
    }
    if (!body.children.length) {
      const row = document.createElement('tr');
      row.innerHTML = '<td colspan="4" class="empty">No kitchen orders linked to this pool session.</td>';
      body.append(row);
    }

    const blocker = $('poolBillBlocker');
    blocker.hidden = true;
    blocker.replaceChildren();
    if (bill.session.status !== 'completed') {
      blocker.hidden = false;
      blocker.textContent = 'End the pool session before settling the final bill.';
    } else if (!bill.settlementReady) {
      blocker.hidden = false;
      blocker.textContent = 'Finish or cancel all kitchen orders before settling this bill.';
    }

    const paid = Number(bill.duePaise || 0) === 0 && bill.session.paymentStatus === 'paid';
    $('poolBillPaymentWrap').hidden = paid;
    const settle = $('settlePoolBill');
    settle.hidden = paid;
    settle.disabled = bill.session.status !== 'completed' || !bill.settlementReady;
    $('poolBillError').textContent = '';
  }

  async function openBill(session) {
    const data = await core().api(`/api/admin/pool/sessions/${encodeURIComponent(session.id)}/bill`);
    renderBill(data.bill);
    const dialog = $('poolBillDialog');
    if (!dialog.open) dialog.showModal();
  }

  async function settleBill() {
    if (!currentBillSessionId) return;
    const data = await core().api(`/api/admin/pool/sessions/${encodeURIComponent(currentBillSessionId)}/settle`, {
      method: 'POST',
      body: { paymentMethod: $('poolBillPaymentMethod').value },
    });
    renderBill(data.bill);
    core().flash('Pool + kitchen final bill settled.');
    await renderHistory();
  }

  async function renderHistory() {
    const data = await core().api('/api/admin/pool/sessions?limit=30');
    const body = $('poolHistoryBody');
    body.replaceChildren();
    for (const item of data.sessions || []) {
      const row = document.createElement('tr');
      const charge = item.amountPaise == null
        ? (item.status === 'active' ? 'Running' : '—')
        : currency(item.amountPaise);
      row.innerHTML = '<td></td><td></td><td></td><td></td><td></td><td></td>';
      row.children[0].textContent = item.tableName || item.tableId;
      row.children[1].textContent = item.guestName || 'Walk-in / member';
      row.children[2].textContent = duration(item.elapsedSeconds);
      row.children[3].textContent = item.status;
      row.children[4].textContent = charge;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = item.paymentStatus === 'paid' ? 'ghost compact-button' : 'compact-button';
      button.textContent = item.paymentStatus === 'paid' ? 'Paid bill' : 'View bill';
      button.addEventListener('click', () => openBill(item).catch((error) => core().flash(error.data?.message || error.message, 'error')));
      row.children[5].append(button);
      body.append(row);
    }
    if (!body.children.length) {
      const row = document.createElement('tr');
      row.innerHTML = '<td colspan="6" class="empty">No pool sessions yet.</td>';
      body.append(row);
    }
  }

  async function render() {
    const grid = $('poolTableGrid');
    if (!grid) return;
    grid.setAttribute('aria-busy', 'true');
    try {
      const data = await core().api('/api/admin/pool/tables');
      grid.replaceChildren(...(data.tables || []).map(tableCard));
      populateReservationTables(data.tables || []);
      await Promise.all([renderReservations(), renderHistory()]);
    } finally {
      grid.setAttribute('aria-busy', 'false');
    }
  }

  $('poolReservationForm')?.addEventListener('submit', (event) => {
    saveReservation(event).catch((error) => core().flash(error.data?.message || error.message, 'error'));
  });
  $('poolReservationCancelEdit')?.addEventListener('click', () => {
    resetReservationForm();
  });
  $('settlePoolBill')?.addEventListener('click', () => {
    settleBill().catch((error) => {
      $('poolBillError').textContent = error.data?.message || error.message;
    });
  });

  window.NewGymPoolAdmin = { renderWorkspace: render };
})();