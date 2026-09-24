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

  function core() { return window.GravityAdminCore; }

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
      startButton.textContent = 'Start session';
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

  async function renderHistory() {
    const data = await core().api('/api/admin/pool/sessions?limit=30');
    const body = $('poolHistoryBody');
    body.replaceChildren();
    for (const item of data.sessions || []) {
      const row = document.createElement('tr');
      const charge = item.amountPaise == null ? '—' : `₹${(item.amountPaise / 100).toFixed(2)}`;
      row.innerHTML = `<td></td><td></td><td></td><td></td><td></td>`;
      row.children[0].textContent = item.tableName || item.tableId;
      row.children[1].textContent = item.guestName || 'Walk-in / member';
      row.children[2].textContent = duration(item.elapsedSeconds);
      row.children[3].textContent = item.status;
      row.children[4].textContent = charge;
      body.append(row);
    }
    if (!body.children.length) {
      const row = document.createElement('tr');
      row.innerHTML = '<td colspan="5" class="empty">No pool sessions yet.</td>';
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
      await renderHistory();
    } finally {
      grid.setAttribute('aria-busy', 'false');
    }
  }

  window.NewGymPoolAdmin = { renderWorkspace: render };
})();