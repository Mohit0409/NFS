const fs = require('node:fs');
const test = require('node:test');
const assert = require('node:assert/strict');
const js = fs.readFileSync('web/js/member-account.js', 'utf8');
const html = fs.readFileSync('web/pages/member-login.html', 'utf8');
const gateway = fs.readFileSync('gateway/member_gateway.py', 'utf8');

test('member login does not force-refresh a fresh Firebase token', () => {
  assert.match(js, /user\.getIdToken\(\)/);
  assert.doesNotMatch(js, /getIdToken\(true\)/);
});

test('Firebase loading is deduplicated and runs with eligibility lookup', () => {
  assert.match(js, /firebaseLoadPromise/);
  assert.match(js, /Promise\.all\(\[checkMemberEligibility\(normalizedPhone\), loadFirebase\(\)\]\)/);
});
test('signed-out form is shown before Firebase session initialization completes', () => {
  const start = js.indexOf('async function initialize()');
  const show = js.indexOf('showSignedOut();', start);
  const load = js.indexOf('await loadFirebase();', start);
  assert.ok(start >= 0 && show > start && load > show);
});

test('Firebase auth connections and modules are warmed by the login page', () => {
  assert.match(html, /rel="modulepreload" href="https:\/\/www\.gstatic\.com\/firebasejs\/12\.18\.0\/firebase-app\.js"/);
  assert.match(html, /rel="modulepreload" href="https:\/\/www\.gstatic\.com\/firebasejs\/12\.18\.0\/firebase-auth\.js"/);
  assert.match(html, /preconnect" href="https:\/\/identitytoolkit\.googleapis\.com"/);
});

test('gateway reuses session user and performs logout cleanup asynchronously', () => {
  assert.match(gateway, /user = session_payload\.get\("user", \{\}\)/);
  assert.match(gateway, /def _logout_async/);
  assert.match(gateway, /threading\.Thread\(/);
});

test('member eligibility requires a currently active membership window', () => {
  assert.match(gateway, /m\.status IN \('active','scheduled'\)/);
  assert.match(gateway, /m\.starts_at <= \?/);
  assert.match(gateway, /m\.ends_at > \?/);
  assert.match(gateway, /_customer_is_login_eligible\(customer_id\)/);
});

test('post-OTP bootstrap rejects stale or missing current memberships', () => {
  assert.match(gateway, /_membership_summary_allows_access\(membership_summary\)/);
  assert.match(gateway, /starts_at <= now < ends_at/);
});

test('an open member session is revalidated when the current membership expires', () => {
  assert.match(js, /scheduleMembershipExpiryCheck\(current\.endsAt\)/);
  assert.match(js, /revalidateMembershipAtExpiry/);
  assert.match(js, /await bootstrapFirebaseUser\(user\)/);
  assert.match(js, /Your membership is no longer active/);
});

test('member login page cache-busts the expiry authorization fix', () => {
  assert.match(html, /member-account\.js\?v=20260831-expiry1/);
});
