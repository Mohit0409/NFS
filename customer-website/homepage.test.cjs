const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const root = __dirname;
const homepage = fs.readFileSync(path.join(root, 'web', 'index.html'), 'utf8');
const siteCss = fs.readFileSync(path.join(root, 'web', 'css', 'style.css'), 'utf8');
const memberCss = fs.readFileSync(path.join(root, 'web', 'css', 'member.css'), 'utf8');

test('membership is the second homepage section', () => {
  const hero = homepage.indexOf('id="home"');
  const membership = homepage.indexOf('id="membership"');
  const about = homepage.indexOf('id="about"');
  assert.ok(hero !== -1 && membership > hero && about > membership);
});

test('restored homepage tools and visit map are present', () => {
  assert.match(homepage, /id="bmi-form"/);
  assert.match(homepage, /id="bmi-weight"/);
  assert.match(homepage, /id="bmi-height"/);
  assert.match(homepage, /google\.com\/maps\?q=24\.476,74\.869/);
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

test('verified Gravity membership prices are shown', () => {
  assert.match(homepage, /1 Month[\s\S]*?1,200/);
  assert.match(homepage, /3 Months[\s\S]*?3,000/);
  assert.match(homepage, /1 Year[\s\S]*?10,000/);
  assert.doesNotMatch(homepage, />999<|>1,499<|>2,499</);
});

test('premium restyle preserves every homepage section and its order', () => {
  const expected = ['home', 'membership', 'about', 'bmi', 'nutrition', 'inside-gravity', 'enquiry', 'contact'];
  const actual = Array.from(homepage.matchAll(/<section[^>]+id="([^"]+)"/g), (match) => match[1]);
  assert.deepEqual(actual, expected);
});

test('hidden login states cannot be overridden by layout rules', () => {
  assert.match(siteCss, /\[hidden\]\s*\{\s*display:\s*none\s*!important;/);
  assert.match(memberCss, /\.member-account\[hidden\][\s\S]*?display:\s*none\s*!important;/);
});
