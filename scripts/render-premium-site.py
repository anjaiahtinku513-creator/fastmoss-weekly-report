from __future__ import annotations

import csv
import html
import json
from collections import Counter, OrderedDict
from pathlib import Path


SITE_ROOT = Path(__file__).resolve().parents[1]
REPORT_DATE = "2026-08-31"
REPORT_DIR = SITE_ROOT / "reports" / REPORT_DATE
CSV_PATH = REPORT_DIR / "data.csv"
MANIFEST_PATH = REPORT_DIR / "visual-report-manifest.json"
REPORT_HTML_PATH = REPORT_DIR / "index.html"
HOME_HTML_PATH = SITE_ROOT / "index.html"


def read_rows() -> list[dict[str, str]]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_manifest() -> dict:
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def compact_number(value: object) -> str:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "0"
    abs_n = abs(n)
    if abs_n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if abs_n >= 1_000:
        return f"{n / 1_000:.1f}K".replace(".0K", "K")
    if n.is_integer():
        return str(int(n))
    return f"{n:.1f}"


def money(value: object) -> str:
    label = compact_number(value)
    return f"${label}" if label != "0" else "$0"


def ordered_stores(rows: list[dict[str, str]]) -> OrderedDict[str, str]:
    stores: OrderedDict[str, str] = OrderedDict()
    for row in rows:
        stores.setdefault(row.get("store_id", ""), row.get("shop_name", ""))
    return stores


def safe_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def clean_display_text(value: object) -> str:
    text = "" if value is None else str(value)
    replacements = {
        "已移除旧版通用15秒结构，不能用模板冒充原视频结构。": "不会使用通用模板冒充原视频结构。",
        "旧版通用15秒结构": "旧版通用结构",
        "通用15秒结构": "通用结构",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def display_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{key: clean_display_text(value) for key, value in row.items()} for row in rows]


