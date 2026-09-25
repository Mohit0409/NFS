(function () {
  'use strict';

  const FIREBASE_SDK_VERSION = '12.18.0';
  const FIREBASE_CONFIG = window.NEW_GYM_CONFIG?.firebase || Object.freeze({});
  const GATEWAY_BASE = window.NEW_GYM_CONFIG?.memberGatewayBase || window.location.origin;
  const loading = document.getElementById('member-loading');
  const signedOut = document.getElementById('member-signed-out');
  const account = document.getElementById('member-account');
  const phoneStep = document.getElementById('phone-step');
  const otpStep = document.getElementById('otp-step');
  const phoneForm = document.getElementById('phone-form');
  const otpForm = document.getElementById('otp-form');
  const phoneStatus = document.getElementById('phone-status');
  const otpStatus = document.getElementById('otp-status');
  const accountStatus = document.getElementById('account-status');
  const resendButton = document.getElementById('resend-otp');
  const phoneInput = document.getElementById('member-phone');
  const otpInput = document.getElementById('member-otp');
  let recaptchaContainer = document.getElementById('recaptcha-container');
  let firebaseApi = null;
  let firebaseAuth = null;
  let firebaseLoadPromise = null;
  let phoneConfirmation = null;
  let recaptchaVerifier = null;
  let normalizedPhone = '';
  let resendTimer = 0;
  let authAttemptInProgress = false;
  let otpThrottleTimer = 0;
  let membershipExpiryTimer = 0;
  let membershipExpiryAt = 0;
  const MAX_EXPIRY_TIMER_MS = 2_000_000_000;
  const OTP_THROTTLE_STORAGE_KEY = 'newGymOtpThrottleUntil';
  const OTP_THROTTLE_SECONDS = 300;

  function setStatus(element, message, state) {
    element.textContent = message || '';
    element.dataset.state = state || '';
  }

  function normalizeIndianPhone(value) {
    let digits = String(value || '').replace(/\D/g, '');
    if (digits.startsWith('0')) digits = digits.slice(1);
    if (digits.length === 12 && digits.startsWith('91')) digits = digits.slice(2);
    return /^[6-9]\d{9}$/.test(digits) ? '+91' + digits : '';
  }

  function maskPhone(phone) {
    return phone ? '+91 XXXXX XX' + phone.slice(-3) : 'your mobile';
  }

  async function loadFirebase() {
    if (firebaseApi && firebaseAuth) return;
    if (!FIREBASE_CONFIG.apiKey || !FIREBASE_CONFIG.authDomain || !FIREBASE_CONFIG.projectId || !FIREBASE_CONFIG.appId) {
      throw new Error('Member login is not configured for this gym yet.');
    }
    if (!firebaseLoadPromise) {
      firebaseLoadPromise = (async () => {
        const base = `https://www.gstatic.com/firebasejs/${FIREBASE_SDK_VERSION}`;
        const [appModule, authModule] = await Promise.all([
          import(`${base}/firebase-app.js`),
          import(`${base}/firebase-auth.js`)
        ]);
        const app = appModule.initializeApp(FIREBASE_CONFIG);
        firebaseAuth = authModule.getAuth(app);
        await authModule.setPersistence(firebaseAuth, authModule.browserSessionPersistence);
        firebaseApi = authModule;
      })();
    }
    try { await firebaseLoadPromise; } catch (error) { firebaseLoadPromise = null; throw error; }
  }

  function rebuildRecaptchaContainer() {
    const fresh = document.createElement('div');
    fresh.id = 'recaptcha-container';
    fresh.setAttribute('aria-hidden', 'true');
    if (recaptchaContainer && recaptchaContainer.parentNode) recaptchaContainer.replaceWith(fresh);
    recaptchaContainer = fresh;
    return fresh;
  }

  function clearRecaptcha({ rebuild = false } = {}) {
    if (recaptchaVerifier) {
      try { recaptchaVerifier.clear(); } catch (_) {}
      recaptchaVerifier = null;
    }
    if (rebuild) rebuildRecaptchaContainer();
    else if (recaptchaContainer) recaptchaContainer.replaceChildren();
  }

  function otpThrottleRemaining() {
    const until = Number(window.sessionStorage.getItem(OTP_THROTTLE_STORAGE_KEY) || 0);
    return Math.max(0, Math.ceil((until - Date.now()) / 1000));
  }

  function stopOtpThrottleTimer() {
    window.clearInterval(otpThrottleTimer);
    otpThrottleTimer = 0;
  }

  function applyOtpThrottleUi() {
    const button = document.getElementById('phone-submit');
    const update = () => {
      const remaining = otpThrottleRemaining();
      if (remaining <= 0) {
        stopOtpThrottleTimer();
        window.sessionStorage.removeItem(OTP_THROTTLE_STORAGE_KEY);
        if (!authAttemptInProgress) button.disabled = false;
        return;
      }
      button.disabled = true;
      const minutes = Math.ceil(remaining / 60);
      setStatus(phoneStatus, 'Firebase temporarily limited OTP requests. Try again in about ' + minutes + ' minute' + (minutes === 1 ? '' : 's') + '.', 'error');
    };
    stopOtpThrottleTimer();
    update();
    if (otpThrottleRemaining() > 0) otpThrottleTimer = window.setInterval(update, 1000);
  }

  function startOtpThrottle(seconds = OTP_THROTTLE_SECONDS) {
    window.sessionStorage.setItem(OTP_THROTTLE_STORAGE_KEY, String(Date.now() + (seconds * 1000)));
    applyOtpThrottleUi();
  }

  function stopCooldown() {
    window.clearInterval(resendTimer);
    resendTimer = 0;
  }

  function clearMembershipExpiryTimer() {
    window.clearTimeout(membershipExpiryTimer);
    membershipExpiryTimer = 0;
    membershipExpiryAt = 0;
  }

  function resetOtpUi({ preservePhone = true } = {}) {
    clearMembershipExpiryTimer();
    stopCooldown();
    phoneConfirmation = null;
    clearRecaptcha();
    otpInput.value = '';
    setStatus(otpStatus, '');
    otpStep.hidden = true;
    phoneStep.hidden = false;
    resendButton.disabled = true;
    resendButton.textContent = 'Resend OTP';
    if (!preservePhone) {
      phoneInput.value = '';
      normalizedPhone = '';
    } else {
      normalizedPhone = normalizeIndianPhone(phoneInput.value) || '';
    }
  }

  function enableImmediateResend() {
    stopCooldown();
    resendButton.disabled = false;
    resendButton.textContent = 'Resend OTP';
  }

  async function jsonRequest(url, options = {}) {
    const { headers = {}, ...requestOptions } = options;
    let response;
    try {
      response = await fetch(url, {
        credentials: 'omit',
        ...requestOptions,
        headers: { Accept: 'application/json', ...headers }
      });
    } catch (cause) {
      const error = new Error('Member service unreachable');
      error.code = 'gateway_unreachable';
      error.cause = cause;
      throw error;
    }
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(payload.message || 'Request failed');
      error.status = response.status;
      error.code = payload.error || 'request_failed';
      throw error;
    }
    return payload;
  }

  async function bootstrapFirebaseUser(user) {
    const idToken = await user.getIdToken();
    return jsonRequest(GATEWAY_BASE + '/api/member/bootstrap', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${idToken}`,
        'ngrok-skip-browser-warning': '1'
      },
      body: ''
    });
  }

  async function revalidateMembershipAtExpiry() {
    const user = firebaseAuth && firebaseAuth.currentUser;
    if (!user) { clearMembershipExpiryTimer(); return; }
    try {
      const payload = await bootstrapFirebaseUser(user);
      renderAccount(payload.user || {}, payload.membership || {});
    } catch (_) {
      clearMembershipExpiryTimer();
      await firebaseApi.signOut(firebaseAuth).catch(() => {});
      resetOtpUi({ preservePhone: true });
      showSignedOut();
      setStatus(phoneStatus, 'Your membership is no longer active. Please contact Need For Strength to renew.', 'error');
    }
  }

  function scheduleMembershipExpiryCheck(endsAt) {
    clearMembershipExpiryTimer();
    const numeric = Number(endsAt || 0);
    membershipExpiryAt = numeric > 0 ? (numeric < 10_000_000_000 ? numeric * 1000 : numeric) : 0;
    if (!membershipExpiryAt) return;
    const arm = () => {
      const remaining = membershipExpiryAt - Date.now();
      if (remaining <= 0) {
        membershipExpiryTimer = 0;
        void revalidateMembershipAtExpiry();
        return;
      }
      membershipExpiryTimer = window.setTimeout(arm, Math.min(remaining, MAX_EXPIRY_TIMER_MS));
    };
    arm();
  }

  function showSignedOut() {
    loading.hidden = true;
    account.hidden = true;
    signedOut.hidden = false;
    phoneStep.hidden = false;
    otpStep.hidden = true;
  }

  function startCooldown(seconds) {
    window.clearInterval(resendTimer);
    let remaining = Math.max(30, Number(seconds) || 60);
    resendButton.disabled = true;
    resendButton.textContent = 'Resend OTP in ' + remaining + 's';
    resendTimer = window.setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        window.clearInterval(resendTimer);
        resendButton.disabled = false;
        resendButton.textContent = 'Resend OTP';
      } else {
        resendButton.textContent = 'Resend OTP in ' + remaining + 's';
      }
    }, 1000);
  }

  function friendlyError(error, context) {
    const code = error && error.code ? String(error.code) : '';
    if (code === 'member_not_eligible') return 'This mobile number is not eligible for member login. Please contact Need For Strength.';
    if (code === 'rate_limited' || code === 'auth/too-many-requests') return 'Too many OTP attempts. Please wait a few minutes before trying again.';
    if (code === 'auth/invalid-verification-code') return 'Incorrect OTP. Check the 6-digit code and try again.';
    if (['auth/code-expired', 'auth/session-expired', 'auth/invalid-verification-id'].includes(code)) return 'This OTP has expired. Tap Resend OTP to get a new code.';
    if (code === 'auth/invalid-phone-number') return 'Enter a valid 10-digit Indian mobile number.';
    if (code === 'auth/quota-exceeded') return 'OTP sending is temporarily limited. Please try again later.';
    if (code === 'auth/network-request-failed') return 'Internet connection problem. Check your connection and try again.';
    if (['auth/captcha-check-failed', 'auth/missing-app-credential', 'auth/invalid-app-credential'].includes(code)) return 'Security verification expired. Please try sending the OTP again.';
    if (['auth/operation-not-allowed', 'auth/app-not-authorized', 'auth/unauthorized-domain', 'auth/invalid-api-key', 'auth/project-not-found'].includes(code)) return 'OTP login is temporarily unavailable. Please contact Need For Strength.';
    if (code === 'auth/user-disabled') return 'This member account is disabled. Please contact Need For Strength.';
    if (code === 'auth/internal-error') return 'OTP service could not complete the request. Please try again.';
    if (['authentication_unavailable', 'account_unavailable', 'gateway_unreachable'].includes(code) || error.status === 503) return 'Member login service is temporarily unavailable. Please try again shortly.';
    if (code === 'invalid_credentials') return context === 'session' ? 'Your login session expired. Please sign in again.' : 'Login verification expired. Please request a new OTP.';
    if (context === 'session') return 'Your member session could not be restored. Please sign in again.';
    const message = error && error.message ? String(error.message) : '';
    if (/recaptcha|captcha|app credential|verification widget/i.test(message)) return 'Security verification could not start. Please try again.';
    return context === 'verify' ? 'OTP verification could not be completed. Please try again.' : 'OTP could not be sent. Please try again.';
  }

  async function checkMemberEligibility(phone) {
    const payload = await jsonRequest(GATEWAY_BASE + '/api/member/eligibility', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': '1'
      },
      body: JSON.stringify({ phone })
    });
    if (!payload.eligible) {
      const error = new Error('Member is not eligible');
      error.code = 'member_not_eligible';
      throw error;
    }
  }

  async function requestOtp() {
    await Promise.all([checkMemberEligibility(normalizedPhone), loadFirebase()]);
    phoneConfirmation = null;
    clearRecaptcha({ rebuild: true });
    if (firebaseAuth.currentUser) await firebaseApi.signOut(firebaseAuth).catch(() => {});
    recaptchaVerifier = new firebaseApi.RecaptchaVerifier(firebaseAuth, recaptchaContainer, { size: 'invisible' });
    phoneConfirmation = await firebaseApi.signInWithPhoneNumber(firebaseAuth, normalizedPhone, recaptchaVerifier);
    phoneStep.hidden = true;
    otpStep.hidden = false;
    document.getElementById('masked-phone').textContent = maskPhone(normalizedPhone);
    otpInput.value = '';
    setStatus(phoneStatus, '');
    setStatus(otpStatus, 'OTP sent. Enter the 6-digit code received on your mobile.', 'success');
    startCooldown(60);
    otpInput.focus();
  }

  phoneForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (authAttemptInProgress) return;
    normalizedPhone = normalizeIndianPhone(phoneInput.value);
    if (!normalizedPhone) {
      setStatus(phoneStatus, 'Enter a valid 10-digit Indian mobile number.', 'error');
      phoneInput.focus();
      return;
    }
    const button = document.getElementById('phone-submit');
    if (otpThrottleRemaining() > 0) { applyOtpThrottleUi(); return; }
    authAttemptInProgress = true;
    button.disabled = true;
    setStatus(otpStatus, '');
    setStatus(phoneStatus, 'Sending OTP...');
    try {
      await requestOtp();
      window.gravityAnalytics?.event('member_otp_sent');
    } catch (error) {
      phoneConfirmation = null;
      clearRecaptcha();
      const code = error && error.code ? String(error.code) : '';
      if (code === 'auth/too-many-requests') startOtpThrottle();
      else setStatus(phoneStatus, friendlyError(error, 'start'), 'error');
    } finally {
      authAttemptInProgress = false;
      button.disabled = otpThrottleRemaining() > 0;
    }
  });

  otpForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (authAttemptInProgress) return;
    const code = otpInput.value.trim();
    if (!/^\d{6}$/.test(code)) {
      setStatus(otpStatus, 'Enter the complete 6-digit OTP.', 'error');
      otpInput.focus();
      return;
    }
    if (!phoneConfirmation) {
      setStatus(otpStatus, 'This OTP session has expired. Tap Resend OTP to get a new code.', 'error');
      enableImmediateResend();
      return;
    }
    const button = document.getElementById('otp-submit');
    authAttemptInProgress = true;
    button.disabled = true;
    setStatus(otpStatus, 'Verifying OTP...');
    try {
      const credential = await phoneConfirmation.confirm(code);
      const payload = await bootstrapFirebaseUser(credential.user);
      phoneConfirmation = null;
      clearRecaptcha();
      stopCooldown();
      renderAccount(payload.user || {}, payload.membership || {});
      window.gravityAnalytics?.event('login', { method: 'phone_otp' });
    } catch (error) {
      const codeValue = error && error.code ? String(error.code) : '';
      if (['auth/code-expired', 'auth/session-expired', 'auth/invalid-verification-id'].includes(codeValue)) {
        phoneConfirmation = null;
        clearRecaptcha();
        enableImmediateResend();
      }
      if (firebaseAuth && firebaseAuth.currentUser && !codeValue.startsWith('auth/')) {
        await firebaseApi.signOut(firebaseAuth).catch(() => {});
        resetOtpUi({ preservePhone: true });
        setStatus(phoneStatus, friendlyError(error, 'verify'), 'error');
        return;
      }
      setStatus(otpStatus, friendlyError(error, 'verify'), 'error');
    } finally {
      authAttemptInProgress = false;
      button.disabled = false;
    }
  });

  document.getElementById('change-number').addEventListener('click', async () => {
    if (authAttemptInProgress) return;
    authAttemptInProgress = true;
    try {
      if (firebaseApi && firebaseAuth) await firebaseApi.signOut(firebaseAuth).catch(() => {});
      resetOtpUi({ preservePhone: false });
      setStatus(phoneStatus, '');
      phoneInput.focus();
    } finally {
      authAttemptInProgress = false;
    }
  });

  resendButton.addEventListener('click', async () => {
    if (resendButton.disabled || !normalizedPhone || authAttemptInProgress) return;
    authAttemptInProgress = true;
    resendButton.disabled = true;
    setStatus(otpStatus, 'Sending a new OTP...');
    try {
      await requestOtp();
    } catch (error) {
      phoneConfirmation = null;
      clearRecaptcha();
      setStatus(otpStatus, friendlyError(error, 'start'), 'error');
      enableImmediateResend();
    } finally {
      authAttemptInProgress = false;
    }
  });

  function formatDate(value) {
    if (!value) return '—';
    const date = typeof value === 'number'
      ? new Date(value > 100000000000 ? value : value * 1000)
      : new Date(value);
    return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(date);
  }

  function formatMoney(paise, currency) {
    const amount = Number(paise);
    if (!Number.isFinite(amount)) return '';
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: currency || 'INR', maximumFractionDigits: 0 }).format(amount / 100);
  }

  function addFact(container, label, value) {
    const item = document.createElement('div');
    item.className = 'account-fact';
    const name = document.createElement('span');
    const data = document.createElement('strong');
    name.textContent = label;
    data.textContent = value || '—';
    item.append(name, data);
    container.appendChild(item);
  }

  function renderMembership(container, membership) {
    container.replaceChildren();
    addFact(container, 'Plan', membership.planName || membership.plan?.name);
    addFact(container, 'Membership Number', membership.membershipNumber);
    addFact(container, 'Status', membership.status);
    addFact(container, 'Start Date', formatDate(membership.startsAt || membership.startDate));
    addFact(container, 'Expiry Date', formatDate(membership.endsAt || membership.expiryDate));
    addFact(container, 'Days Remaining', String(membership.daysRemaining ?? '—'));
  }

  function renderHistory(items, current, upcoming) {
    const history = (Array.isArray(items) ? items : []).filter((item) => item.id !== current?.id && item.id !== upcoming?.id);
    const card = document.getElementById('history-card');
    const list = document.getElementById('membership-history');
    list.replaceChildren();
    card.hidden = history.length === 0;
    history.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'history-item';
      const plan = document.createElement('strong');
      const dates = document.createElement('span');
      const state = document.createElement('span');
      plan.textContent = item.planName || item.plan?.name || 'Membership';
      dates.textContent = formatDate(item.startsAt) + ' – ' + formatDate(item.endsAt);
      state.textContent = item.status || 'Previous';
      row.append(plan, dates, state);
      list.appendChild(row);
    });
  }

  function renderAccount(user, summary) {
    stopCooldown();
    phoneConfirmation = null;
    clearRecaptcha();
    otpInput.value = '';
    setStatus(phoneStatus, '');
    setStatus(otpStatus, '');
    if (user.phone && !phoneInput.value) phoneInput.value = String(user.phone).replace(/^\+91/, '');
    normalizedPhone = normalizeIndianPhone(phoneInput.value) || normalizedPhone;
    const current = summary.current || null;
    const upcoming = summary.upcoming || null;
    const all = summary.all || summary.history || [];
    if (current) scheduleMembershipExpiryCheck(current.endsAt);
    else clearMembershipExpiryTimer();

    document.getElementById('account-name').textContent = user.displayName || user.name || 'Member';
    document.getElementById('account-phone').textContent = maskPhone(user.phone || normalizedPhone);
    signedOut.hidden = true;
    loading.hidden = true;
    account.hidden = false;

    const currentContainer = document.getElementById('current-membership');
    const currentEmpty = document.getElementById('current-empty');
    currentContainer.hidden = !current;
    currentEmpty.hidden = Boolean(current);
    document.getElementById('current-state').textContent = current?.status || 'No current plan';
    if (current) renderMembership(currentContainer, current);

    const upcomingCard = document.getElementById('upcoming-card');
    upcomingCard.hidden = !upcoming;
    if (upcoming) renderMembership(document.getElementById('upcoming-membership'), upcoming);

    const pendingPaise = current?.payment?.pendingPaise ?? current?.pendingPaise;
    const balanceNote = document.getElementById('balance-note');
    const pendingText = formatMoney(pendingPaise, current?.currency);
    balanceNote.hidden = !pendingText || Number(pendingPaise) <= 0;
    if (!balanceNote.hidden) document.getElementById('pending-balance').textContent = 'Pending at gym: ' + pendingText;

    renderHistory(all, current, upcoming);
    setStatus(accountStatus, '');
  }

  async function initialize() {
    showSignedOut();
    try {
      await loadFirebase();
      if (typeof firebaseAuth.authStateReady === 'function') await firebaseAuth.authStateReady();
      const user = firebaseAuth.currentUser;
      if (!user) {
        if (!authAttemptInProgress && !phoneConfirmation) {
          resetOtpUi({ preservePhone: true });
          showSignedOut();
          setStatus(phoneStatus, '');
          if (otpThrottleRemaining() > 0) applyOtpThrottleUi();
        }
        return;
      }
      const payload = await bootstrapFirebaseUser(user);
      renderAccount(payload.user || {}, payload.membership || {});
    } catch (error) {
      if (firebaseApi && firebaseAuth) await firebaseApi.signOut(firebaseAuth).catch(() => {});
      resetOtpUi({ preservePhone: true });
      showSignedOut();
      setStatus(phoneStatus, friendlyError(error, 'session'), 'error');
    }
  }

  document.getElementById('logout-button').addEventListener('click', async () => {
    if (authAttemptInProgress) return;
    const button = document.getElementById('logout-button');
    authAttemptInProgress = true;
    button.disabled = true;
    setStatus(accountStatus, 'Logging out...');
    try {
      stopCooldown();
      phoneConfirmation = null;
      clearRecaptcha();
      if (firebaseApi && firebaseAuth) await firebaseApi.signOut(firebaseAuth);
      resetOtpUi({ preservePhone: false });
      showSignedOut();
      setStatus(accountStatus, '');
      setStatus(phoneStatus, 'Logged out successfully. Enter your mobile number to sign in again.', 'success');
      phoneInput.focus();
    } catch (_) {
      setStatus(accountStatus, 'Logout could not be completed. Please check your connection and try again.', 'error');
    } finally {
      authAttemptInProgress = false;
      button.disabled = false;
    }
  });

  initialize();
})();
