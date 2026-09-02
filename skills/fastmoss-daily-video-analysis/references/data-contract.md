# Data and Scoring Contract

## Structured Product Catalog

Prefer one XLSX workbook with exactly these machine-readable tables:

### `商品主表`

Use one row per `store_id + market + sku` when store IDs are available, or one isolated workbook/table per store when they are not. Required fields are `market`, `sku`, `catalog_segment`, `category`, `fabric`, `selling_points`, `normal_price`, `promo_price`, `currency`, `catalog_status`, and source provenance. `market` must be `US` or `DE`; blank or shared market rows are not eligible for production matching.

### `标识别名表`

Use one row per `store_id + market + sku` when possible. Store `old_skus`, `tiktok_product_ids`, `primary_tiktok_product_id`, `amazon_asins`, `preferred_asin`, conflict counts, and source provenance. Multi-value identifiers use semicolon separators. Resolve identifiers only inside the requested market and store pool.

### `市场库存表`

Use one row per `store_id + market + sku + source_sku + snapshot_date` when store IDs are available. Preserve `on_hand_stock`, `available_stock`, `in_transit_stock`, seven-day sales, color/SKU availability, alias match basis, and source file. For matching, select the latest snapshot per store, market, and SKU; aggregate its source-SKU rows; and require `available_stock > 0` by default.

Use `sku` as the master identifier. Old SKU, TikTok product ID, and ASIN are aliases, never replacement primary keys. Keep stores, US records, and DE records separate through parsing, stock gating, matching, scoring, reporting, and failure logging.

## Candidate Fields

Required for a qualified candidate. `store_id` may come from the run configuration when the FastMoss export itself does not include a store column.

| Field | Meaning |
| --- | --- |
| `store_id` | User-provided store/shop identifier for per-store reports |
| `video_id` | FastMoss or TikTok stable video identifier |
| `video_url` | Canonical source URL |
| `creator_name` | Creator display name or ID |
| `creator_followers` | Creator follower count when exact-handle evidence is available |
| `creator_followers_as_of` | Date or timestamp for the follower-count evidence |
| `creator_profile_source` | FastMoss creator detail/export or exact-handle fallback source name |
| `creator_profile_source_url` | Evidence URL for the matched creator profile |
| `published_at` | Source timestamp with timezone when known |
| `market` | `US` or `DE` |
| `category` | Source category |
| `product_title` | Linked product title |
| `views` | Snapshot views |
| `likes` | Snapshot likes |
| `comments` | Snapshot comments |
| `shares` | Snapshot shares |
| `sales` | Video-attributed or linked sales when FastMoss exposes it |
| `gmv` | Video-attributed or linked GMV with source currency |
| `captured_at` | Collection timestamp |
| `source_tier` | `backend_verified`, `official_export`, or `page_extraction` |

Useful enrichment fields:

`caption`, `transcript`, `thumbnail_url`, `duration_sec`, `view_growth`, `sales_growth`, `hook`, `pain_point`, `proof_action`, `cta`, `content_angle`, `source_video_structure`, `source_voiceover_full`, `source_voiceover_zh`, `voiceover_source`, `risk_note`, `evidence_status`, `cover_copy`, and `hashtags`.

For official video-product exports, preserve product aggregates as `product_total_sales`, `product_total_gmv`, `product_total_views`, and `product_total_likes`. Do not alias these fields to video-level `sales`, `gmv`, `views`, or `likes`. Store non-official timestamp derivations in `published_at_basis` and set `evidence_status=limited_evidence`.

For user-facing Excel and HTML reports, keep operational evidence fields out of the visible table even when they are required internally. Hide TikTok product links, FastMoss product links, evidence/risk notes, creator-size status, creator follower evidence date, creator profile source/source URL, rejection reasons, and match-basis fields from presentation outputs. Preserve them in normalized CSV/JSON, failure logs, and `run-manifest.json` for auditability. Do not hide `source_video_structure`, `source_voiceover_full`, or `source_voiceover_zh`; these are user-facing shoot-planning fields.

When a visual report is requested, add `video_first_frame_path` or `video_cover_path` to the presentation dataset. Prefer TikTok oEmbed or FastMoss-visible video thumbnails; use product cover images only as a recorded fallback. Each visual card must also carry the matched similar SKU, actual source-video structure, complete source-video voiceover/transcript in the market language, and Chinese translation.