def build_report_html(rows: list[dict[str, str]], manifest: dict) -> str:
    rows = display_rows(rows)
    stores = ordered_stores(rows)
    store_filters = "\n".join(
        f'<button type="button" data-store-filter="{esc(store_id)}">{esc(shop_name)}</button>'
        for store_id, shop_name in stores.items()
    )
    store_links = "\n".join(
        f'<a href="#store-{esc(store_id)}">{esc(shop_name)}</a>'
        for store_id, shop_name in stores.items()
    )
    group_counts = Counter(row.get("group", "") for row in rows)
    sku_count = len({(row.get("store_id", ""), row.get("matched_similar_sku", "")) for row in rows if row.get("matched_similar_sku")})
    top_sales = sum(float(row.get("video_sales") or 0) for row in rows)
    top_gmv = sum(float(row.get("product_total_gmv") or 0) for row in rows)
    first_frame = rows[0].get("first_frame_path", "") if rows else ""
    data_json = safe_json(rows)

    css = r"""
:root {
  --page: #f3f0e9;
  --paper: #fffdf8;
  --ink: #171717;
  --muted: #6b6760;
  --faint: #e8e1d5;
  --line: #d8d0c2;
  --hot: #f72566;
  --hot-dark: #b61243;
  --teal: #087f75;
  --amber: #b4642d;
  --green: #0c7a53;
  --shadow: 0 24px 70px rgba(42, 34, 24, .11);
  --shadow-soft: 0 10px 30px rgba(42, 34, 24, .08);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background:
    linear-gradient(90deg, rgba(23, 23, 23, .035) 1px, transparent 1px) 0 0 / 84px 84px,
    linear-gradient(180deg, #fffaf3 0%, var(--page) 48%, #ebe6dc 100%);
  color: var(--ink);
  font-family: "Microsoft YaHei", "PingFang SC", Inter, Arial, sans-serif;
  line-height: 1.52;
  letter-spacing: 0;
}
a { color: inherit; }
button, input, select { font: inherit; }
button { cursor: pointer; }
.page-transition {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: var(--ink);
  transform: translateY(0);
  transition: transform 760ms cubic-bezier(.76, 0, .24, 1);
  pointer-events: none;
}
body.is-loaded .page-transition { transform: translateY(-102%); }
.shell { max-width: 1460px; margin: 0 auto; padding: 22px; }
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  min-height: 64px;
  margin: -22px -22px 22px;
  padding: 0 22px;
  background: rgba(255, 253, 248, .84);
  border-bottom: 1px solid rgba(216, 208, 194, .76);
  backdrop-filter: blur(18px);
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  font-weight: 800;
}
.brand-mark {
  width: 12px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(180deg, var(--hot), var(--amber));
  box-shadow: 0 0 0 6px rgba(247, 37, 102, .08);
}
.top-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 8px 13px;
  border-radius: 6px;
  border: 1px solid var(--ink);
  background: var(--ink);
  color: #fff;
  text-decoration: none;
  font-weight: 760;
  transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease;
}
.button:hover { transform: translateY(-1px); box-shadow: var(--shadow-soft); }
.button.ghost {
  color: var(--ink);
  background: rgba(255, 253, 248, .72);
  border-color: var(--line);
}
.hero {
  display: grid;
  grid-template-columns: minmax(0, .98fr) minmax(300px, .52fr);
  gap: 22px;
  align-items: stretch;
  min-height: auto;
}
.hero-copy,
.hero-media,
.command-bar,
.store-section,
.audit-strip {
  border: 1px solid var(--line);
  background: rgba(255, 253, 248, .86);
  box-shadow: var(--shadow);
  border-radius: 8px;
}
.hero-copy {
  position: relative;
  overflow: hidden;
  padding: 24px;
  min-height: 334px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.hero-copy::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(115deg, rgba(247, 37, 102, .09), transparent 34%),
    linear-gradient(150deg, transparent 55%, rgba(8, 127, 117, .1));
  opacity: .88;
  pointer-events: none;
}
.hero-inner { position: relative; z-index: 1; }
.eyebrow {
  margin: 0 0 13px;
  color: var(--hot-dark);
  font-size: 12px;
  font-weight: 780;
}
h1 {
  max-width: 820px;
  margin: 0;
  font-size: 34px;
  line-height: 1.08;
  letter-spacing: 0;
}
.lead {
  max-width: 790px;
  margin: 14px 0 0;
  color: var(--muted);
  font-size: 15px;
}
.hero-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }
.stats {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  margin-top: 18px;
  background: var(--line);
  border: 1px solid var(--line);
}
.stat {
  min-height: 70px;
  padding: 10px;
  background: rgba(255, 253, 248, .92);
}
.stat b { display: block; font-size: 21px; line-height: 1; }
.stat span { display: block; margin-top: 8px; color: var(--muted); font-size: 12px; }
.hero-media {
  position: relative;
  overflow: hidden;
  min-height: 334px;
  max-height: 430px;
  background: #111;
}
.hero-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  filter: saturate(.96) contrast(1.04);
  transform: scale(1.03);
  transition: transform 1100ms cubic-bezier(.2, .8, .2, 1);
}
body.is-loaded .hero-media img { transform: scale(1); }
.media-caption {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 22px;
  color: #fff;
  background: linear-gradient(180deg, transparent, rgba(0, 0, 0, .76));
}
.media-caption b { display: block; font-size: 20px; }
.media-caption span { display: block; max-width: 520px; color: rgba(255,255,255,.78); font-size: 13px; }
.hero-media::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 30%, rgba(255,255,255,.22) 46%, transparent 62%);
  transform: translateX(-120%);
}
body.is-loaded .hero-media::after { animation: image-sweep 1100ms 430ms cubic-bezier(.2,.8,.2,1) both; }
.audit-strip {
  margin: 16px 0;
  padding: 16px 18px;
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 18px;
  color: var(--muted);
}
.audit-strip b { color: var(--ink); }
.store-jump {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}
.store-jump a {
  padding: 7px 10px;
  border: 1px solid var(--line);
  border-radius: 999px;
  text-decoration: none;
  color: var(--muted);
  background: rgba(255,253,248,.74);
  font-size: 12px;
}
.command-bar {
  position: sticky;
  top: 75px;
  z-index: 15;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, .72fr) auto;
  gap: 14px;
  align-items: center;
  margin-bottom: 22px;
  padding: 12px;
  backdrop-filter: blur(16px);
}
.filter-set { display: flex; align-items: center; gap: 9px; min-width: 0; }
.filter-label {
  flex: 0 0 auto;
  color: var(--muted);
  font-size: 12px;
  font-weight: 780;
}
.filter-buttons { display: flex; gap: 7px; flex-wrap: wrap; min-width: 0; }
.filter-buttons button {
  min-height: 34px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: rgba(255,253,248,.76);
  color: var(--muted);
  transition: color 160ms ease, background 160ms ease, transform 160ms ease;
}
.filter-buttons button:hover { transform: translateY(-1px); }
.filter-buttons button.is-active {
  color: #fff;
  background: var(--ink);
  border-color: var(--ink);
}
.result-count {
  white-space: nowrap;
  border-left: 1px solid var(--line);
  padding-left: 14px;
  color: var(--muted);
  font-size: 13px;
}
.result-count b { color: var(--ink); font-size: 20px; }
.store-section {
  margin: 22px 0;
  padding: 18px;
  overflow: hidden;
}
.store-head {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-end;
  border-bottom: 1px solid var(--line);
  padding-bottom: 14px;
  margin-bottom: 16px;
}
.store-head h2 { margin: 0; font-size: 25px; letter-spacing: 0; }
.store-metrics {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}
.metric-pill {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 6px 9px;
  color: var(--muted);
  font-size: 12px;
  background: rgba(255,253,248,.7);
}
.metric-pill b { color: var(--ink); }
.group-band { margin-top: 18px; }
.group-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.group-head h3 { margin: 0; font-size: 16px; }
.group-head span { color: var(--muted); font-size: 12px; }
.cards-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.video-card {
  display: grid;
  grid-template-columns: 176px minmax(0, 1fr);
  min-height: 366px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  overflow: hidden;
  box-shadow: 0 1px 0 rgba(255,255,255,.85) inset;
  transition:
    opacity 260ms ease,
    transform 260ms ease,
    border-color 260ms ease,
    box-shadow 260ms ease;
}
.video-card:hover {
  transform: translateY(-3px);
  border-color: rgba(247, 37, 102, .36);
  box-shadow: 0 18px 42px rgba(42, 34, 24, .14);
}
.video-card.is-filtered {
  opacity: 0;
  transform: translateY(10px) scale(.985);
}
.media-button {
  position: relative;
  display: block;
  width: 100%;
  min-height: 366px;
  padding: 0;
  border: 0;
  background: #111;
  overflow: hidden;
}
.media-button img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 620ms cubic-bezier(.2,.8,.2,1), filter 260ms ease;
}
.video-card:hover .media-button img { transform: scale(1.045); filter: saturate(1.04); }
.rank-badge {
  position: absolute;
  left: 10px;
  top: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  height: 30px;
  border-radius: 999px;
  background: rgba(23, 23, 23, .9);
  color: #fff;
  font-weight: 820;
  font-size: 13px;
}
.group-badge {
  position: absolute;
  left: 10px;
  bottom: 10px;
  max-width: calc(100% - 20px);
  padding: 6px 8px;
  border-radius: 6px;
  background: rgba(255, 253, 248, .88);
  color: var(--ink);
  font-size: 12px;
  font-weight: 760;
}
.card-body {
  min-width: 0;
  padding: 14px;
  display: flex;
  flex-direction: column;
}
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 4px 8px;
  border-radius: 999px;
  background: #f3f0e9;
  color: var(--muted);
  font-size: 11px;
  font-weight: 720;
}
.chip.hot { background: #fff0f4; color: var(--hot-dark); }
.chip.small { background: #e9f7f4; color: var(--teal); }
.chip.stock { background: #fff6ec; color: #8a491d; }
.video-title {
  margin: 0;
  font-size: 16px;
  line-height: 1.34;
  letter-spacing: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.caption {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 36px;
}
.key-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 13px 0;
}
.key-metric {
  border-top: 1px solid var(--line);
  padding-top: 8px;
}
.key-metric span { display: block; color: var(--muted); font-size: 11px; }
.key-metric b { display: block; margin-top: 2px; font-size: 15px; }
.sku-line {
  border-top: 1px solid var(--line);
  padding-top: 10px;
  margin-top: 2px;
}
.sku-line strong {
  display: block;
  font-size: 14px;
}
.sku-line span {
  display: block;
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.replicate {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  border-top: 1px solid var(--line);
  padding-top: 10px;
  margin-top: 10px;
}
.replicate b {
  display: block;
  margin-bottom: 3px;
  font-size: 12px;
}
.replicate p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: 12px;
}
.card-actions a,
.card-actions button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  min-height: 34px;
  padding: 7px 10px;
  border-radius: 6px;
  border: 1px solid var(--ink);
  background: var(--ink);
  color: #fff;
  text-decoration: none;
  font-size: 12px;
  font-weight: 760;
}
.card-actions button.secondary {
  background: transparent;
  color: var(--ink);
  border-color: var(--line);
}
.reveal {
  opacity: 0;
  transform: translateY(22px);
  transition: opacity 680ms ease, transform 680ms cubic-bezier(.2,.8,.2,1);
}
.reveal.is-visible { opacity: 1; transform: translateY(0); }
.detail-shell {
  position: fixed;
  inset: 0;
  z-index: 60;
  pointer-events: none;
}
.detail-shell.is-open { pointer-events: auto; }
.detail-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(23, 23, 23, .42);
  opacity: 0;
  transition: opacity 240ms ease;
}
.detail-shell.is-open .detail-backdrop { opacity: 1; }
.detail-panel {
  position: absolute;
  top: 16px;
  right: 16px;
  bottom: 16px;
  width: min(760px, calc(100vw - 32px));
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  box-shadow: 0 30px 100px rgba(0,0,0,.26);
  transform: translateX(28px) scale(.985);
  opacity: 0;
  transition: transform 340ms cubic-bezier(.2,.8,.2,1), opacity 240ms ease;
  overflow: hidden;
  display: grid;
  grid-template-rows: auto 1fr;
}
.detail-shell.is-open .detail-panel {
  transform: translateX(0) scale(1);
  opacity: 1;
}
.detail-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 16px;
  border-bottom: 1px solid var(--line);
}
.detail-top b { font-size: 17px; }
.detail-close {
  width: 38px;
  height: 38px;
  border-radius: 6px;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--ink);
  font-size: 22px;
  line-height: 1;
}
.detail-content {
  overflow: auto;
  padding: 16px;
}
.detail-hero {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}
.detail-hero img {
  width: 100%;
  aspect-ratio: 9 / 16;
  object-fit: cover;
  border-radius: 8px;
  background: #111;
}
.detail-hero h3 { margin: 0; font-size: 22px; line-height: 1.25; }
.detail-hero p { margin: 8px 0 0; color: var(--muted); }
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 16px;
}
.detail-block {
  border-top: 1px solid var(--line);
  padding-top: 12px;
}
.detail-block.wide { grid-column: 1 / -1; }
.detail-block h4 { margin: 0 0 6px; font-size: 13px; }
.detail-block p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  white-space: pre-wrap;
}
.toast {
  position: fixed;
  left: 50%;
  bottom: 22px;
  z-index: 90;
  transform: translate(-50%, 20px);
  opacity: 0;
  pointer-events: none;
  border-radius: 999px;
  background: var(--ink);
  color: #fff;
  padding: 9px 13px;
  font-size: 13px;
  transition: opacity 220ms ease, transform 220ms ease;
}
.toast.is-visible { opacity: 1; transform: translate(-50%, 0); }
footer {
  margin: 32px 0 10px;
  color: var(--muted);
  font-size: 12px;
}
[hidden] { display: none !important; }
@keyframes image-sweep {
  from { transform: translateX(-120%); }
  to { transform: translateX(120%); }
}
@media (max-width: 1100px) {
  .hero { grid-template-columns: 1fr; min-height: auto; }
  .hero-copy { min-height: auto; }
  .hero-media { min-height: 260px; }
  .command-bar { grid-template-columns: 1fr; position: static; }
  .result-count { border-left: 0; padding-left: 0; }
}
@media (max-width: 860px) {
  .shell { padding: 14px; }
  .topbar { margin: -14px -14px 14px; padding: 0 14px; align-items: flex-start; flex-direction: column; justify-content: center; min-height: auto; padding-top: 12px; padding-bottom: 12px; }
  .top-actions { width: 100%; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .top-actions .button { width: auto; min-height: 36px; padding: 7px 8px; }
  h1 { font-size: 28px; }
  .hero-copy { padding: 22px; }
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .audit-strip { grid-template-columns: 1fr; }
  .cards-grid { grid-template-columns: 1fr; }
  .video-card { grid-template-columns: 128px minmax(0, 1fr); min-height: 360px; }
  .media-button { min-height: 360px; }
  .key-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .replicate { grid-template-columns: 1fr; }
  .store-head { align-items: flex-start; flex-direction: column; }
  .store-metrics { justify-content: flex-start; }
  .detail-hero { grid-template-columns: 132px minmax(0, 1fr); }
  .detail-grid { grid-template-columns: 1fr; }
  .filter-set { align-items: flex-start; flex-direction: column; }
}
@media (max-width: 560px) {
  .button { width: 100%; }
  .top-actions .button { width: auto; }
  .hero-media { display: none; }
  .hero-copy { padding: 16px; }
  .hero .lead,
  .hero-actions { display: none; }
  .stats { grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 14px; }
  .stat { min-height: 58px; padding: 8px; }
  .stat b { font-size: 19px; }
  .stat span { margin-top: 6px; font-size: 10px; }
  .command-bar { gap: 8px; padding: 8px; margin-bottom: 14px; }
  .filter-set { gap: 6px; }
  .filter-label { display: none; }
  .result-count { font-size: 12px; }
  .store-section { margin: 14px 0; padding: 12px; }
  .store-head { margin-bottom: 10px; padding-bottom: 8px; }
  .store-head h2 { font-size: 20px; }
  .store-metrics { display: none; }
  .group-band { margin-top: 12px; }
  .group-head { margin-bottom: 8px; }
  .filter-buttons { flex-wrap: nowrap; overflow-x: auto; width: 100%; padding-bottom: 3px; }
  .filter-buttons button { flex: 0 0 auto; }
  .video-card { grid-template-columns: 1fr; }
  .media-button { min-height: 360px; aspect-ratio: 4 / 5; }
  .detail-panel { inset: 0; width: 100%; border-radius: 0; }
  .detail-hero { grid-template-columns: 1fr; }
  .detail-hero img { max-height: 420px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
  }
  .page-transition { display: none; }
}
"""

    js = r"""
const rows = JSON.parse(document.getElementById("report-data").textContent);
const storeOrder = Array.from(new Map(rows.map((row) => [row.store_id, row.shop_name])).entries());
const storeIndex = new Map(storeOrder.map(([storeId], index) => [storeId, index + 1]));
const groupLabels = {
  top_sales: "销量最高 Top 7",
  small_account_sales: "小账号爆款 Top 7"
};
let activeStore = "all";
let activeGroup = "all";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

function numberValue(value) {
  const num = Number.parseFloat(value);
  return Number.isFinite(num) ? num : 0;
}

function compact(value) {
  const num = numberValue(value);
  const abs = Math.abs(num);
  if (abs >= 1000000) return `${(num / 1000000).toFixed(1).replace(".0", "")}M`;
  if (abs >= 1000) return `${(num / 1000).toFixed(1).replace(".0", "")}K`;
  if (Number.isInteger(num)) return `${num}`;
  return num.toFixed(1);
}

function money(value) {
  return `$${compact(value)}`;
}

function text(value, fallback = "未提供") {
  const current = (value || "").toString().trim();
  return current || fallback;
}

function followerLabel(value) {
  const current = (value || "").toString().trim();
  return current ? compact(current) : "未验证";
}

function safeUrl(url) {
  return (url || "#").toString();
}

function groupChip(row) {
  return row.group === "small_account_sales"
    ? '<span class="chip small">小账号爆款</span>'
    : '<span class="chip hot">销量最高</span>';
}

function cardTemplate(row, index) {
  const cardId = `video-${index}`;
  const image = safeUrl(row.first_frame_path);
  const groupLabel = groupLabels[row.group] || row.group;
  const rank = row.group_rank || "";
  const caption = text(row.caption, "FastMoss 本行未提供视频文案");
  const skuTitle = text(row.matched_similar_product_title, "SKU 标题待补");
  return `
    <article class="video-card reveal" id="${cardId}" data-store="${row.store_id}" data-group="${row.group}" data-index="${index}">
      <button type="button" class="media-button" data-detail="${index}" aria-label="查看视频详情">
        <img src="${image}" loading="lazy" alt="视频首帧截图">
        <span class="rank-badge">#${rank}</span>
        <span class="group-badge">${groupLabel}</span>
      </button>
      <div class="card-body">
        <div class="chips">
          ${groupChip(row)}
          <span class="chip">销量 ${compact(row.video_sales)}</span>
          <span class="chip">GMV ${money(row.product_total_gmv)}</span>
          <span class="chip stock">库存 ${text(row.matched_sku_stock, "待核")}</span>
        </div>
        <h3 class="video-title" title="${escapeHtml(text(row.source_product_title))}">${escapeHtml(text(row.source_product_title))}</h3>
        <p class="caption">${escapeHtml(caption)}</p>
        <div class="key-metrics">
          <div class="key-metric"><span>播放</span><b>${compact(row.video_views)}</b></div>
          <div class="key-metric"><span>达人</span><b>${escapeHtml(text(row.creator_handle, "未提供"))}</b></div>
          <div class="key-metric"><span>粉丝</span><b>${followerLabel(row.creator_followers)}</b></div>
        </div>
        <div class="sku-line">
          <strong>${escapeHtml(text(row.matched_similar_sku, "SKU 待补"))}</strong>
          <span>${escapeHtml(skuTitle)}</span>
        </div>
        <div class="replicate">
          <div><b>买家痛点</b><p>${escapeHtml(text(row.buyer_pain))}</p></div>
          <div><b>证明动作</b><p>${escapeHtml(text(row.proof_action))}</p></div>
        </div>
        <div class="card-actions">
          <a href="${safeUrl(row.video_url)}" target="_blank" rel="noopener">打开视频</a>
          <button type="button" class="secondary" data-detail="${index}">展开详情</button>
          <button type="button" class="secondary" data-copy="${escapeHtml(text(row.matched_similar_sku, ""))}">复制 SKU</button>
        </div>
      </div>
    </article>
  `;
}

function escapeHtml(value) {
  return (value || "").toString()
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderFilters() {
  const storeBox = $("#storeFilters");
  storeBox.innerHTML = `
    <button type="button" class="is-active" data-store-filter="all">全部店铺</button>
    ${storeOrder.map(([storeId, shopName]) => `<button type="button" data-store-filter="${storeId}">${escapeHtml(shopName)}</button>`).join("")}
  `;
  const groupBox = $("#groupFilters");
  groupBox.innerHTML = `
    <button type="button" class="is-active" data-group-filter="all">全部榜单</button>
    <button type="button" data-group-filter="top_sales">销量最高</button>
    <button type="button" data-group-filter="small_account_sales">小账号爆款</button>
  `;
}

function renderStores() {
  const root = $("#reportRoot");
  root.innerHTML = storeOrder.map(([storeId, shopName]) => {
    const storeRows = rows.filter((row) => row.store_id === storeId);
    const storeSkus = new Set(storeRows.map((row) => row.matched_similar_sku).filter(Boolean)).size;
    const storeSales = storeRows.reduce((sum, row) => sum + numberValue(row.video_sales), 0);
    const groups = ["top_sales", "small_account_sales"].map((group) => {
      const groupRows = storeRows.filter((row) => row.group === group);
      return `
        <div class="group-band" data-group-block="${group}">
          <div class="group-head">
            <h3>${groupLabels[group]}</h3>
            <span>${groupRows.length} 条</span>
          </div>
          <div class="cards-grid">
            ${groupRows.map((row) => cardTemplate(row, rows.indexOf(row))).join("")}
          </div>
        </div>
      `;
    }).join("");
    return `
      <section class="store-section reveal" id="store-${storeId}" data-store-section="${storeId}">
        <div class="store-head">
          <div>
            <p class="eyebrow">STORE ${String(storeIndex.get(storeId)).padStart(2, "0")}</p>
            <h2>${escapeHtml(shopName)}</h2>
          </div>
          <div class="store-metrics">
            <span class="metric-pill"><b>${storeRows.length}</b> 条视频</span>
            <span class="metric-pill"><b>${storeSkus}</b> 个 SKU</span>
            <span class="metric-pill"><b>${compact(storeSales)}</b> 总销量</span>
          </div>
        </div>
        ${groups}
      </section>
    `;
  }).join("");
  $("[data-result-count]").textContent = rows.length;
}

function applyFilters() {
  let count = 0;
  $$(".video-card").forEach((card) => {
    const matchesStore = activeStore === "all" || card.dataset.store === activeStore;
    const matchesGroup = activeGroup === "all" || card.dataset.group === activeGroup;
    const visible = matchesStore && matchesGroup;
    if (visible) {
      card.hidden = false;
      requestAnimationFrame(() => card.classList.remove("is-filtered"));
      count += 1;
    } else {
      card.classList.add("is-filtered");
      window.setTimeout(() => {
        if (card.classList.contains("is-filtered")) card.hidden = true;
      }, 260);
    }
  });
  $("[data-result-count]").textContent = count;
  $$("[data-store-section]").forEach((section) => {
    const hasCards = $$(".video-card", section).some((card) => !card.hidden && !card.classList.contains("is-filtered"));
    section.hidden = !hasCards;
  });
  $$("[data-store-filter]").forEach((button) => button.classList.toggle("is-active", button.dataset.storeFilter === activeStore));
  $$("[data-group-filter]").forEach((button) => button.classList.toggle("is-active", button.dataset.groupFilter === activeGroup));
}

function setupFilters() {
  $("#storeFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-store-filter]");
    if (!button) return;
    activeStore = button.dataset.storeFilter;
    applyFilters();
  });
  $("#groupFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-group-filter]");
    if (!button) return;
    activeGroup = button.dataset.groupFilter;
    applyFilters();
  });
}

function setupReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { rootMargin: "0px 0px 8% 0px", threshold: .01 });
  $$(".reveal").forEach((element, index) => {
    element.style.transitionDelay = `${Math.min(index % 8, 6) * 38}ms`;
    observer.observe(element);
  });
}

function detailBlock(title, body, wide = false) {
  return `<div class="detail-block${wide ? " wide" : ""}"><h4>${escapeHtml(title)}</h4><p>${escapeHtml(text(body))}</p></div>`;
}

function openDetail(index) {
  const row = rows[index];
  if (!row) return;
  const panel = $("#detailPanel");
  panel.innerHTML = `
    <div class="detail-top">
      <div><b>${escapeHtml(text(row.shop_name))}</b><div class="eyebrow">${groupLabels[row.group] || row.group} / Rank ${row.group_rank}</div></div>
      <button type="button" class="detail-close" aria-label="关闭详情">&times;</button>
    </div>
    <div class="detail-content">
      <div class="detail-hero">
        <img src="${safeUrl(row.first_frame_path)}" alt="视频首帧截图">
        <div>
          <h3>${escapeHtml(text(row.source_product_title))}</h3>
          <p>${escapeHtml(text(row.caption, "FastMoss 本行未提供视频文案"))}</p>
          <div class="hero-actions">
            <a class="button" href="${safeUrl(row.video_url)}" target="_blank" rel="noopener">打开视频</a>
            <button class="button ghost" type="button" data-copy="${escapeHtml(text(row.matched_similar_sku, ""))}">复制 SKU</button>
          </div>
        </div>
      </div>
      <div class="detail-grid">
        ${detailBlock("销量 / GMV / 播放", `销量 ${compact(row.video_sales)}\nGMV ${money(row.product_total_gmv)}\n播放 ${compact(row.video_views)}`)}
        ${detailBlock("达人信息", `@${text(row.creator_handle, "未提供")}\n粉丝 ${followerLabel(row.creator_followers)}`)}
        ${detailBlock("可复刻 SKU", `${text(row.matched_similar_sku, "SKU 待补")}\n${text(row.matched_similar_product_title, "SKU 标题待补")}\n库存 ${text(row.matched_sku_stock, "待核")} / 匹配分 ${text(row.sku_match_score, "待核")}`, true)}
        ${detailBlock("SKU 匹配理由", row.sku_similarity_reason, true)}
        ${detailBlock("买家痛点", row.buyer_pain)}
        ${detailBlock("证明动作", row.proof_action)}
        ${detailBlock("原爆款视频结构", row.source_video_structure, true)}
        ${detailBlock("完整原视频口播", row.source_voiceover_full, true)}
        ${detailBlock("中文翻译 / 德文或英文对应状态", row.source_voiceover_zh, true)}
        ${detailBlock("封面文案", row.cover_copy)}
        ${detailBlock("推荐标签", row.hashtags)}
      </div>
    </div>
  `;
  $("#detailShell").classList.add("is-open");
  document.body.style.overflow = "hidden";
}

function closeDetail() {
  $("#detailShell").classList.remove("is-open");
  document.body.style.overflow = "";
}

function setupDetail() {
  document.addEventListener("click", (event) => {
    const detailButton = event.target.closest("[data-detail]");
    if (detailButton) {
      openDetail(Number(detailButton.dataset.detail));
      return;
    }
    const copyButton = event.target.closest("[data-copy]");
    if (copyButton) {
      const sku = copyButton.dataset.copy || "";
      if (sku && navigator.clipboard) {
        navigator.clipboard.writeText(sku).then(() => showToast(`已复制 ${sku}`)).catch(() => showToast(sku));
      } else if (sku) {
        showToast(sku);
      }
      return;
    }
    if (event.target.closest(".detail-close") || event.target.classList.contains("detail-backdrop")) {
      closeDetail();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDetail();
  });
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("is-visible"), 1600);
}

document.addEventListener("DOMContentLoaded", () => {
  renderFilters();
  renderStores();
  setupFilters();
  setupDetail();
  setupReveal();
  requestAnimationFrame(() => document.body.classList.add("is-loaded"));
});
"""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FastMoss 本周四店 56 条可复刻视频报告｜{esc(REPORT_DATE)}</title>
  <meta name="description" content="FastMoss 本周四店 56 条 TikTok 女装可复刻视频报告，包含首帧、销量、GMV、达人粉丝、相似 SKU、痛点、证明动作和采集状态。">
  <link rel="icon" href="data:,">
  <style>{css}</style>
