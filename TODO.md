# Need For Strength — TODO / Commercial Website Redesign

Last updated: 2026-09-26

## Goal

Turn the current customer website into a classy, premium, modern fitness-club website without breaking any existing functionality.

The redesign is a presentation-layer project first. Existing routes, APIs, IDs, data attributes, forms, business rules, authentication, pool operations, kitchen operations, BCA content, membership flows, BMI, diet planner, exercise library, admin links and member login must continue to work.

## Current issues observed

### 1. Website does not look premium

Symptoms:
- Visual hierarchy is weak.
- Sections feel disconnected.
- Too much empty beige/cream space in some areas.
- Dark and light sections do not feel like one design system.
- Cards, buttons and forms look generic.
- Typography feels inconsistent and does not create a strong fitness/luxury brand.
- Some sections feel like demo components instead of a finished commercial website.

Resolution:
- Create one premium design system for the entire public website.
- Use a consistent palette: deep charcoal/near-black, warm ivory, restrained bronze/gold accent and high-contrast text.
- Define consistent spacing, section widths, card radii, borders, shadows and button states.
- Use a tighter desktop grid and deliberate mobile spacing.
- Use one display typeface + one highly readable body typeface.
- Add subtle hover/scroll interactions only where they improve polish; avoid gimmicky animation.

### 2. Current AI images look blurred / low quality

Symptoms:
- Hero, BCA, kitchen and pool images appear soft or blurry on desktop.
- Current generated assets are too small/compressed for full-width presentation.
- Image treatment is inconsistent between sections.

Resolution:
- Replace current visual assets with high-resolution originals, ideally 1920x1080 or larger for wide sections.
- Generate separate compositions for hero, BCA, pool and kitchen instead of stretching one asset.
- Export optimized WebP/AVIF without aggressive compression.
- Add responsive `srcset` / `sizes` so desktop receives a sharp image while mobile receives a lighter version.
- Preserve aspect ratios and use `object-fit: cover` only where cropping is intentional.
- Verify at 100%, 125% and 150% browser scaling on desktop plus common mobile sizes.
- Do not re-use Gravity Fitness photographs.

### 3. Hero section needs a complete premium redesign

Resolution:
- Stronger Need For Strength branding and headline.
- High-quality full-width visual with intentional gradient overlay.
- Reduce clutter in the navigation.
- Primary CTA: membership/enquiry.
- Secondary CTA: member login or explore facilities.
- Keep existing functional links intact.
- Maintain accessible text contrast and mobile navigation.

### 4. Membership section looks sparse and unfinished

Resolution:
- Convert membership plans into premium cards with clear plan name, price, validity, highlights and CTA.
- Keep plan data sourced from the existing runtime/config/database path; do not hard-code production pricing.
- Keep owner-demo labels where demo pricing is being shown.
- Avoid huge blank areas when fewer cards are present.

### 5. BCA section needs stronger presentation

Current functionality:
- BCA feature is already customer-facing.

Resolution:
- Keep the BCA section prominent.
- Use a sharper professional body-composition-machine visual.
- Present supported metrics cleanly: weight, body fat %, muscle mass, visceral fat, body water %, BMI and metabolic age.
- Keep the existing safety note that BCA measurements are fitness-tracking estimates and not a medical diagnosis.
- Do not claim medical accuracy or diagnosis.

### 6. The Cue Master / pool section needs a premium club feel

Current functionality:
- Separate pool page exists.
- 3 tables are represented: 1 private + 2 common.
- Rates/status are read from the operations database.
- Reservation request opens WhatsApp and staff confirms final availability.

Resolution:
- Use a sharp high-resolution image where all 3 tables are visibly countable.
- Give private and common tables distinct premium cards.
- Show current rate/status clearly.
- Improve reservation form styling without changing field names/IDs or submission behavior.
- Keep the rule that a website request is NOT an automatically confirmed reservation.
- Never bypass backend conflict checks.

