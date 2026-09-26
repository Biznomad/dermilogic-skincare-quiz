# Dermilogic skincare quiz: project-manager handoff

## What you are installing

A Shopify Online Store 2.0 section that starts with skincare concerns. Five questions cover the main concern, skin feel, product sensitivity, current routine, and sunscreen use. Results explain a simple routine, the reason for a product suggestion, and where the catalog does not cover an essential step. No brush purchase is required or recommended by the routing.

Painful/persistent breakouts, current irritation, and prescribed routines route to professional guidance without a shopping CTA or email gate. This is educational guidance, not diagnosis, treatment, or a validated clinical assessment. Do not add cure claims or promise results.

## Files to copy into the theme

| Package file | Theme destination |
| --- | --- |
| `shopify/sections/dermilogic-skin-quiz.liquid` | `sections/dermilogic-skin-quiz.liquid` |
| `shopify/assets/dermilogic-skin-quiz.js` | `assets/dermilogic-skin-quiz.js` |
| `shopify/assets/dermilogic-skin-quiz.css` | `assets/dermilogic-skin-quiz.css` |
| `shopify/templates/page.skin-quiz.json` | `templates/page.skin-quiz.json`, only if that template does not already exist |

This is a section package, not an entire Shopify theme. Never push this directory as a replacement theme. Keep all existing theme files, settings, app embeds, tracking, and templates. Do not copy the Python server, preview API shim, preview dashboard, or SQLite database into Shopify.

## Install with Claude Code

1. Give Claude Code this folder and `CLAUDE-CODE-PROMPT.md`. Confirm the exact Dermilogic `.myshopify.com` store and an **unpublished** duplicate theme ID. Production store access is not included in this package.
2. Pull or use a complete local copy of that unpublished theme. Back it up or commit its current state. Copy only the four files listed above; merge an existing matching template rather than replacing it. Run Theme Check on the complete theme.
3. Use the theme editor to add **Dermilogic skincare quiz** to a page template, or use the provided `page.skin-quiz` template. Set the heading, introduction, CTA, lifestyle image, cleanser product, patch product, and corresponding explanations. Product pickers must select actual available store products; absent/unavailable selections hide purchase links.
4. Test the unpublished-theme preview on iPad and desktop. Verify all five questions, Back, Restart, sensitive-skin routing, missing/sold-out products, and professional-guidance paths. Keep email signup off until its copy and store behavior are confirmed.
5. When authorized, enable the native newsletter form and verify one consenting test signup in Shopify Customers, including the store's double-opt-in behavior if configured. Confirm an actual welcome email flow separately. Get explicit approval for the exact live theme before publication.

### Optional CLI path, after confirming the store and theme

Use `shopify theme list --store <confirmed-store>.myshopify.com` to identify the draft. Use `shopify theme pull --store <confirmed-store>.myshopify.com --theme <confirmed-unpublished-id> --path <complete-theme-directory>` to prepare a full theme checkout. After merging the package, run `shopify theme check --path <complete-theme-directory>`.

For upload, use `shopify theme push --store <confirmed-store>.myshopify.com --theme <confirmed-unpublished-id> --path <complete-theme-directory> --only sections/dermilogic-skin-quiz.liquid --only assets/dermilogic-skin-quiz.js --only assets/dermilogic-skin-quiz.css --only templates/page.skin-quiz.json`. Verify the CLI's current options with `--help` first. Do not use `--live`, `--allow-live`, or a guessed theme ID. Do not publish as part of installation.

## What the project manager can change

Theme editor settings control the heading, introduction, button label, hero image, product selections, product explanations, signup toggle, signup heading, and consent copy. Questions and options live in `public/app.js`. Educational rules and result copy live in `skincare.py`. Layout styles live in `public/style.css`. Shopify form markup/settings live in `shopify-section-wrapper.liquid`.

After changes, run `python3 build_preview.py` then `python3 build_shopify.py`. Generated Shopify JS/CSS/Liquid are overwritten by the build; change the source files instead. The generated decision table comes directly from the same Python rules used by the local prototype, so the two versions cannot silently diverge through duplicate handwritten logic.

The renderer uses Shadow DOM to isolate quiz CSS and IDs from the merchant's theme. The native Shopify customer form stays in light DOM, displayed through a slot, for normal Shopify form processing. Custom-element initialization handles dynamically inserted sections and guards against double initialization. Global theme styling still applies to the native signup form.

## Signup and data behavior

Shopify results are shown before signup. The newsletter form is disabled by default, uses Shopify's native `customer` form, requires an unchecked marketing checkbox, and submits only email, explicit consent, and the neutral tags `newsletter,dermilogic-skin-quiz`. Skin concerns, skin type, treatment choices, and quiz answers are not submitted, persisted in browser storage, or added to customer tags by this package.

This package does not create a personalized routine email or a Klaviyo flow. It does not guarantee that native signup sends an email: confirmation and delivery depend on the store's configured email settings. Do not replace the native form with a custom fetch to a private API or put API keys in a theme asset. If segmentation based on skin-related answers is later wanted, design consent, retention, and provider handling separately before storing that data.

The Netlify review link is different: it simulates saves using browser-only test storage and has a test dashboard. Never treat those records as real subscribers or install that simulator into Shopify. Existing version-one preview entries remain in their old browser storage key and are not merged into this skin-concern preview.

## Product mapping and review

Occasional spots + comfortable skin + no active-treatment routine can suggest Pimple Rescue Patches as an optional surface cover. Other non-escalation routes can suggest The Reset Cleanser for cleansing. Neither product is presented as a treatment for deep acne, pigmentation, or a diagnosed condition. Moisturizer and sunscreen remain essential categories even though suitable Dermilogic items have not been verified. If you select different products in the theme editor, verify the ingredients and rewrite the explanation to match the actual product; the default description assumes the verified Dermilogic product.

Review clinical-adjacent copy with the brand's qualified reviewer before launch. No clinical endorsement of the quiz or products is implied by the educational references.

Sources checked September 25, 2026:

- AAD routine basics: https://www.aad.org/public/everyday-care/skin-care-basics/care/skin-care-budget
- AAD blemish-prone skin guidance: https://www.aad.org/public/diseases/acne/skin-care/tips
- AAD moisturizer guidance: https://www.aad.org/public/everyday-care/skin-care-basics/dry/pick-moisturizer
- AAD sunscreen guidance: https://www.aad.org/media/stats-sunscreen
- Store catalog: https://dermilogic.com/products/the-reset-cleanser and https://dermilogic.com/products/pimple-rescue-patch

## Release limits and rollback

The package can be validated locally, but actual Shopify theme rendering, native signup, CAPTCHA, double opt-in, app compatibility, and customer records require testing against the confirmed unpublished theme. No Shopify store or live theme was modified during this build.

Rollback on a draft: remove the section from the template in the theme editor, or restore the backed-up files. Leave unrelated theme changes intact. Any live-theme rollback also requires the approved target and release process.