</head>
<body>
  <div class="page-transition"></div>
  <main class="shell">
    <header class="topbar">
      <a class="brand" href="../../"><span class="brand-mark"></span><span>FastMoss Weekly</span></a>
      <nav class="top-actions" aria-label="报告操作">
        <a class="button ghost" href="data.csv">下载 CSV</a>
        <a class="button ghost" href="fastmoss-56-video-report-new-rules-2026-08-31.xlsx">下载 Excel</a>
        <a class="button" href="https://github.com/anjaiahtinku513-creator/fastmoss-weekly-report" target="_blank" rel="noopener">GitHub</a>
      </nav>
    </header>

    <section class="hero">
      <div class="hero-copy reveal">
        <div class="hero-inner">
          <p class="eyebrow">WEEKLY VIRAL VIDEO REPORT / {esc(REPORT_DATE)}</p>
          <h1>四店 56 条可复刻视频，一页看完本周最该拍什么。</h1>
          <p class="lead">按美国三店与德国一店拆分，每店 7 条销量最高视频和 7 条小账号爆款视频。每条视频都绑定一个本店铺可复刻 SKU，优先看销量、GMV、达人粉丝与实际库存。</p>
          <div class="hero-actions">
            <a class="button" href="#reportRoot">查看视频清单</a>
            <a class="button ghost" href="fastmoss-56-video-report-new-rules-2026-08-31.xlsx">下载完整 Excel</a>
          </div>
        </div>
        <div class="stats" aria-label="报告统计">
          <div class="stat"><b>{len(rows)}</b><span>入选视频</span></div>
          <div class="stat"><b>{group_counts.get("small_account_sales", 0)}</b><span>小账号爆款</span></div>
          <div class="stat"><b>{sku_count}</b><span>唯一 SKU</span></div>
          <div class="stat"><b>{money(top_gmv)}</b><span>本周样本 GMV</span></div>
        </div>
      </div>
      <div class="hero-media reveal">
        <img src="{esc(first_frame)}" alt="本周报告代表视频首帧">
        <div class="media-caption">
          <b>首帧驱动的选题看板</b>
          <span>卡片保留决策字段，原视频结构、完整口播和 SKU 证据进入详情抽屉，适合每周复盘与拍摄排期。</span>
        </div>
      </div>
    </section>

    <section class="command-bar reveal" aria-label="筛选">
      <div class="filter-set">
        <span class="filter-label">店铺</span>
        <div class="filter-buttons" id="storeFilters">{store_filters}</div>
      </div>
      <div class="filter-set">
        <span class="filter-label">榜单</span>
        <div class="filter-buttons" id="groupFilters"></div>
      </div>
      <div class="result-count"><b data-result-count>{len(rows)}</b> 条匹配</div>
    </section>

    <div id="reportRoot"></div>
    <section class="audit-strip reveal">
      <div><b>采集状态</b></div>
      <div>
        本周 FastMoss 官方导出含视频指标、标题/文案和首帧，不含可核验的完整音频转录与逐秒画面结构。页面保留“待补采”状态，不用通用模板代替原爆款结构。
        <div class="store-jump">{store_links}</div>
      </div>
    </section>
    <footer>GitHub Pages 静态发布。每周更新时替换报告目录数据并重新渲染页面。</footer>
  </main>

  <section class="detail-shell" id="detailShell" aria-live="polite">
    <div class="detail-backdrop"></div>
    <aside class="detail-panel" id="detailPanel" aria-label="视频详情"></aside>
  </section>
  <div class="toast" id="toast"></div>
  <script id="report-data" type="application/json">{data_json}</script>
  <script>{js}</script>
