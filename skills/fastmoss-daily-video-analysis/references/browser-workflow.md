# Authenticated FastMoss Acquisition

## Purpose

Use this procedure to determine whether a logged-in FastMoss account supports direct data reads and to fall back without user clicks.

## Direct Read Test

1. Connect to the user-selected logged-in browser and confirm a FastMoss dashboard page is visible.
2. Open the relevant video-ranking surface through visible navigation. Prefer Hot Shoppable Videos or Video Discovery for apparel commerce research.
3. Set one target market and the previous market date. Record the visible filter labels and selected values.
4. Inspect only read-only network/resource evidence exposed by the documented browser surface. Do not inspect cookies, local storage, session storage, passwords, or browser profiles.
5. Accept an endpoint only when it is either documented by FastMoss in the account or already observed from the current page. Do not enumerate guessed paths.
6. Replay only the exact read request necessary for the filtered result. Do not invoke create, update, delete, monitor, save, subscribe, or purchase actions.
7. Reconcile the response total and at least three row values against the visible table. Check video URL/ID, creator, publish time, and one performance metric.
8. Test pagination once and verify that page 2 has new IDs without changing server state.
9. Record `backend_verified=true` only when reconciliation succeeds. Otherwise record the precise failure and move to official export.

## Official Export Test

1. Keep the same market, date, category, ranking period, and sort order used in the direct-read test.
2. Locate the visible official export control from a fresh DOM snapshot. Confirm it is unique before clicking.
3. Trigger the download. Existing user authorization covers the requested FastMoss data export, but do not accept unrelated browser permissions.
4. Find a newly created CSV or XLSX file whose modification time is after the run start.
5. Parse it without editing the original. Copy normalized data into the dated run folder.
6. Reconcile at least three exported rows and the total or page count against the UI.
7. Record entitlement limits, row caps, watermarks, missing fields, and any paid upgrade prompt.
8. Keep video metrics separate from product aggregates. Current video-product exports may expose video views and video sales alongside aggregate product sales, GMV, views, and likes.
9. Parse creator and product ID from canonical TikTok URLs when the export omits separate columns. If publish time is inferred from a TikTok video ID, store the inference basis and mark the row `limited_evidence`; do not present it as an official FastMoss timestamp.
10. Reject a strict SKU binding when one market product ID maps to multiple SKUs or when the latest market inventory is not positive.
11. When the report is for small-account replication, collect creator follower evidence before final selection. Prefer FastMoss creator detail/export. If unavailable, use exact-handle public profile evidence only for the creator-size gate, record the fallback source and as-of date, and do not describe it as FastMoss backend evidence.

## Page Extraction Test

Use this only when direct read and official export are unavailable.

1. Identify the exact result-table container from a fresh DOM snapshot.
2. Extract a bounded page in one read, not by looping over individual cells.
3. Advance with a verified unique pagination control and take a fresh snapshot.
4. Deduplicate by FastMoss video ID, TikTok video ID, or canonical video URL.
5. Stop and record `page_structure_unverified` when headers and rows cannot be mapped reliably.

## Minimum Module Checks

Test and log whether the account can access:

- Hot Shoppable Videos or the closest video leaderboard;
- Video Discovery;
- video detail;
- linked product detail;
- creator detail;
- date, market, category, and sort filters;
- official export;
- transcript, AI script, or caption fields when visible.

Do not treat a module name on a public sitemap as authenticated access evidence.

## TikTok Limitation

If a TikTok source page cannot be read, do not block the whole run. Preserve FastMoss metrics, thumbnail, caption/title, product, creator, and transcript when available. Set `evidence_status=limited_evidence`, list missing observations, and reduce the replicability score.

## Failure Codes

Use stable codes in `failure-log.jsonl`:

- `browser_policy_unavailable`
- `login_expired`
- `captcha_required`
- `two_factor_required`
- `paid_entitlement_required`
- `backend_endpoint_unobserved`
- `backend_reconciliation_failed`
- `export_unavailable`
- `export_reconciliation_failed`
- `export_row_cap`
- `page_structure_unverified`
- `field_missing`
- `creator_size_unverified`
- `creator_size_over_limit`
- `creator_size_not_qualified`
- `tiktok_unreadable`
- `product_catalog_incomplete`
- `candidate_floor_not_met`

Each event must include timestamp, stage, severity, message, attempted tier, and selected fallback.
