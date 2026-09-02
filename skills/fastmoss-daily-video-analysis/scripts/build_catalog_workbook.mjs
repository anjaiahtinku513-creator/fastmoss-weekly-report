#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";


const TABLES = [
  {
    key: "product_master",
    sheetName: "\u5546\u54c1\u4e3b\u8868",
    tableName: "ProductMaster",
    headers: [
      "market", "sku", "display_name", "title", "title_status", "catalog_segment", "category",
      "product_type", "planning_type", "style_label", "season", "operations_note", "fabric", "colors",
      "selling_points", "pain_points", "proof_actions", "scenarios", "normal_price", "promo_price",
      "currency", "weight_g", "cost_cny", "profit_cny", "margin", "gmv", "units_sold", "video_gmv",
      "product_card_gmv", "performance_period", "image_workbook", "image_sheet", "image_row",
      "main_image_count", "white_image_count", "scene_image_count", "has_market_inventory", "is_in_stock",
      "catalog_status", "missing_fields", "source_updated_at", "source_files",
    ],
  },
  {
    key: "identifier_aliases",
    sheetName: "\u6807\u8bc6\u522b\u540d\u8868",
    tableName: "IdentifierAliases",
    headers: [
      "market", "sku", "old_skus", "tiktok_product_ids", "primary_tiktok_product_id", "product_id_sources",
      "amazon_asins", "preferred_asin", "preferred_asin_image_url", "active_asin_count", "delisted_asin_count",
      "asin_conflict_count", "identifier_conflict", "source_files",
    ],
  },
  {
    key: "market_inventory",
    sheetName: "\u5e02\u573a\u5e93\u5b58\u8868",
    tableName: "MarketInventory",
    headers: [
      "market", "sku", "source_sku", "match_basis", "alias_conflict", "snapshot_date", "stock_status",
      "on_hand_stock", "available_stock", "in_transit_stock", "available_plus_in_transit", "daily_sales_7d",
      "color_count", "full_stock_color_count", "sku_count", "zero_available_sku_count", "is_available", "source_file",
    ],
  },
];


function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index]?.replace(/^--/, "");
    const value = argv[index + 1];
    if (key && value) args[key] = value;
  }
  if (!args.input || !args.output || !args.previewDir) {
    throw new Error("Usage: build_catalog_workbook.mjs --input data.json --output catalog.xlsx --previewDir previews");
  }
  return args;
}


function columnName(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    value -= 1;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
}


function widthFor(header) {
  if (["market", "currency"].includes(header)) return 9;
  if (["sku", "source_sku", "preferred_asin", "snapshot_date"].includes(header)) return 16;
  if (header.includes("product_id") || header.includes("asin")) return header.endsWith("count") ? 12 : 34;
  if (header.includes("source_file") || header === "image_workbook") return 42;
  if (["selling_points", "pain_points", "proof_actions", "operations_note", "missing_fields"].includes(header)) return 36;
  if (["fabric", "colors", "display_name", "category", "catalog_status"].includes(header)) return 24;
  if (header.includes("price") || header.includes("stock") || header.includes("gmv") || header.includes("count")) return 14;
  return 18;
}


function writeSheet(workbook, definition, rows) {
  const sheet = workbook.worksheets.add(definition.sheetName);
  const headers = definition.headers;
  const matrix = [headers, ...rows.map((row) => headers.map((header) => row[header] ?? null))];
  const endColumn = columnName(headers.length - 1);
  const endRow = Math.max(1, matrix.length);
  const used = sheet.getRange(`A1:${endColumn}${endRow}`);
  used.values = matrix;
  used.format.font = { name: "Calibri", size: 10, color: "#17211B" };
  used.format.verticalAlignment = "top";
  used.format.borders = { preset: "all", style: "thin", color: "#D9E2DC" };
  sheet.getRange(`A1:${endColumn}1`).format = {
    fill: "#176B4D",
    font: { name: "Calibri", size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    rowHeight: 32,
  };
  for (let index = 0; index < headers.length; index += 1) {
    const column = columnName(index);
    const body = sheet.getRange(`${column}2:${column}${endRow}`);
    body.format.columnWidth = widthFor(headers[index]);
    if (["selling_points", "pain_points", "proof_actions", "operations_note", "missing_fields", "source_files", "source_file", "amazon_asins"].includes(headers[index])) {
      body.format.wrapText = true;
    }
    if (["normal_price", "promo_price", "cost_cny", "profit_cny", "gmv", "video_gmv", "product_card_gmv"].includes(headers[index])) {
      body.format.numberFormat = "#,##0.00";
    }
    if (["weight_g", "units_sold", "image_row", "main_image_count", "white_image_count", "scene_image_count", "active_asin_count", "delisted_asin_count", "asin_conflict_count", "on_hand_stock", "available_stock", "in_transit_stock", "available_plus_in_transit", "daily_sales_7d", "color_count", "full_stock_color_count", "sku_count", "zero_available_sku_count"].includes(headers[index])) {
      body.format.numberFormat = "#,##0";
    }
    if (headers[index] === "margin") body.format.numberFormat = "0.0%";
  }
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(2);
  sheet.showGridLines = false;
  const table = sheet.tables.add(`A1:${endColumn}${endRow}`, true, definition.tableName);
  table.style = "TableStyleMedium4";
  table.showFilterButton = true;
  return { sheet, endColumn, endRow };
}


const args = parseArgs(process.argv.slice(2));
const payload = JSON.parse(await fs.readFile(args.input, "utf8"));
const workbook = Workbook.create();
const rendered = [];

for (const definition of TABLES) {
  const rows = payload.tables?.[definition.key] ?? [];
  const result = writeSheet(workbook, definition, rows);
  const previewEndColumn = columnName(Math.min(definition.headers.length, 12) - 1);
  const previewEndRow = Math.min(result.endRow, 25);
  const preview = await workbook.render({
    sheetName: definition.sheetName,
    range: `A1:${previewEndColumn}${previewEndRow}`,
    scale: 1.2,
    format: "png",
  });
  await fs.mkdir(args.previewDir, { recursive: true });
  const previewPath = path.join(args.previewDir, `${definition.key}.png`);
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
  rendered.push(previewPath);
}

const inspect = await workbook.inspect({
  kind: "sheet,table",
  include: "id,name,range",
  maxChars: 5000,
  tableMaxRows: 3,
  tableMaxCols: 8,
});
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "catalog formula error scan",
});

await fs.mkdir(path.dirname(args.output), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(args.output);
console.log(JSON.stringify({
  output: path.resolve(args.output),
  rows: Object.fromEntries(TABLES.map((definition) => [definition.key, payload.tables?.[definition.key]?.length ?? 0])),
  previews: rendered,
  inspect: inspect.ndjson,
  errors: errors.ndjson,
}));