</body>
</html>
"""


def build_home_html(rows: list[dict[str, str]], manifest: dict) -> str:
    stores = ordered_stores(rows)
    first_frame = rows[0].get("first_frame_path", "") if rows else ""
    report_title = "FastMoss 本周四店 56 条可复刻视频报告｜新规则版"
    report_notes = "已补每条相似可复刻 SKU，SKU 不重复；本周导出缺完整原视频口播和逐秒结构，已在报告内标明待补采。"
    top_sales = sum(float(row.get("video_sales") or 0) for row in rows)
    top_gmv = sum(float(row.get("product_total_gmv") or 0) for row in rows)
    store_count = len(stores)
    data_json = safe_json({
        "date": REPORT_DATE,
        "title": report_title,
        "notes": report_notes,
        "path": f"reports/{REPORT_DATE}/",
        "thumbnail": f"reports/{REPORT_DATE}/{first_frame}",
        "items": len(rows),
        "stores": store_count,
        "sales": compact_number(top_sales),
        "gmv": money(top_gmv),
    })

    css = r"""
:root {
  --page: #f3f0e9;
  --paper: #fffdf8;
  --ink: #171717;
  --muted: #6b6760;
  --line: #d8d0c2;
  --hot: #f72566;
  --hot-dark: #b61243;
  --teal: #087f75;
  --amber: #b4642d;
  --shadow: 0 24px 70px rgba(42, 34, 24, .11);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  background:
    linear-gradient(90deg, rgba(23, 23, 23, .035) 1px, transparent 1px) 0 0 / 84px 84px,
    linear-gradient(180deg, #fffaf3 0%, var(--page) 54%, #ebe6dc 100%);
  color: var(--ink);
  font-family: "Microsoft YaHei", "PingFang SC", Inter, Arial, sans-serif;
  line-height: 1.55;
  letter-spacing: 0;
}
a { color: inherit; }
.wipe {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: var(--ink);
  transform: translateY(0);
  transition: transform 760ms cubic-bezier(.76,0,.24,1);
  pointer-events: none;
}
body.is-loaded .wipe { transform: translateY(-102%); }
.shell { max-width: 1240px; margin: 0 auto; padding: 24px; }
.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
}
.brand { display: flex; align-items: center; gap: 10px; font-weight: 820; }
.brand-mark {
  width: 12px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(180deg, var(--hot), var(--amber));
  box-shadow: 0 0 0 6px rgba(247,37,102,.08);
}
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 39px;
  padding: 8px 13px;
  border-radius: 6px;
  border: 1px solid var(--ink);
  background: var(--ink);
  color: #fff;
  text-decoration: none;
  font-weight: 780;
  transition: transform 180ms ease, box-shadow 180ms ease;
}
.button:hover { transform: translateY(-1px); box-shadow: 0 12px 32px rgba(42,34,24,.14); }
.button.ghost { background: rgba(255,253,248,.74); color: var(--ink); border-color: var(--line); }
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, .82fr);
  gap: 22px;
  align-items: stretch;
}
.panel,
.cover,
.archive {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255,253,248,.86);
  box-shadow: var(--shadow);
}
.panel {
  position: relative;
  overflow: hidden;
  padding: 34px;
  min-height: 520px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.panel::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(115deg, rgba(247,37,102,.09), transparent 34%),
    linear-gradient(150deg, transparent 55%, rgba(8,127,117,.1));
  pointer-events: none;
}
.content { position: relative; z-index: 1; }
.eyebrow {
  margin: 0 0 13px;
  color: var(--hot-dark);
  font-size: 12px;
  font-weight: 820;
}
h1 {
  margin: 0;
  max-width: 760px;
  font-size: 46px;
  line-height: 1.08;
  letter-spacing: 0;
}
.lead {
  max-width: 760px;
  margin: 18px 0 0;
  color: var(--muted);
  font-size: 15px;
}
.stats {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  margin-top: 30px;
  border: 1px solid var(--line);
  background: var(--line);
}
.stat { background: rgba(255,253,248,.92); padding: 15px; min-height: 96px; }
.stat b { display: block; font-size: 27px; line-height: 1; }
.stat span { display: block; margin-top: 8px; color: var(--muted); font-size: 12px; }
.cover {
  position: relative;
  min-height: 520px;
  overflow: hidden;
  background: #111;
}
.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transform: scale(1.035);
  transition: transform 1100ms cubic-bezier(.2,.8,.2,1);
}
body.is-loaded .cover img { transform: scale(1); }
.cover::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 30%, rgba(255,255,255,.22) 46%, transparent 62%);
  transform: translateX(-120%);
}
body.is-loaded .cover::after { animation: sweep 1100ms 430ms cubic-bezier(.2,.8,.2,1) both; }
.cover-info {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 22px;
  background: linear-gradient(180deg, transparent, rgba(0,0,0,.76));
  color: #fff;
}
.cover-info b { display: block; font-size: 20px; }
.cover-info span { display: block; margin-top: 4px; color: rgba(255,255,255,.78); font-size: 13px; }
.archive {
  margin-top: 22px;
  padding: 18px;
}
.archive-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 14px;
  margin-bottom: 16px;
}
.archive-head h2 { margin: 0; font-size: 24px; }
.report-row {
  display: grid;
  grid-template-columns: 128px minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  padding: 10px;
  transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
}
.report-row:hover {
  transform: translateY(-2px);
  border-color: rgba(247,37,102,.34);
  box-shadow: 0 16px 40px rgba(42,34,24,.12);
}
.report-row img {
  width: 128px;
  height: 92px;
  object-fit: cover;
  border-radius: 6px;
  background: #111;
}
.report-row h3 { margin: 0; font-size: 18px; line-height: 1.32; }
.report-row p { margin: 6px 0 0; color: var(--muted); font-size: 13px; }
.reveal {
  opacity: 0;
  transform: translateY(22px);
  transition: opacity 680ms ease, transform 680ms cubic-bezier(.2,.8,.2,1);
}
.reveal.is-visible { opacity: 1; transform: translateY(0); }
footer { margin: 24px 0 8px; color: var(--muted); font-size: 12px; }
@keyframes sweep {
  from { transform: translateX(-120%); }
  to { transform: translateX(120%); }
}
@media (max-width: 900px) {
  .shell { padding: 16px; }
  .nav { align-items: flex-start; flex-direction: column; }
  .hero { grid-template-columns: 1fr; }
  .panel, .cover { min-height: 430px; }
  h1 { font-size: 32px; }
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .report-row { grid-template-columns: 96px 1fr; }
  .report-row img { width: 96px; height: 76px; }
  .report-row .button { grid-column: 1 / -1; }
}
@media (max-width: 560px) {
  .actions, .button { width: 100%; }
  .panel { padding: 22px; }
  .report-row { grid-template-columns: 1fr; }
  .report-row img { width: 100%; height: 190px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
  }
  .wipe { display: none; }
}
"""

    js = r"""