Core-field missingness is measured across `video_id or video_url`, `creator_name`, `published_at`, `market`, `product_title`, `views`, and at least one of `sales or gmv`.

## Creator Size Evidence

When the strategy targets small-account replication, final selection must reject performance driven by creators whose audience is too large to benchmark against the user's account. Use FastMoss creator detail or official export fields first. If FastMoss export lacks follower count, use an exact-handle public profile fallback only for this gate, never as proof of FastMoss backend access.

Required creator-size fields are `creator_name`, `creator_followers`, `creator_followers_as_of`, `creator_profile_source`, and `creator_profile_source_url`. The source URL handle must exactly match the candidate creator handle after lowercasing and removing a leading `@`. Missing followers, missing as-of date, missing source, source-handle mismatch, or `creator_followers > max_creator_followers` makes the row ineligible for final selection.

## Product Fields

Every final row needs `sku`, `title`, `market`, and enough product evidence to justify a similar, shootable match for the source viral video. Prefer these fields:

`category`, `product_type`, `pain_points`, `selling_points`, `proof_actions`, `fit`, `colors`, `neckline`, `sleeve`, `fabric`, `scenarios`, `price`, `stock`, `margin`, `prohibited_claims`, and `image_paths`.

Unknown stock, margin, price, or prohibited wording lowers commercial readiness. Never fabricate these values from a product image. A product cannot be selected merely because it is in the same broad category; it must be similar enough in style, occasion, buyer problem, and proof-action capability to reproduce the viral video's core selling idea.

## Number Parsing

Normalize commas, currency symbols, percentages, `K/M/B`, and Chinese `万/亿`. Preserve raw values in the source artifact. Treat blank, dash, `N/A`, and hidden entitlement values as missing rather than zero.

## Hot Score

Calculate percentile ranks inside the same store, market, date, surface, and category cohort. Renormalize weights over available metrics:

| Signal | Weight |
| --- | ---: |
| sales | 40 |
| GMV | 30 |
| views | 10 |
| engagement rate | 5 |
| view or sales growth | 10 |
| recency to analysis date | 5 |

Use `(likes + comments + shares) / views` only when FastMoss does not provide a reliable engagement rate. Lifetime performance without previous-day growth is weaker evidence and must be labeled.

## Product Match Score

Score the buying reason rather than only garment-name similarity:

| Signal | Weight |
| --- | ---: |
| product type and category | 25 |
| buyer pain overlap | 25 |
| proof-action compatibility | 15 |
| garment attributes | 15 |
| market and scenario | 10 |
| price position | 5 |
| stock and margin readiness | 5 |

Reject a match when prohibited wording conflicts with the source concept or when the needed visible proof cannot be demonstrated by the SKU.

Also reject a match when the SKU is only a broad category neighbor and cannot plausibly reproduce the source video's visible style, wearing occasion, buyer pain, or proof action.

## Final Score

Use this deterministic pre-ranking before semantic review:

`final = 0.55 * hot + 0.30 * product_match + 0.10 * replicability + 0.05 * evidence_confidence`

Replicability considers usable hook/proof/CTA evidence, practical duration and setting, and whether the idea depends on a specific creator identity, copyrighted asset, or unverifiable claim. Semantic review may reduce a score but must record the reason.

## Selection Constraints

- Require one concrete, similar, currently eligible SKU for every final source video selection.
- For each store, select seven highest-sales qualified videos, ranked by `sales` descending and then GMV.
- For each store, select seven small-account highest-sales videos after requiring exact-handle creator-size evidence and `creator_followers < 50000`.
- Require `source_video_structure`, `source_voiceover_full`, and `source_voiceover_zh` for every final production recommendation. If the complete voiceover/transcript cannot be obtained, reject the row unless the report explicitly documents a shortage.
- Keep overlap between a store's two seven-video groups to at most one source video.
- Keep pairwise overlap between any two stores to at most 20 percent of selected source videos.
- Prefer no more than two rows per SKU and two per creator.
- Cover at least four content angles when available.
- Do not select duplicate source IDs or URLs.
- Keep excluded high scorers in a watchlist with the exclusion reason.
