(() => {
  'use strict';

  function initials(name) {
    return String(name || 'Need For Strength')
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() || '')
      .join('') || 'NG';
  }

  async function applyBrand() {
    try {
      const response = await fetch('/api/health', { credentials: 'same-origin', cache: 'no-store' });
      if (!response.ok) return;
      const payload = await response.json();
      const name = typeof payload.service === 'string' && payload.service.trim()
        ? payload.service.trim()
        : 'Need For Strength';
      const poolName = typeof payload.poolName === 'string' && payload.poolName.trim()
        ? payload.poolName.trim()
        : 'The Cue Master';
      document.title = `${name} Admin`;
      document.querySelectorAll('[data-gym-name]').forEach((node) => { node.textContent = name; });
      document.querySelectorAll('[data-pool-name]').forEach((node) => { node.textContent = poolName; });
      const mark = initials(name);
      document.querySelectorAll('[data-gym-initials]').forEach((node) => { node.textContent = mark; });
    } catch (_) {
      // Static placeholder remains if health/config is unavailable.
    }
  }

  applyBrand();
})();