const latest = JSON.parse(document.getElementById("latest-report").textContent);

function setupReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: .08 });
  document.querySelectorAll(".reveal").forEach((element, index) => {
    element.style.transitionDelay = `${Math.min(index, 5) * 54}ms`;
    observer.observe(element);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  fetch("reports.json")
    .then((response) => response.ok ? response.json() : null)
    .then((data) => {
      if (!data || !Array.isArray(data.reports) || data.reports.length === 0) return;
      const report = data.reports.slice().sort((a, b) => b.date.localeCompare(a.date))[0];
      document.querySelector("[data-report-count]").textContent = data.reports.length;
      document.querySelector("[data-item-count]").textContent = report.items || latest.items;
      document.querySelector("[data-store-count]").textContent = report.stores || latest.stores;
    })
    .catch(() => {});
  setupReveal();
  requestAnimationFrame(() => document.body.classList.add("is-loaded"));
});
"""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FastMoss 每周视频复刻报告</title>
  <meta name="description" content="FastMoss 每周美国和德国 TikTok 女装视频复刻报告归档。">
  <link rel="icon" href="data:,">
  <style>{css}</style>
</head>
<body>
  <div class="wipe"></div>
  <main class="shell">
    <header class="nav">
      <div class="brand"><span class="brand-mark"></span><span>FastMoss Weekly</span></div>
      <nav class="actions" aria-label="站点操作">
        <a class="button ghost" href="skill-packages/fastmoss-daily-video-analysis.zip">下载 Skill 安装包</a>
        <a class="button ghost" href="https://github.com/anjaiahtinku513-creator/fastmoss-weekly-report/tree/main/skills/fastmoss-daily-video-analysis" target="_blank" rel="noopener">Skill 源码</a>
        <a class="button" href="reports/{esc(REPORT_DATE)}/">打开最新报告</a>
      </nav>
    </header>

    <section class="hero">
      <div class="panel reveal">
        <div class="content">
          <p class="eyebrow">FASTMOSS WEEKLY / TIKTOK WOMENSWEAR</p>
          <h1>把每周爆款视频压缩成一张能执行的拍摄清单。</h1>
          <p class="lead">站点按周归档美国三店与德国一店的 FastMoss 视频复刻报告。最新版本保留首帧、销量、GMV、达人粉丝、店铺 SKU、买家痛点和证明动作，长结构进入详情页阅读。</p>
          <div class="actions" style="margin-top:24px">
            <a class="button" href="reports/{esc(REPORT_DATE)}/">进入最新周报</a>
            <a class="button ghost" href="reports/{esc(REPORT_DATE)}/fastmoss-56-video-report-new-rules-2026-08-31.xlsx">下载 Excel</a>
          </div>
        </div>
        <div class="stats" aria-label="归档统计">
          <div class="stat"><b data-report-count>1</b><span>已归档周报</span></div>
          <div class="stat"><b data-item-count>{len(rows)}</b><span>最新入选视频</span></div>
          <div class="stat"><b data-store-count>{store_count}</b><span>覆盖店铺</span></div>
          <div class="stat"><b>{money(top_gmv)}</b><span>样本 GMV</span></div>
        </div>
      </div>
      <aside class="cover reveal">
        <img src="reports/{esc(REPORT_DATE)}/{esc(first_frame)}" alt="最新报告视频首帧">
        <div class="cover-info">
          <b>{esc(REPORT_DATE)} 最新周报</b>
          <span>{esc(report_notes)}</span>
        </div>
      </aside>
    </section>

    <section class="archive reveal">
      <div class="archive-head">
        <div>
          <p class="eyebrow">REPORT ARCHIVE</p>
          <h2>历史报告</h2>
        </div>
        <a class="button ghost" href="https://github.com/anjaiahtinku513-creator/fastmoss-weekly-report" target="_blank" rel="noopener">打开仓库</a>
      </div>
      <article class="report-row">
        <img src="reports/{esc(REPORT_DATE)}/{esc(first_frame)}" alt="{esc(REPORT_DATE)} 报告预览">
        <div>
          <h3>{esc(REPORT_DATE)} {esc(report_title)}</h3>
          <p>{len(rows)} 条视频，{store_count} 个店铺，{compact_number(top_sales)} 样本销量。{esc(report_notes)}</p>
        </div>
        <a class="button" href="reports/{esc(REPORT_DATE)}/">查看</a>
      </article>
    </section>

    <footer>GitHub Pages 静态发布。每周更新时新增日期目录并刷新 reports.json。</footer>
  </main>
  <script id="latest-report" type="application/json">{data_json}</script>
  <script>{js}</script>
</body>
</html>
"""


def main() -> None:
    rows = read_rows()
    manifest = read_manifest()
    REPORT_HTML_PATH.write_text(build_report_html(rows, manifest), encoding="utf-8")
    HOME_HTML_PATH.write_text(build_home_html(rows, manifest), encoding="utf-8")
    print(f"Rendered {HOME_HTML_PATH}")
    print(f"Rendered {REPORT_HTML_PATH}")


if __name__ == "__main__":
    main()
