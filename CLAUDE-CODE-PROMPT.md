# Paste this into Claude Code

Install and adapt the Dermilogic concern-first skincare quiz from this package in an unpublished Shopify Online Store 2.0 theme.

Read HANDOFF.md before editing. Identify the exact Dermilogic store and unpublished theme ID from the project manager; do not infer credentials or reuse another client's account. If the manager has already provided those exact targets in the conversation, use them without asking again. Do not publish or push to a live theme.

Work in a complete local copy of the chosen unpublished theme. Preserve and back up existing files. Copy only the section, two assets, and optional JSON page template listed in HANDOFF.md. Never deploy the package directory as a whole Shopify theme, and never overwrite a pre-existing template without merging its content.

Configure the theme-editor product pickers to The Reset Cleanser, Pimple Rescue Patches, The Reset Towels, and No-Drip Wash Bands, verifying the current products and availability. Use actual store images. Review heading, question wording, product explanations, and consent copy with the manager. Keep the concern-first approach: practical routine guidance, no forced brush upsell, no diagnosis or cure claims, and professional guidance for painful breakouts, active irritation, or prescribed routines. Preserve the path that shows results without email.

For copy or logic changes, edit source files and regenerate with `python3 build_preview.py` and `python3 build_shopify.py`; do not patch generated assets alone. Keep optional newsletter signup disabled until ready to test. Use the native Shopify customer form, require explicit marketing consent, and never save skin answers to customer tags or send them to analytics. Do not promise a personalized results email unless a separate tested flow exists.

Run the included backend and browser tests, then Shopify Theme Check against the complete theme. Test the real unpublished preview on iPad and desktop, including back navigation, restart, all concern routes, absent/sold-out selected products, section reload in the theme editor, newsletter errors, and confirmation. Enable signup only with the manager's authorization and confirm the consenting test contact in Shopify Customers. Treat actual email delivery and double opt-in as account-dependent checks, not completed features.

Return the unpublished Shopify preview link, a concise list of changed files, test evidence, remaining account-dependent checks, and a rollback path. Wait for explicit approval identifying the live theme before publishing. Do not contact other people or launch ads, social posts, or email campaigns.

Preserve automatic progression, Back/reselection, and selectable dynamic bundles. Use current Liquid prices and available one-time variants. Test locale-aware multi-item cart submission with mocked errors first, then the authorized draft store. Never attach skin answers as cart attributes or invent bundle discounts. Run `python3 package_handoff.py` after rebuilding if a refreshed ZIP is needed.
