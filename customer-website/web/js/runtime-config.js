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

  function renderMembershipOffers() {
    const offers = Array.isArray(cfg.membershipOffers) ? cfg.membershipOffers : [];
    const grid = document.querySelector('.pricing-grid');
    if (!grid || !offers.length) return;
    grid.replaceChildren();
    for (const offer of offers) {
      const card = document.createElement('article');
      card.className = 'price-card reveal owner-offer-card' + (offer.featured ? ' price-card--featured' : '');
      if (offer.badge) {
        const badge = document.createElement('span');
        badge.className = 'price-badge';
        badge.textContent = offer.badge;
        card.append(badge);
      }
      const title = document.createElement('h3');
      title.className = 'owner-offer-title';
      title.textContent = offer.title || 'Membership';
      card.append(title);
      const list = document.createElement('div');
      list.className = 'owner-offer-lines';
      for (const line of Array.isArray(offer.lines) ? offer.lines : []) {
        const row = document.createElement('div');
        row.className = 'owner-offer-line';
        const label = document.createElement('span');
        label.textContent = line.label || '';
        const price = document.createElement('strong');
        price.textContent = line.price || 'Ask';
        row.append(label, price);
        if (line.note) {
          const note = document.createElement('small');
          note.textContent = line.note;
          row.append(note);
        }
        list.append(row);
      }
      card.append(list);
      const button = document.createElement('button');
      button.className = 'button button--outline price-card__cta';
      button.type = 'button';
      button.dataset.enquiry = 'membership';
      button.textContent = 'Enquire About This Plan';
      card.append(button);
      grid.append(card);
    }
  }

  function renderPersonalTraining() {
    const offers = Array.isArray(cfg.personalTrainingOffers) ? cfg.personalTrainingOffers : [];
    const root = document.querySelector('[data-pt-offers]');
    if (!root || !offers.length) return;
    root.replaceChildren();
    for (const offer of offers) {
      const card = document.createElement('article');
      card.className = 'pt-package-card';
      const eyebrow = document.createElement('p');
      eyebrow.className = 'pt-package-card__eyebrow';
      eyebrow.textContent = 'Personal Training';
      const price = document.createElement('strong');
      price.className = 'pt-package-card__price';
      price.textContent = offer.price || 'Ask';
      const label = document.createElement('p');
      label.className = 'pt-package-card__label';
      label.textContent = offer.label || '';
      const button = document.createElement('button');
      button.className = 'button button--outline pt-package-card__cta';
      button.type = 'button';
      button.dataset.enquiry = 'coaching';
      button.textContent = 'Enquire Now';
      card.append(eyebrow, price, label, button);
      root.append(card);
    }
  }

  function applyPoolDemo() {
    const poolName = configured(cfg.poolName);
    if (poolName) {
      document.querySelectorAll('[data-pool-name]').forEach((node) => { node.textContent = poolName; });
    }
    const rates = cfg.poolDemoRatesPaise || {};
    const privateRate = document.querySelector('[data-pool-private-rate]');
    const commonRate = document.querySelector('[data-pool-common-rate]');
    if (privateRate) privateRate.textContent = formatPrice(rates.private) + '/hour';
    if (commonRate) commonRate.textContent = formatPrice(rates.common) + '/hour';
  }

  function apply() {
    const name = configured(cfg.name) || 'Need For Strength';
    const city = configured(cfg.city);

    replaceText(document.body, 'NEED FOR STRENGTH', name.toUpperCase());
    replaceText(document.body, 'Need For Strength', name);
    replaceAttributes('Need For Strength', name);
    if (city) {
      replaceText(document.body, 'Your City', city);
      replaceText(document.body, 'Location to be configured', city);
      replaceAttributes('Your City', city);
    }

    document.title = document.title.replaceAll('Need For Strength', name);

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

    const openingAnnouncement = configured(cfg.openingAnnouncement);
    if (openingAnnouncement) {
      document.querySelectorAll('[data-gym-opening-announcement]').forEach((node) => { node.textContent = openingAnnouncement; });
    }
    const foundingOfferText = configured(cfg.foundingOfferText);
    if (foundingOfferText) {
      document.querySelectorAll('[data-gym-founding-offer]').forEach((node) => { node.textContent = foundingOfferText; });
    }

    const mapUrl = configured(cfg.mapUrl);
    if (mapUrl) {
      setLink('[data-gym-map-link]', mapUrl, 'Open in Google Maps');
    }

    const embed = configured(cfg.mapEmbedUrl);
    if (embed) {
      document.querySelectorAll('[data-gym-map-frame]').forEach((frame) => { frame.src = embed; });
    }

    renderMembershipOffers();
    renderPersonalTraining();
    applyPoolDemo();

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