# Validation: skincare revision

- Eight backend tests passed, including all 900 answer combinations, care-route suppression of product links, consent history, deduplication, export escaping, malformed requests, origin/host/CSRF guards, and rate limits.
- Desktop/mobile browser workflow passed: imagery, back navigation, consent default, failed-save retry, test capture, source attribution, dashboard filters, CSV download, and professional guidance without an email gate.
- Packaged Shopify JS/CSS passed an iPad WebKit harness: concern-based results, product-picker overrides, optional unchecked signup consent, no skin-answer storage, care-route signup suppression, hidden unavailable-product CTAs, CSS isolation, and theme-editor-style reinsertion.
- Shopify skill validator passed `sections/dermilogic-skin-quiz.liquid` and `templates/page.skin-quiz.json` in a minimal full-theme fixture with their real assets. This validates Liquid/schema, not a real store install.
- No Shopify account was accessed or changed. Native customer form submission, CAPTCHA, double opt-in, customer records, and outgoing email must be verified in the target unpublished theme.

Test scripts live in tests/. Browser screenshots are local test artifacts and are not part of the Shopify theme. The downloadable handoff contains source, generated theme files, and instructions; it excludes databases, credentials, Netlify linkage, and test captures.

Bundle revision: iPad WebKit tests cover automatic progression, Back and checked-answer reselection, dynamic bundle contents, item removal/subtotal changes, zero selection, unavailable products, duplicate variant IDs, locale-aware multi-item cart payloads, mocked 422 errors and successful cart navigation. Liquid section/schema validation passed. Native cart testing on the real unpublished theme remains required.
