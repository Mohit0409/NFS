(function () {
  'use strict';

  const cfg = window.NEW_GYM_CONFIG || {};

  function configured(value) {
    return typeof value === 'string' && value.trim() ? value.trim() : '';
  }

  function replaceText(root, from, to) {
    if (!root || !from || !to || from === to) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) {
      const node = walker.currentNode;
      const parent = node.parentElement;
      if (!parent || ['SCRIPT', 'STYLE'].includes(parent.tagName)) continue;
      if (node.nodeValue.includes(from)) nodes.push(node);
    }
    nodes.forEach((node) => { node.nodeValue = node.nodeValue.split(from).join(to); });
  }

  function replaceAttributes(from, to) {
    if (!from || !to || from === to) return;
    for (const element of document.querySelectorAll('[title],[aria-label],[alt],[content]')) {
      for (const name of ['title', 'aria-label', 'alt', 'content']) {
        if (!element.hasAttribute(name)) continue;
        const value = element.getAttribute(name);
        if (value && value.includes(from)) {
          element.setAttribute(name, value.split(from).join(to));
        }
      }
    }
  }

  function formatPrice(paise) {
    if (!Number.isFinite(Number(paise)) || Number(paise) < 0) return 'Ask';
    const rupees = Number(paise) / 100;
    return '₹' + rupees.toLocaleString('en-IN', {
      minimumFractionDigits: Number.isInteger(rupees) ? 0 : 2,
      maximumFractionDigits: 2
    });
  }

  function setLink(selector, href, label) {
    for (const element of document.querySelectorAll(selector)) {
      if (href) {
        element.href = href;
        element.removeAttribute('aria-disabled');
        if (/^https?:/i.test(href)) {
          element.target = '_blank';
          element.rel = 'noopener noreferrer';
        }
      }
      if (label) element.textContent = label;
    }
  }

  function apply() {
    const name = configured(cfg.name) || 'New Gym';
    const city = configured(cfg.city);

    replaceText(document.body, 'NEW GYM', name.toUpperCase());
    replaceText(document.body, 'New Gym', name);
    replaceAttributes('New Gym', name);
    if (city) {
      replaceText(document.body, 'Your City', city);
      replaceText(document.body, 'Location to be configured', city);
      replaceAttributes('Your City', city);
    }

    document.title = document.title.replaceAll('New Gym', name);

    const phoneDisplay = configured(cfg.phoneDisplay);
    const phoneHref = configured(cfg.phoneHref);
    if (phoneDisplay && phoneHref) {
      setLink('[data-gym-phone-link]', phoneHref, phoneDisplay);
    }

    const whatsapp = configured(cfg.whatsappNumber);
    if (whatsapp) {
      const digits = whatsapp.replace(/\D/g, '');
      if (digits) setLink('[data-gym-whatsapp-link]', 'https://wa.me/' + digits, 'WhatsApp');
    }

    const instagram = configured(cfg.instagramUrl);
    if (instagram) {
      setLink('[data-gym-instagram-link]', instagram, 'Instagram');
    }

    const address = configured(cfg.address);
    if (address) {
      document.querySelectorAll('[data-gym-address]').forEach((node) => { node.textContent = address; });
    }

    const hours = configured(cfg.openingHours);
    if (hours) {
      document.querySelectorAll('[data-gym-opening-hours]').forEach((node) => { node.textContent = hours; });
    }

    const mapUrl = configured(cfg.mapUrl);
    if (mapUrl) {
      setLink('[data-gym-map-link]', mapUrl, 'Open in Google Maps');
    }

    const embed = configured(cfg.mapEmbedUrl);
    if (embed) {
      document.querySelectorAll('[data-gym-map-frame]').forEach((frame) => { frame.src = embed; });
    }

    const pricing = cfg.membershipPricesPaise || {};
    document.querySelectorAll('[data-plan-key]').forEach((card) => {
      const key = card.dataset.planKey;
      const priceNode = card.querySelector('[data-plan-price]');
      if (!priceNode) return;
      priceNode.textContent = formatPrice(pricing[key]);
    });

    const siteUrl = configured(cfg.siteUrl);
    if (siteUrl) {
      const clean = siteUrl.replace(/\/$/, '');
      document.querySelector('link[rel="canonical"]')?.setAttribute('href', clean + '/');
      document.querySelector('meta[property="og:url"]')?.setAttribute('content', clean + '/');
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', apply, { once: true });
  } else {
    apply();
  }
})();