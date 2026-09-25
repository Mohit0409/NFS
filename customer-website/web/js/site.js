(function () {
  'use strict';

  const menuButton = document.getElementById('menu-button');
  const mobileMenu = document.getElementById('mobile-menu');
  const header = document.getElementById('site-header');
  const enquiryForm = document.getElementById('enquiry-form');
  const interestField = document.getElementById('enquiry-interest');
  const status = document.getElementById('enquiry-status');
  const bmiForm = document.getElementById('bmi-form');
  const bmiResult = document.getElementById('bmi-result');
  const bmiError = document.getElementById('bmi-error');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const gymConfig = window.NEW_GYM_CONFIG || { name: 'Need For Strength', whatsappNumber: '' };

  function setMenu(open) {
    if (!menuButton || !mobileMenu) return;
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    mobileMenu.hidden = !open;
    document.body.classList.toggle('menu-open', open);
    if (open) mobileMenu.querySelector('a,button')?.focus();
  }

  menuButton?.addEventListener('click', () => {
    setMenu(menuButton.getAttribute('aria-expanded') !== 'true');
  });
  mobileMenu?.addEventListener('click', (event) => {
    if (event.target.closest('a')) setMenu(false);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menuButton?.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      menuButton.focus();
    }
  });

  function interestLabel(key) {
    return {
      membership: 'Membership',
      coaching: 'Training & Coaching',
      nutrition: 'Diet & Nutrition Guidance',
      visit: 'Gym Visit',
      general: 'General Enquiry'
    }[key] || 'General Enquiry';
  }

  document.querySelectorAll('[data-enquiry]').forEach((button) => {
    button.addEventListener('click', () => {
      window.gravityAnalytics?.event('enquiry_opened');
      if (interestField) interestField.value = interestLabel(button.dataset.enquiry);
      document.getElementById('enquiry')?.scrollIntoView({
        behavior: reducedMotion ? 'auto' : 'smooth',
        block: 'start'
      });
      window.setTimeout(() => document.getElementById('enquiry-name')?.focus(), reducedMotion ? 0 : 500);
      setMenu(false);
    });
  });

  function validPhone(value) {
    const digits = String(value || '').replace(/\D/g, '');
    return /^(?:91)?[6-9]\d{9}$/.test(digits);
  }

  enquiryForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    const form = new FormData(enquiryForm);
    const name = String(form.get('name') || '').trim();
    const phone = String(form.get('phone') || '').trim();
    const interest = String(form.get('interest') || '').trim();
    const message = String(form.get('message') || '').trim();

    status.textContent = '';
    if (!name || !validPhone(phone) || !interest) {
      status.textContent = 'Please enter your name, a valid Indian mobile number and the information you need.';
      status.dataset.state = 'error';
      enquiryForm.querySelector(':invalid')?.focus();
      return;
    }

    const whatsappNumber = String(gymConfig.whatsappNumber || '').replace(/\D/g, '');
    if (!whatsappNumber) {
      status.textContent = 'WhatsApp contact is not configured for this gym yet.';
      status.dataset.state = 'error';
      return;
    }

    const lines = [
      'Hello ' + (gymConfig.name || 'Need For Strength') + ',',
      '',
      'I would like information about: ' + interest,
      'Name: ' + name,
      'Mobile: ' + phone
    ];
    if (message) lines.push('Message: ' + message);
    lines.push('', 'Please share the current details with me.');

    if (!gymConfig.whatsappNumber) {
      status.textContent = 'WhatsApp contact is not configured for this gym yet.';
      status.dataset.state = 'error';
      return;
    }
    const url = 'https://wa.me/' + gymConfig.whatsappNumber + '?text=' + encodeURIComponent(lines.join('\n'));
    const opened = window.open(url, '_blank', 'noopener,noreferrer');
    if (opened) opened.opener = null;
    status.textContent = 'WhatsApp opened with your enquiry ready to review and send.';
    status.dataset.state = 'success';
    window.gravityAnalytics?.event('generate_lead');
  });

  function bmiCategory(value) {
    if (value < 18.5) return 'Below the desirable adult range. Consider discussing healthy weight gain with a qualified professional.';
    if (value < 23) return 'Within the desirable adult range for Indian and other Asian populations.';
    if (value <= 27.5) return 'Within the overweight range for Indian and other Asian populations. Use this as a prompt to review your routine with a qualified professional.';
    return 'Above the adult overweight range. Consider speaking with a doctor or registered dietitian for personalised guidance.';
  }

  bmiForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    const weight = Number(document.getElementById('bmi-weight')?.value);
    const height = Number(document.getElementById('bmi-height')?.value);

    bmiError.textContent = '';
    bmiResult.hidden = true;
    if (!Number.isFinite(weight) || !Number.isFinite(height) || weight < 35 || weight > 250 || height < 130 || height > 220) {
      bmiError.textContent = 'Enter a weight from 35–250 kg and a height from 130–220 cm.';
      bmiForm.querySelector(':invalid')?.focus();
      return;
    }

    const metres = height / 100;
    const bmi = weight / (metres * metres);
    document.getElementById('bmi-value').textContent = bmi.toFixed(1);
    document.getElementById('bmi-message').textContent = bmiCategory(bmi);
    bmiResult.hidden = false;
    window.gravityAnalytics?.event('bmi_calculated');
  });

  if (header) {
    const updateHeader = () => header.classList.toggle('is-scrolled', window.scrollY > 16);
    updateHeader();
    window.addEventListener('scroll', updateHeader, { passive: true });
  }

  const revealTargets = document.querySelectorAll('.reveal');
  if (reducedMotion || !('IntersectionObserver' in window)) {
    revealTargets.forEach((element) => element.classList.add('is-visible'));
  } else {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -24px' });
    revealTargets.forEach((element) => observer.observe(element));
  }

  const year = document.getElementById('current-year');
  if (year) year.textContent = String(new Date().getFullYear());
})();