### 7. Kitchen menu page needs premium food presentation

Current functionality:
- Separate kitchen page exists.
- Customer menu loads available items from the live/read-only kitchen catalog.

Resolution:
- Use high-quality food photography/AI imagery.
- Group items by category with consistent cards.
- Make pricing easy to scan.
- Preserve live menu source; do not duplicate/hard-code menu data into HTML.
- Keep availability controlled by the operations system.

### 8. Forms look basic

Affected areas:
- Enquiry form.
- Pool reservation request.
- BMI and related interaction panels.

Resolution:
- Standardize labels, inputs, selects, focus states, validation states and buttons.
- Improve spacing and readable contrast.
- Keep all current input names, IDs, data attributes, validation rules and JS hooks.
- Do not change API payload contracts during visual redesign.

### 9. Footer and navigation need refinement

Resolution:
- Simplify primary navigation.
- Keep links to Membership, BCA, The Cue Master, Kitchen, Exercise Library, Contact and Member Login.
- Make legal links visible but unobtrusive.
- Improve footer grouping, spacing and branding.
- Keep Privacy and Terms pages available.

## Non-negotiable functionality safety rules

Do NOT break or remove:
- Member login.
- Admin portal.
- Existing API routes.
- Firebase/member authentication wiring.
- Membership plan/runtime configuration.
- BMI calculator.
- Indian diet planner.
- Exercise library.
- Contact/enquiry form.
- BCA information.
- Pool table live catalog.
- Pool reservation request flow.
- Kitchen live menu catalog.
- Privacy/Terms.
- Existing production-readiness and owner-demo safeguards.

During HTML changes preserve:
- Element IDs used by JavaScript.
- `data-*` attributes.
- Form field names.
- API endpoint paths.
- Script load order where required.
- Runtime config behavior.

## Required regression before deployment

1. Run customer homepage tests.
2. Run member-login tests.
3. Run diet-planner tests.
4. Run member-gateway tests.
5. Run full backend unit tests.
6. Run Chromium E2E suite.
7. Run JS syntax checks.
8. Run Python compile checks.
9. Run `git diff --check`.
10. Verify homepage, BCA, pool and kitchen on desktop + mobile.
11. Verify all four major image assets load without blur/stretching.
12. Verify pool and kitchen public APIs still return 200.
13. Verify admin portal remains unaffected.
14. Verify Universal Gym / LocalStoreTrack / other Redmi services remain untouched.

## Recommended implementation phases

### Phase A — Design system
- Typography
- Color tokens
- Layout widths
- Spacing scale
- Buttons
- Cards
- Forms
- Navigation/footer

### Phase B — Homepage
- Hero
- Membership
- BCA
- Cue Master
- Kitchen
- About
- BMI
- Diet
- Exercise
- Enquiry
- Contact

### Phase C — Dedicated pages
- Pool reservation page
- Kitchen menu page
- Member login visual refresh if needed
- Legal-page visual consistency

### Phase D — Images
- Regenerate high-resolution hero/BCA/pool/kitchen assets
- Add responsive sources
- Compress carefully
- Visual QA at desktop and mobile resolutions

### Phase E — Release
- Full regression
- Commit exact candidate
- Archive + SHA256
- Stage on Redmi
- Deploy only Need For Strength owner demo
- Public smoke test
- Confirm other Redmi applications remain healthy

## Production blockers still separate from visual redesign

The owner-demo is not the final commercial production environment. Production still requires:
- Final approved opening hours.
- Final membership/PT pricing.
- Final pool rates.
- Final kitchen menu/recipes/opening stock.
- Dedicated Need For Strength Firebase project.
- Stable production domains.
- Named/dedicated Cloudflare Tunnel.
- Dedicated off-device backup destination.
- Owner/legal review of Privacy and Terms.
- Final-domain E2E and backup/recovery acceptance.

Do not mark production ready by forcing confirmation flags. Each production gate must represent a real reviewed value.
