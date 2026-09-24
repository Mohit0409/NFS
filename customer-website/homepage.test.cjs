const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const root = __dirname;
const homepage = fs.readFileSync(path.join(root, 'web', 'index.html'), 'utf8');
const siteCss = fs.readFileSync(path.join(root, 'web', 'css', 'style.css'), 'utf8');
const memberCss = fs.readFileSync(path.join(root, 'web', 'css', 'member.css'), 'utf8');
const gymConfig = fs.readFileSync(path.join(root, 'web', 'js', 'gym-config.js'), 'utf8');
const runtimeConfig = fs.readFileSync(path.join(root, 'web', 'js', 'runtime-config.js'), 'utf8');

test('membership is the second homepage section', () => {
  const hero = homepage.indexOf('id="home"');
  const membership = homepage.indexOf('id="membership"');
  const about = homepage.indexOf('id="about"');
  assert.ok(hero !== -1 && membership > hero && about > membership);
});

test('homepage tools are present and map stays unconfigured until real gym data exists', () => {
  assert.match(homepage, /id="bmi-form"/);
  assert.match(homepage, /id="bmi-weight"/);
  assert.match(homepage, /id="bmi-height"/);
  assert.match(homepage, /data-gym-map-frame/);
  assert.match(homepage, /src="about:blank"/);
  assert.doesNotMatch(homepage, /24\.476,74\.869|Gravity Fitness/);
  assert.match(homepage, /js\/athlete-animation\.js/);
});

test('removed training and gallery routes stay removed', () => {
  assert.doesNotMatch(homepage, /Explore how you want to move\.|gallery\.html|trainers\.html|id="training"/);
  assert.equal(fs.existsSync(path.join(root, 'web', 'pages', 'gallery.html')), false);
  assert.equal(fs.existsSync(path.join(root, 'web', 'pages', 'trainers.html')), false);
});

test('membership stays enquiry-only and contains no payment CTA', () => {
  assert.match(homepage, /No online payment is collected/);
  assert.doesNotMatch(homepage, /Book\s*&\s*Pay|Pay Now|Razorpay|checkout/i);
  assert.doesNotMatch(homepage, /class="price-features"/);
  assert.equal((homepage.match(/class="button[^>]*price-card__cta"[^>]*data-enquiry=/g) || []).length, 4);
});

test('membership prices are configuration-driven and never inherit Gravity prices', () => {
  assert.match(homepage, /data-plan-key="oneMonth"[\s\S]*?data-plan-price>Ask/);
  assert.match(homepage, /data-plan-key="threeMonths"[\s\S]*?data-plan-price>Ask/);
  assert.match(homepage, /data-plan-key="oneYear"[\s\S]*?data-plan-price>Ask/);
  assert.match(gymConfig, /membershipPricesPaise/);
  assert.match(runtimeConfig, /formatPrice/);
  assert.doesNotMatch(homepage, /1,200|3,000|10,000/);
});

test('premium restyle preserves every homepage section and its order', () => {
  const expected = ['home', 'membership', 'about', 'bmi', 'nutrition', 'exercise-library', 'inside-gym', 'enquiry', 'contact'];
  const actual = Array.from(homepage.matchAll(/<section[^>]+id="([^"]+)"/g), (match) => match[1]);
  assert.deepEqual(actual, expected);
});

test('customer business details come from the New Gym runtime config', () => {
  assert.match(homepage, /js\/gym-config\.js/);
  assert.match(homepage, /js\/runtime-config\.js/);
  assert.match(gymConfig, /phoneDisplay: ''/);
  assert.match(gymConfig, /whatsappNumber: ''/);
  assert.match(gymConfig, /address: ''/);
  assert.match(gymConfig, /mapUrl: ''/);
  assert.doesNotMatch(gymConfig, /gravityfitnessnmh|917999526112|gravity-authe/);
});

test('hidden login states cannot be overridden by layout rules', () => {
  assert.match(siteCss, /\[hidden\]\s*\{\s*display:\s*none\s*!important;/);
  assert.match(memberCss, /\.member-account\[hidden\][\s\S]*?display:\s*none\s*!important;/);
});
