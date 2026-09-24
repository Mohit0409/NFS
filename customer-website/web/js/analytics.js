(function () {
  'use strict';

  const SDK_VERSION = '12.18.0';
  const CONFIG = window.NEW_GYM_CONFIG?.analyticsFirebase || Object.freeze({});

  let analyticsPromise = null;

  function initAnalytics() {
    if (analyticsPromise) return analyticsPromise;
    if (!CONFIG.apiKey || !CONFIG.projectId || !CONFIG.appId || !CONFIG.measurementId) {
      analyticsPromise = Promise.resolve(null);
      return analyticsPromise;
    }
    const base = `https://www.gstatic.com/firebasejs/${SDK_VERSION}`;
    analyticsPromise = Promise.all([
      import(`${base}/firebase-app.js`),
      import(`${base}/firebase-analytics.js`)
    ]).then(async ([appModule, analyticsModule]) => {
      if (!(await analyticsModule.isSupported())) return null;
      const app = appModule.initializeApp(CONFIG, 'new-gym-analytics');
      const analytics = analyticsModule.getAnalytics(app);
      analyticsModule.setConsent?.({
        analytics_storage: 'granted',
        ad_storage: 'denied',
        ad_user_data: 'denied',
        ad_personalization: 'denied'
      });
      return { analytics, logEvent: analyticsModule.logEvent };
    }).catch(() => null);
    return analyticsPromise;
  }

  function validEventName(name) {
    return /^[a-z][a-z0-9_]{0,39}$/.test(String(name || ''));
  }

  window.gravityAnalytics = Object.freeze({
    event(name, params) {
      if (!validEventName(name)) return;
      const safe = {};
      if (params && typeof params.method === 'string') safe.method = params.method.slice(0, 40);
      initAnalytics().then((api) => {
        if (api) api.logEvent(api.analytics, name, safe);
      });
    }
  });

  document.addEventListener('click', (event) => {
    const link = event.target.closest && event.target.closest('a[href]');
    if (!link) return;
    const href = String(link.getAttribute('href') || '');
    if (href.includes('diet-planner.html') && !window.location.pathname.endsWith('/diet-planner.html')) {
      window.gravityAnalytics.event('diet_planner_cta_click');
    } else if (href.includes('exercises.html') && !window.location.pathname.endsWith('/exercises.html')) {
      window.gravityAnalytics.event('exercise_library_cta_click');
    } else if (href.startsWith('https://wa.me/')) {
      window.gravityAnalytics.event('whatsapp_contact_click');
    } else if (href.startsWith('tel:')) {
      window.gravityAnalytics.event('phone_contact_click');
    }
  }, { capture: true });

  initAnalytics();
  if (window.location.pathname.endsWith('/diet-planner.html')) {
    window.gravityAnalytics.event('diet_planner_open');
  } else if (window.location.pathname.endsWith('/exercises.html')) {
    window.gravityAnalytics.event('exercise_library_open');
  } else if (window.location.pathname.endsWith('/member-login.html')) {
    window.gravityAnalytics.event('member_login_open');
  }
})();
