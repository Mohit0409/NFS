(() => {
  'use strict';

  function initials(name) {
    return String(name || 'New Gym')
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
        : 'New Gym';
      document.title = `${name} Admin`;
      document.querySelectorAll('[data-gym-name]').forEach((node) => { node.textContent = name; });
      const mark = initials(name);
      document.querySelectorAll('[data-gym-initials]').forEach((node) => { node.textContent = mark; });
    } catch (_) {
      // Static placeholder remains if health/config is unavailable.
    }
  }

  applyBrand();
})();