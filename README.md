# Dermilogic concern-first skincare quiz

[Open the preview](https://dermilogic-shopper-preview.netlify.app/) · [Download the Shopify handoff](https://dermilogic-shopper-preview.netlify.app/dermilogic-shopify-handoff.zip)

Start with **HANDOFF.md** for installation, editing, data behavior, and release limits. Give the project manager **CLAUDE-CODE-PROMPT.md** to run the install with Claude Code.

## What changed

The five-question quiz covers skin concerns, skin feel, sensitivity, the current routine, and sunscreen habits. Results lead with practical skincare guidance and explain the product suggestion. Professional-guidance paths do not show product sales or an email gate. No routine recommends a brush by default. Answers auto-advance, and results include an editable product selection with prices, a subtotal, and a cart action.

## Three environments

- **Shopify package:** `shopify/` contains a Liquid section, isolated JS/CSS, and optional page template. Native customer signup is independently optional, disabled by default, and does not submit or store skin answers. Requires installation and account-specific QA in a confirmed unpublished theme.
- **Hosted review:** Netlify browser-only demo. Test email captures and answers remain in that browser, in version-two storage. No emails are sent, no shared database is populated, and test records must not be treated as subscribers.
- **Local prototype:** `python3 server.py` serves http://127.0.0.1:8891 with SQLite test captures and a local dashboard. It is not suitable for public hosting. Source and database routes are not exposed; local CSRF protection is not public admin authentication.

## Edit and build

Questions: `public/app.js`. Rules and result copy: `skincare.py`. Styling: `public/style.css`. Shopify settings/form wrapper: `shopify-section-wrapper.liquid`.

```sh
python3 build_preview.py
python3 build_shopify.py
python3 package_handoff.py
python3 -m unittest discover -s tests -q
python3 tests/browser_smoke.py
python3 tests/shopify_smoke.py
```

Browser tests require Python Playwright with Chromium and WebKit. They use isolated fixture data. Python build/runtime uses the standard library only. `generated-matches.js` is generated from Python rules and interned to minimize repeated text. Shopify assets use the same rules, not separately handwritten routing.

## Hosting

Authorized BizNomad preview site ID: `077d38fb-1c8f-440f-bc15-458c3d01c4da`. Deploy **only** `preview-dist`, with the explicit site ID. Never deploy the project directory, database, or local server. The existing Dermilogic advisory site is separate and must not be overwritten.

## Current validation

See VALIDATION.md. Shopify Liquid validation and packaged iPad browser tests are complete. Actual Shopify store installation, native signup delivery, double opt-in, and theme/app integration remain manager-side checks. No Shopify store/theme was changed.
