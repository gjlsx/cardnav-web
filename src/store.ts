// @ts-nocheck
/**
 * 文件说明: 负责公开站点首页的数据读取、提交入库和搜索行为持久化。
 */
import 'dotenv/config';
import { createHash } from 'node:crypto';
import mysql from 'mysql2/promise';
import type { PackedShopProductsData, PublicShopProductsData } from './shop-products-data.js';
import { validatePublicSubmittedUrl, type PublicSubmittedUrlRejectReason } from './submitted-url.js';

export type PublicSiteRow = {
  id: string;
  name: string;
  url: string;
  lastProductRefreshSuccessAt: string | null;
  lastProductRefreshSuccessTime: string;
  score: number;
  sponsor: boolean;
};

export type PublicGatewaySiteRow = {
  id: string;
  slug: string;
  name: string;
  url: string;
  outboundUrl: string;
  host: string;
  family: string;
  displayFamily: string;
  createdAt: string | null;
  createdTime: string;
  lastProductRefreshCompleteAt: string | null;
  lastProductRefreshCompleteTime: string;
  siteScore: number | null;
  sponsor: boolean;
  availabilityPercent: number;
  avgSuccessLatencyMs: number | null;
  summary: string;
  modelTypes: string[];
  paymentMethods: string[];
  modelCount: number;
  priceCount: number;
  modelFamilies: string[];
  displayModelFamilies: string[];
  refreshStatus: string;
  refreshErrorType: string;
  latestGatewayRefreshAt: string | null;
  latestGatewayRefreshTime: string;
};

export type PublicGatewayPriceRow = {
  modelId: string;
  unit: string;
  inputPrice: number | null;
  outputPrice: number | null;
  cacheInputPrice: number | null;
  cacheOutputPrice: number | null;
};

export type PublicGatewayModelRow = {
  id: string;
  modelId: string;
  modelFamily: string;
  supportSiteCount: number;
  priceCount: number;
  latestGatewayRefreshAt: string | null;
  latestGatewayRefreshTime: string;
};

export type PublicGatewayModelSiteRow = PublicGatewaySiteRow & {
  priceCountForModel: number;
  unitsForModel: string[];
  pricesForModel: PublicGatewayPriceRow[];
  latestModelRefreshAt: string | null;
  latestModelRefreshTime: string;
};

export type PublicGatewayDetail = {
  site: PublicGatewaySiteRow;
  prices: PublicGatewayPriceRow[];
};

export type PublicGatewayModelDetail = {
  model: PublicGatewayModelRow;
  sites: PublicGatewayModelSiteRow[];
};

export type PublicProductRow = {
  categoryName: string;
  name: string;
  price: string;
  priceNumber: number | null;
  priceUnit: string | null;
  productUrl?: string;
  stock?: number;
  inStock: boolean;
  refreshedAt: string | null;
  refreshTime: string;
  siteId: string;
  siteName: string;
  siteUrl: string;
  siteProductRefreshSuccessAt: string | null;
  siteProductRefreshSuccessTime: string;
  siteScore: number;
  siteSponsor: boolean;
  clickCount: number;
  score: number;
};

export type ProductClickInput = {
  siteId: string;
  productUrl?: string;
  categoryName?: string;
  name?: string;
};

export type PopularSearchTermsSnapshot = {
  terms: string[];
  normalizedTerms: string[];
};

type SubmitSiteUrlErrorKey = PublicSubmittedUrlRejectReason | 'duplicateUrl' | 'invalidGatewayInfo' | 'gatewayInvalidUrl' | 'gatewayInvalidApiEndpoint';
type PublicSnapshotKey =
  | 'shop-products'
  | 'shop-products-packed'
  | 'popular-search-terms'
  | 'gateway-sites'
  | 'gateway-models'
  | 'official-price-catalog'
  | 'official-prices'
  | 'model-leaderboard-task-slugs'
  | 'model-leaderboards';

type PublicListLimitOptions = {
  limit?: number;
};
type PublicGatewaySitesData = { sites: PublicGatewaySiteRow[]; totalSiteCount: number; sitesWithPricesCount: number; totalModelCount: number; totalPriceCount: number };
type PublicGatewayModelsData = { models: PublicGatewayModelRow[]; totalModelCount: number; totalSupportCount: number };

function safeListLimit(limit: number | undefined) {
  return typeof limit === 'number' && Number.isFinite(limit)
    ? Math.max(1, Math.floor(limit))
    : null;
}

type QueryResult = { rows: Array<Record<string, unknown>> };

type DatabaseClient = {
  query(sql: string, values?: unknown[]): Promise<QueryResult>;
};

let pool: mysql.Pool | null = null;
const beijingDateFormatter = new Intl.DateTimeFormat('sv-SE', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
});

function getPool() {
  if (!pool) {
    pool = mysql.createPool({
      host: process.env.MYSQL_HOST || '127.0.0.1',
      port: Number(process.env.MYSQL_PORT || 3306),
      user: process.env.MYSQL_USER || 'root',
      password: process.env.MYSQL_PASSWORD,
      database: process.env.MYSQL_DATABASE || 'ailovemoney',
      connectionLimit: 12,
      connectTimeout: 5_000,
      timezone: 'Z',
    });
  }

  const query = async (sql: string, values: unknown[] = []): Promise<QueryResult> => {
    const [rows] = await pool!.query(sql, values);
    return { rows: Array.isArray(rows) ? rows as Array<Record<string, unknown>> : [] };
  };
  return { query } satisfies DatabaseClient;
}

async function loadPublicSnapshot<T>(key: PublicSnapshotKey): Promise<T | null> {
  try {
    const result = await getPool().query(
      'SELECT payload FROM public_snapshot_entries WHERE `key` = ?',
      [key],
    );
    return result.rows[0]?.payload as T ?? null;
  } catch (error) {
    if (typeof error === 'object' && error && 'code' in error && error.code === '42P01') {
      return null;
    }
    throw error;
  }
}

export function formatBeijingRefreshTime(input: string | null | undefined): string {
  if (!input) return '';
  const date = new Date(input);
  if (Number.isNaN(date.getTime())) return '';
  const parts = beijingDateFormatter.formatToParts(date);
  const lookup = Object.fromEntries(parts.map(part => [part.type, part.value]));
  return `${lookup.year}-${lookup.month}-${lookup.day} ${lookup.hour}:${lookup.minute}:${lookup.second}`;
}

function displayGatewayFamily(family: string) {
  if (!family || family === 'unknown' || family === 'custom' || family.startsWith('custom-')) return '';
  const labels: Record<string, string> = {
    newApi: 'New API',
    sub2Api: 'Sub2API',
    oneApi: 'One API',
    rixApi: 'Rix API',
    voApi: 'VoAPI',
    veloera: 'Veloera',
    anyRouter: 'AnyRouter',
    metapi: 'MetAPI',
  };
  return labels[family] ?? family;
}

function mapGatewaySiteRow(row: Record<string, unknown>): PublicGatewaySiteRow {
  const createdAt = row.created_at ? String(row.created_at) : null;
  const latestGatewayRefreshAt = row.latest_gateway_refresh_at ? String(row.latest_gateway_refresh_at) : null;
  const family = row.family ? String(row.family) : '';
  const url = String(row.url);
  const inviteUrl = row.invite_url ? String(row.invite_url).trim() : '';
  return {
    id: String(row.id || ''),
    slug: String(row.slug || ''),
    name: String(row.site_name),
    url,
    outboundUrl: inviteUrl || url,
    host: row.host ? String(row.host) : hostFromUrl(url),
    family,
    displayFamily: displayGatewayFamily(family),
    createdAt,
    createdTime: formatBeijingRefreshTime(createdAt),
    lastProductRefreshCompleteAt: null,
    lastProductRefreshCompleteTime: '',
    siteScore: Number(row.score) || 0,
    sponsor: row.sponsor === true || row.sponsor === 1 || row.sponsor === '1',
    availabilityPercent: Number(row.availability_percent) || 0,
    avgSuccessLatencyMs: row.avg_success_latency_ms == null ? null : Number(row.avg_success_latency_ms),
    summary: String(row.summary || ''),
    modelTypes: parseStringList(row.model_types),
    paymentMethods: parseStringList(row.payment_methods),
    modelCount: Number(row.model_count) || 0,
    priceCount: Number(row.price_count) || 0,
    modelFamilies: parseStringList(row.model_families),
    displayModelFamilies: parseStringList(row.display_model_families),
    refreshStatus: '',
    refreshErrorType: '',
    latestGatewayRefreshAt,
    latestGatewayRefreshTime: formatBeijingRefreshTime(latestGatewayRefreshAt),
  };
}

function parseStringList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String);
  if (typeof value !== 'string') return [];
  try {
    const parsed: unknown = JSON.parse(value);
    if (Array.isArray(parsed)) return parsed.map(String);
  } catch {
    // MySQL GROUP_CONCAT values are represented as comma-separated strings.
  }
  return value.split(',').map(item => item.trim()).filter(Boolean);
}

function mapGatewayModelSiteRow(row: Record<string, unknown>, modelId: string): PublicGatewayModelSiteRow {
  const latestModelRefreshAt = row.latest_model_refresh_at ? String(row.latest_model_refresh_at) : null;
  return {
    ...mapGatewaySiteRow(row),
    priceCountForModel: Number(row.price_count_for_model) || 0,
    unitsForModel: Array.isArray(row.units_for_model) ? row.units_for_model.map(String) : [],
    pricesForModel: Array.isArray(row.prices_for_model) ? row.prices_for_model.map((price: Record<string, unknown>) => ({
      modelId,
      unit: String(price.unit || ''),
      inputPrice: price.inputPrice == null ? null : Number(price.inputPrice),
      outputPrice: price.outputPrice == null ? null : Number(price.outputPrice),
      cacheInputPrice: price.cacheInputPrice == null ? null : Number(price.cacheInputPrice),
      cacheOutputPrice: price.cacheOutputPrice == null ? null : Number(price.cacheOutputPrice),
    })) : [],
    latestModelRefreshAt,
    latestModelRefreshTime: formatBeijingRefreshTime(latestModelRefreshAt),
  };
}

function mapMySqlGatewaySiteRow(row: Record<string, unknown>) {
  const site = mapGatewaySiteRow(row);
  return {
    ...site,
    displayModelFamilies: site.modelFamilies.length > 0 ? site.modelFamilies : site.modelTypes,
  };
}

async function mysqlGatewaySiteRows(options: { slug?: string; modelId?: string; limit?: number | null } = {}) {
  const values: unknown[] = [];
  let modelFilter = '';
  if (options.modelId) {
    modelFilter = ' AND EXISTS (SELECT 1 FROM gateway_model_prices filtered_prices WHERE filtered_prices.site_id = gateway_sites.site_id AND filtered_prices.model_id = ?)';
    values.push(options.modelId);
  }
  if (options.slug) {
    modelFilter += ' AND gateway_sites.slug = ?';
    values.push(options.slug);
  }
  const result = await getPool().query(`
    SELECT
      gateway_sites.site_id AS id,
      gateway_sites.name AS site_name,
      gateway_sites.url,
      gateway_sites.family,
      gateway_sites.score,
      gateway_sites.availability_percent,
      gateway_sites.avg_success_latency_ms,
      gateway_sites.created_at,
      gateway_sites.slug,
      gateway_sites.host,
      gateway_sites.summary,
      gateway_sites.invite_url,
      gateway_sites.sponsor,
      gateway_sites.model_types,
      gateway_sites.payment_methods,
      COUNT(DISTINCT prices.model_id) AS model_count,
      COUNT(prices.id) AS price_count,
      COALESCE(GROUP_CONCAT(DISTINCT NULLIF(NULLIF(prices.model_family, ''), 'Other') ORDER BY prices.model_family SEPARATOR ','), '') AS model_families,
      MAX(prices.fetched_at) AS latest_gateway_refresh_at
    FROM gateway_sites
    LEFT JOIN gateway_model_prices prices ON prices.site_id = gateway_sites.site_id
    WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway'${modelFilter}
    GROUP BY gateway_sites.site_id, gateway_sites.name, gateway_sites.url, gateway_sites.family, gateway_sites.score,
      gateway_sites.availability_percent, gateway_sites.avg_success_latency_ms, gateway_sites.created_at,
      gateway_sites.slug, gateway_sites.host, gateway_sites.summary, gateway_sites.invite_url, gateway_sites.sponsor,
      gateway_sites.model_types, gateway_sites.payment_methods, gateway_sites.weight
    ORDER BY gateway_sites.sponsor DESC, gateway_sites.score DESC, gateway_sites.weight DESC, gateway_sites.created_at DESC, gateway_sites.name ASC, gateway_sites.site_id ASC
    ${options.limit ? 'LIMIT ?' : ''}
  `, options.limit ? [...values, options.limit] : values);
  return result.rows.map(mapMySqlGatewaySiteRow);
}

async function loadMySqlShopProductsData(options: { productLimit?: number; inStockOnly?: boolean }): Promise<PublicShopProductsData> {
  const limit = typeof options.productLimit === 'number' && Number.isFinite(options.productLimit) ? Math.max(1, Math.floor(options.productLimit)) : null;
  const productsResult = await getPool().query(`
    SELECT
      shop_products.site_id, shop_sites.name AS site_name, shop_sites.url AS site_url,
      shop_sites.score AS site_score, shop_sites.sponsor AS site_sponsor,
      shop_sites.last_product_refresh_success_at AS site_product_refresh_success_at,
      shop_products.category_name, shop_products.name, shop_products.price, shop_products.price_number,
      shop_products.price_unit, shop_products.product_url, shop_products.stock, shop_products.in_stock,
      shop_products.click_count, shop_products.score, shop_products.refreshed_at
    FROM shop_products
    INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id
    WHERE shop_sites.status = 'online' AND shop_sites.type = 'cardShop'
      ${options.inStockOnly ? 'AND shop_products.in_stock = TRUE' : ''}
    ORDER BY shop_sites.sponsor DESC, shop_products.score DESC, shop_sites.score DESC, shop_products.in_stock DESC,
      shop_products.refreshed_at DESC, shop_products.category_name ASC, shop_products.name ASC
    ${limit ? 'LIMIT ?' : ''}
  `, limit ? [limit] : []);
  const products: PublicProductRow[] = productsResult.rows.map(row => {
    const refreshedAt = row.refreshed_at ? String(row.refreshed_at) : null;
    const siteProductRefreshSuccessAt = row.site_product_refresh_success_at ? String(row.site_product_refresh_success_at) : null;
    return {
      categoryName: String(row.category_name || ''), name: String(row.name || ''), price: String(row.price || ''),
      priceNumber: row.price_number == null ? null : Number(row.price_number), priceUnit: row.price_unit == null ? null : String(row.price_unit),
      ...(row.product_url ? { productUrl: String(row.product_url) } : {}), ...(row.stock == null ? {} : { stock: Number(row.stock) }),
      inStock: row.in_stock === true || row.in_stock === 1 || row.in_stock === '1', refreshedAt, refreshTime: formatBeijingRefreshTime(refreshedAt),
      clickCount: Number(row.click_count) || 0, siteId: String(row.site_id || ''), siteName: String(row.site_name || ''), siteUrl: String(row.site_url || ''),
      siteProductRefreshSuccessAt, siteProductRefreshSuccessTime: formatBeijingRefreshTime(siteProductRefreshSuccessAt), siteScore: Number(row.site_score) || 0,
      siteSponsor: row.site_sponsor === true || row.site_sponsor === 1 || row.site_sponsor === '1', score: Number(row.score) || 0,
    };
  });
  const sitesResult = await getPool().query(`SELECT id, name, url, score, sponsor, last_product_refresh_success_at FROM shop_sites WHERE status = 'online' AND type = 'cardShop' ORDER BY sponsor DESC, score DESC, product_count DESC, in_stock_product_count DESC, last_product_refresh_success_at DESC, id ASC`);
  const summaryResult = await getPool().query(`
    SELECT COUNT(*) AS total_site_count,
      COALESCE((SELECT COUNT(*) FROM shop_products INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id WHERE shop_sites.status = 'online' AND shop_sites.type = 'cardShop'), 0) AS total_product_count,
      COALESCE((SELECT COUNT(*) FROM shop_products INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id WHERE shop_sites.status = 'online' AND shop_sites.type = 'cardShop' AND shop_products.in_stock = TRUE), 0) AS total_in_stock_product_count,
      MAX(last_product_refresh_success_at) AS latest_refreshed_at
    FROM shop_sites WHERE status = 'online' AND type = 'cardShop'
  `);
  const summary = summaryResult.rows[0] ?? {};
  return {
    sites: sitesResult.rows.map(row => { const at = row.last_product_refresh_success_at ? String(row.last_product_refresh_success_at) : null; return { id: String(row.id || ''), name: String(row.name || ''), url: String(row.url || ''), lastProductRefreshSuccessAt: at, lastProductRefreshSuccessTime: formatBeijingRefreshTime(at), score: Number(row.score) || 0, sponsor: row.sponsor === true || row.sponsor === 1 || row.sponsor === '1' }; }),
    products, totalSiteCount: Number(summary.total_site_count) || 0, totalProductCount: Number(summary.total_product_count) || 0,
    totalInStockProductCount: Number(summary.total_in_stock_product_count) || 0, latestRefreshedAt: summary.latest_refreshed_at ? String(summary.latest_refreshed_at) : null,
    latestRefreshTime: formatBeijingRefreshTime(summary.latest_refreshed_at ? String(summary.latest_refreshed_at) : null),
    isPartial: (options.inStockOnly ? Number(summary.total_in_stock_product_count) : Number(summary.total_product_count)) > products.length,
  };
}

async function loadMySqlGatewaySites(options: PublicListLimitOptions): Promise<PublicGatewaySitesData> {
  const limit = safeListLimit(options.limit);
  const sites = await mysqlGatewaySiteRows({ limit });
  const summaryResult = await getPool().query(`
    SELECT COUNT(*) AS total_site_count, COALESCE(SUM(price_count > 0), 0) AS sites_with_prices_count,
      COALESCE(SUM(model_count), 0) AS total_model_count, COALESCE(SUM(price_count), 0) AS total_price_count
    FROM (
      SELECT gateway_sites.site_id, COUNT(DISTINCT prices.model_id) AS model_count, COUNT(prices.id) AS price_count
      FROM gateway_sites LEFT JOIN gateway_model_prices prices ON prices.site_id = gateway_sites.site_id
      WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway'
      GROUP BY gateway_sites.site_id
    ) AS online_sites
  `);
  const summary = summaryResult.rows[0] ?? {};
  return { sites, totalSiteCount: Number(summary.total_site_count) || 0, sitesWithPricesCount: Number(summary.sites_with_prices_count) || 0, totalModelCount: Number(summary.total_model_count) || 0, totalPriceCount: Number(summary.total_price_count) || 0 };
}

async function loadMySqlGatewayModels(options: PublicListLimitOptions): Promise<PublicGatewayModelsData> {
  const limit = safeListLimit(options.limit);
  const result = await getPool().query(`
    SELECT prices.model_id, COALESCE(NULLIF(prices.model_family, ''), 'Other') AS model_family,
      COUNT(DISTINCT prices.site_id) AS support_site_count, COUNT(*) AS price_count,
      MAX(prices.fetched_at) AS latest_gateway_refresh_at, MAX(gateway_sites.score) AS max_site_score
    FROM gateway_model_prices prices INNER JOIN gateway_sites ON gateway_sites.site_id = prices.site_id
    WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway'
    GROUP BY prices.model_id, COALESCE(NULLIF(prices.model_family, ''), 'Other')
    ORDER BY support_site_count DESC, max_site_score DESC, prices.model_id ASC ${limit ? 'LIMIT ?' : ''}
  `, limit ? [limit] : []);
  const models = result.rows.map(row => { const at = row.latest_gateway_refresh_at ? String(row.latest_gateway_refresh_at) : null; return { id: String(row.model_id), modelId: String(row.model_id), modelFamily: String(row.model_family || 'Other'), supportSiteCount: Number(row.support_site_count) || 0, priceCount: Number(row.price_count) || 0, latestGatewayRefreshAt: at, latestGatewayRefreshTime: formatBeijingRefreshTime(at) }; });
  return { models, totalModelCount: models.length, totalSupportCount: models.reduce((sum, model) => sum + model.supportSiteCount, 0) };
}

async function loadMySqlGatewaySiteBySlug(slug: string) {
  const sites = await mysqlGatewaySiteRows({ slug: slug.trim(), limit: 1 });
  return sites[0] ?? null;
}

async function loadMySqlGatewayModelSummary(modelId: string): Promise<PublicGatewayModelRow | null> {
  const result = await getPool().query(`
    SELECT prices.model_id, COALESCE(NULLIF(prices.model_family, ''), 'Other') AS model_family,
      COUNT(DISTINCT prices.site_id) AS support_site_count, COUNT(*) AS price_count, MAX(prices.fetched_at) AS latest_gateway_refresh_at
    FROM gateway_model_prices prices INNER JOIN gateway_sites ON gateway_sites.site_id = prices.site_id
    WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway' AND prices.model_id = ?
    GROUP BY prices.model_id, COALESCE(NULLIF(prices.model_family, ''), 'Other') LIMIT 1
  `, [modelId]);
  const row = result.rows[0];
  if (!row) return null;
  const at = row.latest_gateway_refresh_at ? String(row.latest_gateway_refresh_at) : null;
  return { id: String(row.model_id), modelId: String(row.model_id), modelFamily: String(row.model_family || 'Other'), supportSiteCount: Number(row.support_site_count) || 0, priceCount: Number(row.price_count) || 0, latestGatewayRefreshAt: at, latestGatewayRefreshTime: formatBeijingRefreshTime(at) };
}

async function loadMySqlGatewayDetail(slug: string, options: { priceLimit?: number }) {
  const site = await loadMySqlGatewaySiteBySlug(slug);
  if (!site) return null;
  const limit = safeListLimit(options.priceLimit);
  const result = await getPool().query(`
    SELECT model_id, unit, input_price, output_price, cache_input_price, cache_output_price
    FROM gateway_model_prices WHERE site_id = ?
    ORDER BY FIELD(model_family, 'GPT', 'Claude', 'Gemini', 'Qwen', 'Grok'), model_id ASC, unit ASC ${limit ? 'LIMIT ?' : ''}
  `, limit ? [site.id, limit] : [site.id]);
  return { site, prices: result.rows.map(row => ({ modelId: String(row.model_id), unit: String(row.unit || ''), inputPrice: row.input_price == null ? null : Number(row.input_price), outputPrice: row.output_price == null ? null : Number(row.output_price), cacheInputPrice: row.cache_input_price == null ? null : Number(row.cache_input_price), cacheOutputPrice: row.cache_output_price == null ? null : Number(row.cache_output_price) })) };
}

async function loadMySqlGatewayModelDetail(modelId: string, options: { siteLimit?: number }) {
  const model = await loadMySqlGatewayModelSummary(modelId);
  if (!model) return null;
  const sites = await mysqlGatewaySiteRows({ modelId, limit: safeListLimit(options.siteLimit) });
  const pricesResult = await getPool().query(`SELECT site_id, model_id, unit, input_price, output_price, cache_input_price, cache_output_price, fetched_at FROM gateway_model_prices WHERE model_id = ? ORDER BY unit ASC, input_price ASC, output_price ASC`, [modelId]);
  const pricesBySite = new Map<string, PublicGatewayPriceRow[]>();
  const datesBySite = new Map<string, string[]>();
  for (const row of pricesResult.rows) {
    const siteId = String(row.site_id);
    pricesBySite.set(siteId, [...(pricesBySite.get(siteId) ?? []), { modelId: String(row.model_id), unit: String(row.unit || ''), inputPrice: row.input_price == null ? null : Number(row.input_price), outputPrice: row.output_price == null ? null : Number(row.output_price), cacheInputPrice: row.cache_input_price == null ? null : Number(row.cache_input_price), cacheOutputPrice: row.cache_output_price == null ? null : Number(row.cache_output_price) }]);
    if (row.fetched_at) datesBySite.set(siteId, [...(datesBySite.get(siteId) ?? []), String(row.fetched_at)]);
  }
  return { model, sites: sites.map(site => { const prices = pricesBySite.get(site.id) ?? []; const at = (datesBySite.get(site.id) ?? []).sort().at(-1) ?? null; return { ...site, priceCountForModel: prices.length, unitsForModel: [...new Set(prices.map(price => price.unit).filter(Boolean))], pricesForModel: prices, latestModelRefreshAt: at, latestModelRefreshTime: formatBeijingRefreshTime(at) }; }) };
}

async function loadMySqlPopularSearchTerms(limit: number, presetPopularSearchTerms: string[]) {
  const safeLimit = Math.max(1, Math.min(30, Math.floor(limit)));
  const runtime = await getPool().query(`SELECT term FROM shop_search_terms WHERE total_count > 0 AND result_count > 0 ORDER BY total_count DESC, result_count DESC, last_seen_at DESC, term ASC LIMIT ?`, [safeLimit]);
  const terms = runtime.rows.map(row => String(row.term));
  const seen = new Set(terms.map(normalizeSearchText));
  for (const candidate of presetPopularSearchTerms) {
    if (terms.length >= safeLimit) break;
    const normalized = normalizeSearchText(candidate);
    if (!normalized || seen.has(normalized)) continue;
    const match = await getPool().query(`SELECT 1 FROM shop_products INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id WHERE shop_sites.status = 'online' AND shop_sites.type = 'cardShop' AND LOWER(CONCAT(shop_products.category_name, ' ', shop_products.name)) LIKE ? LIMIT 1`, [`%${normalized}%`]);
    if (match.rows.length) { terms.push(candidate.trim()); seen.add(normalized); }
  }
  return { terms, normalizedTerms: terms.map(normalizeSearchText) };
}

async function loadMySqlOfficialPriceCatalog(): Promise<PublicOfficialPriceCatalogRow[]> {
  const result = await getPool().query(`
    SELECT app_slug, plan_slug, MIN(app_name) AS app_name, MIN(plan_name) AS plan_name, MIN(display_name) AS display_name,
      MIN(url_slug) AS url_slug, MAX(is_default) AS is_default, MIN(display_order) AS display_order
    FROM official_prices WHERE trim(url_slug) <> '' AND lower(trim(url_slug)) NOT IN ('default', 'official-price') AND trim(display_name) <> ''
    GROUP BY app_slug, plan_slug ORDER BY display_order ASC
  `);
  return result.rows.map(row => ({ appSlug: String(row.app_slug), planSlug: String(row.plan_slug), appName: String(row.app_name), planName: String(row.plan_name), displayName: String(row.display_name), urlSlug: String(row.url_slug), isDefault: row.is_default === true || row.is_default === 1 || row.is_default === '1', displayOrder: Number(row.display_order) || 0 }));
}

export async function loadShopProductsData(options: { productLimit?: number; inStockOnly?: boolean } = {}): Promise<PublicShopProductsData> {
  return loadMySqlShopProductsData(options);
  const snapshot = await loadPublicSnapshot<{
    sites: PublicSiteRow[];
    products: PublicProductRow[];
    totalSiteCount: number;
    totalProductCount: number;
    totalInStockProductCount?: number;
    latestRefreshedAt?: string | null;
    latestRefreshTime: string;
    isPartial: boolean;
  }>('shop-products');
  const db = getPool();
  const safeProductLimit = typeof options.productLimit === 'number' && Number.isFinite(options.productLimit)
    ? Math.max(1, Math.floor(options.productLimit))
    : null;
  if (snapshot) {
    const normalizedSites = snapshot.sites.map(site => ({ ...site, sponsor: site.sponsor === true }));
    const sourceProducts = (options.inStockOnly
      ? snapshot.products.filter(product => product.inStock)
      : snapshot.products)
      .map(product => ({ ...product, siteSponsor: product.siteSponsor === true }));
    const products = safeProductLimit === null ? sourceProducts : sourceProducts.slice(0, safeProductLimit);
    const sites = safeProductLimit === null
      ? normalizedSites
      : (() => {
        const selectedSiteIds = new Set(products.map(product => product.siteId));
        return normalizedSites.filter(site => selectedSiteIds.has(site.id));
      })();
    const totalInStockProductCount = typeof snapshot.totalInStockProductCount === 'number'
      ? snapshot.totalInStockProductCount
      : snapshot.products.filter(product => product.inStock).length;
    const totalProductCount = snapshot.totalProductCount;
    const partialTotalCount = options.inStockOnly ? totalInStockProductCount : totalProductCount;
    return {
      ...snapshot,
      sites,
      products,
      totalProductCount,
      totalInStockProductCount,
      ...(safeProductLimit === null ? {} : { initialProductLimit: safeProductLimit }),
      isPartial: partialTotalCount > products.length,
    };
  }
  const sitesResult = safeProductLimit === null
    ? await db.query(`
      SELECT
        id,
        name,
        url,
        score,
        sponsor,
        last_product_refresh_success_at
      FROM shop_sites
      WHERE status = 'online'
        AND type = 'cardShop'
      ORDER BY sponsor DESC, score DESC, product_count DESC, in_stock_product_count DESC, last_product_refresh_success_at DESC, id ASC
    `)
    : null;
  const productsResult = await db.query(`
    WITH base_products AS (
      SELECT
        shop_products.id AS product_row_id,
        shop_products.site_id,
        shop_sites.name AS site_name,
        shop_sites.url AS site_url,
        shop_sites.score AS site_score,
        shop_sites.sponsor AS site_sponsor,
        shop_sites.last_product_refresh_success_at AS site_product_refresh_success_at,
        shop_products.category_name,
        shop_products.name,
        shop_products.price,
        shop_products.price_number,
        shop_products.price_unit,
        shop_products.product_url,
        shop_products.stock,
        shop_products.in_stock,
        shop_products.click_count,
        shop_products.score,
        shop_products.refreshed_at,
        ROW_NUMBER() OVER (
          ORDER BY shop_products.score DESC, shop_sites.score DESC, shop_products.in_stock DESC, shop_products.refreshed_at DESC, shop_products.category_name ASC, shop_products.name ASC
        ) AS natural_order
      FROM shop_products
      INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id
      WHERE shop_sites.status = 'online'
        AND shop_sites.type = 'cardShop'
        ${options.inStockOnly ? 'AND shop_products.in_stock = TRUE' : ''}
    ),
    sponsor_candidates AS (
      SELECT
        product_row_id,
        natural_order,
        ROW_NUMBER() OVER (PARTITION BY site_id ORDER BY natural_order ASC) AS sponsor_site_product_rank,
        MIN(natural_order) OVER (PARTITION BY site_id) AS sponsor_site_first_order
      FROM base_products
      WHERE site_sponsor = TRUE
    ),
    sponsor_pins AS (
      SELECT
        product_row_id,
        ROW_NUMBER() OVER (ORDER BY sponsor_site_product_rank ASC, sponsor_site_first_order ASC, natural_order ASC) AS sponsor_pin_rank
      FROM sponsor_candidates
      WHERE sponsor_site_product_rank <= 5
      ORDER BY sponsor_site_product_rank ASC, sponsor_site_first_order ASC, natural_order ASC
      LIMIT 10
    )
    SELECT
      base_products.site_id,
      base_products.site_name,
      base_products.site_url,
      base_products.site_score,
      base_products.site_sponsor,
      base_products.site_product_refresh_success_at,
      base_products.category_name,
      base_products.name,
      base_products.price,
      base_products.price_number,
      base_products.price_unit,
      base_products.product_url,
      base_products.stock,
      base_products.in_stock,
      base_products.click_count,
      base_products.score,
      base_products.refreshed_at
    FROM base_products
    LEFT JOIN sponsor_pins ON sponsor_pins.product_row_id = base_products.product_row_id
    ORDER BY
      CASE WHEN sponsor_pins.sponsor_pin_rank IS NULL THEN 1 ELSE 0 END ASC,
      sponsor_pins.sponsor_pin_rank ASC,
      base_products.natural_order ASC
    ${safeProductLimit ? 'LIMIT ?' : ''}
  `, safeProductLimit ? [safeProductLimit] : []);

  const products: PublicProductRow[] = productsResult.rows.map(row => {
    const refreshedAt = row.refreshed_at ? String(row.refreshed_at) : null;
    const siteProductRefreshSuccessAt = row.site_product_refresh_success_at ? String(row.site_product_refresh_success_at) : null;
    return {
      categoryName: String(row.category_name),
      name: String(row.name),
      price: String(row.price),
      priceNumber: typeof row.price_number === 'number' ? Number(row.price_number) : null,
      priceUnit: typeof row.price_unit === 'string' ? String(row.price_unit) : null,
      ...(row.product_url ? { productUrl: String(row.product_url) } : {}),
      ...(typeof row.stock === 'number' ? { stock: row.stock } : {}),
      inStock: row.in_stock === true || row.in_stock === 1 || row.in_stock === '1',
      refreshedAt,
      refreshTime: formatBeijingRefreshTime(refreshedAt),
      clickCount: Number(row.click_count) || 0,
      siteId: String(row.site_id),
      siteName: String(row.site_name),
      siteUrl: String(row.site_url),
      siteProductRefreshSuccessAt,
      siteProductRefreshSuccessTime: formatBeijingRefreshTime(siteProductRefreshSuccessAt),
      siteScore: Number(row.site_score) || 0,
      siteSponsor: row.site_sponsor === true || row.site_sponsor === 1 || row.site_sponsor === '1',
      score: Number(row.score) || 0,
    };
  });

  const sites: PublicSiteRow[] = sitesResult
    ? sitesResult.rows.map(row => ({
      id: String(row.id),
      name: String(row.name),
      url: String(row.url),
      lastProductRefreshSuccessAt: row.last_product_refresh_success_at ? String(row.last_product_refresh_success_at) : null,
      lastProductRefreshSuccessTime: formatBeijingRefreshTime(row.last_product_refresh_success_at ? String(row.last_product_refresh_success_at) : null),
      score: Number(row.score) || 0,
      sponsor: row.sponsor === true || row.sponsor === 1 || row.sponsor === '1',
    }))
    : (() => {
      const siteById = new Map<string, PublicSiteRow>();
      for (const row of productsResult.rows) {
        const siteId = String(row.site_id);
        if (siteById.has(siteId)) continue;
        const lastProductRefreshSuccessAt = row.site_product_refresh_success_at ? String(row.site_product_refresh_success_at) : null;
        siteById.set(siteId, {
          id: siteId,
          name: String(row.site_name),
          url: String(row.site_url),
          lastProductRefreshSuccessAt,
          lastProductRefreshSuccessTime: formatBeijingRefreshTime(lastProductRefreshSuccessAt),
          score: Number(row.site_score) || 0,
          sponsor: row.site_sponsor === true || row.site_sponsor === 1 || row.site_sponsor === '1',
        });
      }
      return [...siteById.values()];
    })();
  const summaryResult = await db.query(`
    SELECT
      SUM(status = 'online' AND type = 'cardShop') AS total_site_count,
      COALESCE((
        SELECT COUNT(*)
        FROM shop_products
        INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id
        WHERE shop_sites.status = 'online'
          AND shop_sites.type = 'cardShop'
      ), 0) AS total_product_count,
      COALESCE((
        SELECT COUNT(*)
        FROM shop_products
        INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id
        WHERE shop_sites.status = 'online'
          AND shop_sites.type = 'cardShop'
          AND shop_products.in_stock = TRUE
      ), 0) AS total_in_stock_product_count,
      MAX(CASE WHEN status = 'online' AND type = 'cardShop' THEN last_product_refresh_success_at END) AS latest_refreshed_at
    FROM shop_sites
  `);
  const summaryRow = summaryResult.rows[0] ?? {};
  const totalSiteCount = Number(summaryRow.total_site_count) || 0;
  const allProductCount = Number(summaryRow.total_product_count) || 0;
  const totalInStockProductCount = Number(summaryRow.total_in_stock_product_count) || 0;
  const totalProductCount = allProductCount;
  const partialTotalCount = options.inStockOnly ? totalInStockProductCount : totalProductCount;
  const latestRefreshedAt = summaryRow.latest_refreshed_at ? String(summaryRow.latest_refreshed_at) : null;

  return {
    sites,
    products,
    totalSiteCount,
    totalProductCount,
    totalInStockProductCount,
    latestRefreshedAt,
    latestRefreshTime: formatBeijingRefreshTime(latestRefreshedAt),
    isPartial: partialTotalCount > products.length,
  };
}

export async function loadPackedShopProductsSnapshot(): Promise<PackedShopProductsData | null> {
  return loadPublicSnapshot<PackedShopProductsData>('shop-products-packed');
}

export async function loadGatewaySites(options: PublicListLimitOptions = {}): Promise<PublicGatewaySitesData> {
  return loadMySqlGatewaySites(options);
  const limit = safeListLimit(options.limit);
  const snapshot = await loadPublicSnapshot<{
    sites: PublicGatewaySiteRow[];
    totalSiteCount: number;
    sitesWithPricesCount: number;
    totalModelCount: number;
    totalPriceCount: number;
  }>('gateway-sites');
  if (snapshot) {
    return {
      ...snapshot,
      sites: snapshot.sites
        .slice(0, limit ?? snapshot.sites.length)
        .map(site => ({ ...site, sponsor: site.sponsor === true })),
    };
  }

  const result = await getPool().query(`
    WITH price_summary AS (
      SELECT
        site_id,
        COUNT(DISTINCT model_id) AS model_count,
        COUNT(*) AS price_count,
        ARRAY_AGG(DISTINCT model_family ORDER BY model_family) FILTER (WHERE model_family <> '' AND model_family <> 'Other') AS model_families,
        MAX(fetched_at) AS latest_price_fetched_at
      FROM gateway_model_prices
      GROUP BY site_id
    )
    SELECT
      gateway_sites.site_id AS id,
      gateway_sites.name AS site_name,
      gateway_sites.url,
      gateway_sites.family,
      gateway_sites.score,
      gateway_sites.availability_percent,
      gateway_sites.avg_success_latency_ms,
      gateway_sites.created_at,
      gateway_sites.slug,
      gateway_sites.host,
      gateway_sites.summary,
      gateway_sites.invite_url,
      gateway_sites.sponsor,
      gateway_sites.model_types,
      gateway_sites.payment_methods,
      COALESCE(price_summary.model_count, 0) AS model_count,
      COALESCE(price_summary.price_count, 0) AS price_count,
      COALESCE(price_summary.model_families, ARRAY[]) AS model_families,
      CASE
        WHEN cardinality(COALESCE(price_summary.model_families, ARRAY[])) > 0
          THEN price_summary.model_families
        ELSE ARRAY(
          SELECT jsonb_array_elements_text(COALESCE(gateway_sites.model_types, '[]'))
        )
      END AS display_model_families,
      price_summary.latest_price_fetched_at AS latest_gateway_refresh_at
    FROM gateway_sites
    LEFT JOIN price_summary ON price_summary.site_id = gateway_sites.site_id
    WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway'
    ORDER BY gateway_sites.sponsor DESC, gateway_sites.score DESC, gateway_sites.weight DESC, gateway_sites.created_at DESC, gateway_sites.name ASC, gateway_sites.site_id ASC
    ${limit ? 'LIMIT ?' : ''}
  `, limit ? [limit] : []);

  const summaryResult = await getPool().query(`
    WITH price_summary AS (
      SELECT
        site_id,
        COUNT(DISTINCT model_id) AS model_count,
        COUNT(*) AS price_count
      FROM gateway_model_prices
      GROUP BY site_id
    ),
    online_sites AS (
      SELECT
        gateway_sites.site_id,
        COALESCE(price_summary.model_count, 0) AS model_count,
        COALESCE(price_summary.price_count, 0) AS price_count
      FROM gateway_sites
      LEFT JOIN price_summary ON price_summary.site_id = gateway_sites.site_id
      WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway'
    )
    SELECT
      COUNT(*) AS total_site_count,
      COUNT(*) FILTER (WHERE price_count > 0) AS sites_with_prices_count,
      COALESCE(SUM(model_count), 0) AS total_model_count,
      COALESCE(SUM(price_count), 0) AS total_price_count
    FROM online_sites
  `);
  const summaryRow = summaryResult.rows[0] ?? {};

  const sites: PublicGatewaySiteRow[] = result.rows.map(row => mapGatewaySiteRow(row));

  return {
    sites,
    totalSiteCount: Number(summaryRow.total_site_count) || 0,
    sitesWithPricesCount: Number(summaryRow.sites_with_prices_count) || 0,
    totalModelCount: Number(summaryRow.total_model_count) || 0,
    totalPriceCount: Number(summaryRow.total_price_count) || 0,
  };
}

export async function loadGatewayModels(options: PublicListLimitOptions = {}): Promise<PublicGatewayModelsData> {
  return loadMySqlGatewayModels(options);
  const limit = safeListLimit(options.limit);
  const snapshot = await loadPublicSnapshot<{
    models: PublicGatewayModelRow[];
    totalModelCount: number;
    totalSupportCount: number;
  }>('gateway-models');
  if (snapshot) {
    return {
      ...snapshot,
      models: snapshot.models.slice(0, limit ?? snapshot.models.length),
    };
  }

  const result = await getPool().query(`
    SELECT
      prices.model_id,
      COALESCE(NULLIF(prices.model_family, ''), 'Other') AS model_family,
      COUNT(DISTINCT prices.site_id) AS support_site_count,
      COUNT(*) AS price_count,
      MAX(prices.fetched_at) AS latest_gateway_refresh_at,
      MAX(gateway_sites.score) AS max_site_score
    FROM gateway_model_prices prices
    INNER JOIN gateway_sites ON gateway_sites.site_id = prices.site_id
    WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway'
    GROUP BY prices.model_id, COALESCE(NULLIF(prices.model_family, ''), 'Other')
    ORDER BY
      COUNT(DISTINCT prices.site_id) DESC,
      MAX(gateway_sites.score) DESC,
      prices.model_id ASC
    ${limit ? 'LIMIT ?' : ''}
  `, limit ? [limit] : []);

  const summaryResult = await getPool().query(`
    WITH grouped_models AS (
      SELECT
        prices.model_id,
        COALESCE(NULLIF(prices.model_family, ''), 'Other') AS model_family,
        COUNT(DISTINCT prices.site_id) AS support_site_count
      FROM gateway_model_prices prices
      INNER JOIN gateway_sites ON gateway_sites.site_id = prices.site_id
      WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway'
      GROUP BY prices.model_id, COALESCE(NULLIF(prices.model_family, ''), 'Other')
    )
    SELECT
      COUNT(*) AS total_model_count,
      COALESCE(SUM(support_site_count), 0) AS total_support_count
    FROM grouped_models
  `);
  const summaryRow = summaryResult.rows[0] ?? {};

  const models: PublicGatewayModelRow[] = result.rows.map(row => {
    const modelId = String(row.model_id);
    const latestGatewayRefreshAt = row.latest_gateway_refresh_at ? String(row.latest_gateway_refresh_at) : null;
    return {
      id: modelId,
      modelId,
      modelFamily: String(row.model_family || 'Other'),
      supportSiteCount: Number(row.support_site_count) || 0,
      priceCount: Number(row.price_count) || 0,
      latestGatewayRefreshAt,
      latestGatewayRefreshTime: formatBeijingRefreshTime(latestGatewayRefreshAt),
    };
  });

  return {
    models,
    totalModelCount: Number(summaryRow.total_model_count) || 0,
    totalSupportCount: Number(summaryRow.total_support_count) || 0,
  };
}

export async function loadGatewaySiteBySlug(slug: string): Promise<PublicGatewaySiteRow | null> {
  return loadMySqlGatewaySiteBySlug(slug);
  const normalizedSlug = slug.trim();
  if (!normalizedSlug) return null;
  const sitesSnapshot = await loadPublicSnapshot<{
    sites: PublicGatewaySiteRow[];
  }>('gateway-sites');
  const snapshotSite = sitesSnapshot?.sites.find(site => site.slug === normalizedSlug) ?? null;
  if (snapshotSite) return { ...snapshotSite, sponsor: snapshotSite.sponsor === true };

  const result = await getPool().query(`
    WITH price_summary AS (
      SELECT
        site_id,
        COUNT(DISTINCT model_id) AS model_count,
        COUNT(*) AS price_count,
        ARRAY_AGG(DISTINCT model_family ORDER BY model_family) FILTER (WHERE model_family <> '' AND model_family <> 'Other') AS model_families,
        MAX(fetched_at) AS latest_price_fetched_at
      FROM gateway_model_prices
      GROUP BY site_id
    )
    SELECT
      gateway_sites.site_id AS id,
      gateway_sites.name AS site_name,
      gateway_sites.url,
      gateway_sites.family,
      gateway_sites.score,
      gateway_sites.availability_percent,
      gateway_sites.avg_success_latency_ms,
      gateway_sites.created_at,
      gateway_sites.slug,
      gateway_sites.host,
      gateway_sites.summary,
      gateway_sites.invite_url,
      gateway_sites.sponsor,
      gateway_sites.model_types,
      gateway_sites.payment_methods,
      COALESCE(price_summary.model_count, 0) AS model_count,
      COALESCE(price_summary.price_count, 0) AS price_count,
      COALESCE(price_summary.model_families, ARRAY[]) AS model_families,
      CASE
        WHEN cardinality(COALESCE(price_summary.model_families, ARRAY[])) > 0
          THEN price_summary.model_families
        ELSE ARRAY(
          SELECT jsonb_array_elements_text(COALESCE(gateway_sites.model_types, '[]'))
        )
      END AS display_model_families,
      price_summary.latest_price_fetched_at AS latest_gateway_refresh_at
    FROM gateway_sites
    LEFT JOIN price_summary ON price_summary.site_id = gateway_sites.site_id
    WHERE gateway_sites.status = 'online'
      AND gateway_sites.type = 'gateway'
      AND gateway_sites.slug = ?
    LIMIT 1
  `, [normalizedSlug]);
  const row = result.rows[0];
  if (!row) return null;
  return mapGatewaySiteRow(row);
}

async function loadGatewayModelSummary(modelId: string): Promise<PublicGatewayModelRow | null> {
  return loadMySqlGatewayModelSummary(modelId);
  const normalizedModelId = modelId.trim();
  if (!normalizedModelId) return null;
  const modelsSnapshot = await loadPublicSnapshot<{
    models: PublicGatewayModelRow[];
  }>('gateway-models');
  const snapshotModel = modelsSnapshot?.models.find(model => model.modelId === normalizedModelId) ?? null;
  if (snapshotModel) return snapshotModel;

  const result = await getPool().query(`
    SELECT
      prices.model_id,
      COALESCE(NULLIF(prices.model_family, ''), 'Other') AS model_family,
      COUNT(DISTINCT prices.site_id) AS support_site_count,
      COUNT(*) AS price_count,
      MAX(prices.fetched_at) AS latest_gateway_refresh_at
    FROM gateway_model_prices prices
    INNER JOIN gateway_sites ON gateway_sites.site_id = prices.site_id
    WHERE gateway_sites.status = 'online'
      AND gateway_sites.type = 'gateway'
      AND prices.model_id = ?
    GROUP BY prices.model_id, COALESCE(NULLIF(prices.model_family, ''), 'Other')
    LIMIT 1
  `, [normalizedModelId]);
  const row = result.rows[0];
  if (!row) return null;
  const latestGatewayRefreshAt = row.latest_gateway_refresh_at ? String(row.latest_gateway_refresh_at) : null;
  return {
    id: String(row.model_id),
    modelId: String(row.model_id),
    modelFamily: String(row.model_family || 'Other'),
    supportSiteCount: Number(row.support_site_count) || 0,
    priceCount: Number(row.price_count) || 0,
    latestGatewayRefreshAt,
    latestGatewayRefreshTime: formatBeijingRefreshTime(latestGatewayRefreshAt),
  };
}

export async function loadGatewayDetail(slug: string, options: { priceLimit?: number } = {}): Promise<PublicGatewayDetail | null> {
  return loadMySqlGatewayDetail(slug, options);
  const site = await loadGatewaySiteBySlug(slug);
  if (!site) return null;
  const priceLimit = safeListLimit(options.priceLimit);

  const priceResult = await getPool().query(`
    SELECT
      prices.model_id,
      prices.unit,
      prices.input_price,
      prices.output_price,
      prices.cache_input_price,
      prices.cache_output_price
    FROM gateway_model_prices prices
    WHERE prices.site_id = ?
    ORDER BY
      CASE prices.model_family
        WHEN 'GPT' THEN 1
        WHEN 'Claude' THEN 2
        WHEN 'Gemini' THEN 3
        WHEN 'Qwen' THEN 4
        WHEN 'Grok' THEN 5
        ELSE 20
      END ASC,
      prices.model_id ASC,
      prices.unit ASC
    ${priceLimit ? 'LIMIT ?' : ''}
  `, priceLimit ? [site.id, priceLimit] : [site.id]);

  return {
    site,
    prices: priceResult.rows.map(row => ({
      modelId: String(row.model_id),
      unit: String(row.unit || ''),
      inputPrice: row.input_price == null ? null : Number(row.input_price),
      outputPrice: row.output_price == null ? null : Number(row.output_price),
      cacheInputPrice: row.cache_input_price == null ? null : Number(row.cache_input_price),
      cacheOutputPrice: row.cache_output_price == null ? null : Number(row.cache_output_price),
    })),
  };
}

export async function loadGatewayModelDetail(pathId: string, options: { siteLimit?: number } = {}): Promise<PublicGatewayModelDetail | null> {
  return loadMySqlGatewayModelDetail(pathId.trim(), options);
  const modelId = pathId.trim();
  if (!modelId) return null;
  const siteLimit = safeListLimit(options.siteLimit);

  const model = await loadGatewayModelSummary(modelId);
  if (!model) return null;

  const result = await getPool().query(`
    WITH model_price_summary AS (
      SELECT
        site_id,
        COUNT(*) AS price_count_for_model,
        ARRAY_AGG(DISTINCT unit ORDER BY unit) FILTER (WHERE unit <> '') AS units_for_model,
        jsonb_agg(
          jsonb_build_object(
            'unit', unit,
            'inputPrice', input_price,
            'outputPrice', output_price,
            'cacheInputPrice', cache_input_price,
            'cacheOutputPrice', cache_output_price
          )
          ORDER BY unit ASC, input_price ASC, output_price ASC
        ) AS prices_for_model,
        MAX(fetched_at) AS latest_model_refresh_at
      FROM gateway_model_prices
      WHERE model_id = ?
      GROUP BY site_id
    ),
    site_price_summary AS (
      SELECT
        site_id,
        COUNT(DISTINCT model_id) AS model_count,
        COUNT(*) AS price_count,
        ARRAY_AGG(DISTINCT model_family ORDER BY model_family) FILTER (WHERE model_family <> '' AND model_family <> 'Other') AS model_families,
        MAX(fetched_at) AS latest_price_fetched_at
      FROM gateway_model_prices
      GROUP BY site_id
    )
    SELECT
      gateway_sites.site_id AS id,
      gateway_sites.name AS site_name,
      gateway_sites.url,
      gateway_sites.family,
      gateway_sites.score,
      gateway_sites.availability_percent,
      gateway_sites.avg_success_latency_ms,
      gateway_sites.created_at,
      gateway_sites.slug,
      gateway_sites.host,
      gateway_sites.summary,
      gateway_sites.invite_url,
      gateway_sites.sponsor,
      gateway_sites.model_types,
      gateway_sites.payment_methods,
      COALESCE(site_price_summary.model_count, 0) AS model_count,
      COALESCE(site_price_summary.price_count, 0) AS price_count,
      COALESCE(site_price_summary.model_families, ARRAY[]) AS model_families,
      CASE
        WHEN cardinality(COALESCE(site_price_summary.model_families, ARRAY[])) > 0
          THEN site_price_summary.model_families
        ELSE ARRAY(
          SELECT jsonb_array_elements_text(COALESCE(gateway_sites.model_types, '[]'))
        )
      END AS display_model_families,
      site_price_summary.latest_price_fetched_at AS latest_gateway_refresh_at,
      model_price_summary.price_count_for_model,
      COALESCE(model_price_summary.units_for_model, ARRAY[]) AS units_for_model,
      COALESCE(model_price_summary.prices_for_model, '[]') AS prices_for_model,
      model_price_summary.latest_model_refresh_at
    FROM model_price_summary
    INNER JOIN gateway_sites ON gateway_sites.site_id = model_price_summary.site_id
    LEFT JOIN site_price_summary ON site_price_summary.site_id = gateway_sites.site_id
    WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway'
    ORDER BY gateway_sites.sponsor DESC, gateway_sites.score DESC, gateway_sites.weight DESC, gateway_sites.created_at DESC, gateway_sites.name ASC
    ${siteLimit ? 'LIMIT ?' : ''}
  `, siteLimit ? [modelId, siteLimit] : [modelId]);

  return {
    model,
    sites: result.rows.map(row => mapGatewayModelSiteRow(row, modelId)),
  };
}

function hostFromUrl(input: string) {
  try {
    return new URL(input).hostname;
  } catch {
    return input;
  }
}

export function normalizeSearchText(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, ' ');
}

export async function submitSiteUrl(input: string) {
  const validation = validatePublicSubmittedUrl(input);
  if (!validation.ok) {
    return { ok: false as const, errorKey: validation.reason satisfies SubmitSiteUrlErrorKey };
  }
  const url = validation.url;
  getPool();
  const id = createHash('sha256').update(`${url.replace(/#.*/, '').replace(/\/$/, '')}:2164802aa948726ee717662bcc17f7295e278340d9dcf4f0`).digest('hex');
  const [writeResult] = await pool!.execute(`INSERT IGNORE INTO shop_sites (id, url, status, family, type) VALUES (?, ?, 'accepted', 'unknown', 'unknown')`, [id, url]);
  return (writeResult as mysql.ResultSetHeader).affectedRows > 0
    ? { ok: true as const, url }
    : { ok: false as const, errorKey: 'duplicateUrl' satisfies SubmitSiteUrlErrorKey };

  const result = await getPool().query(
    `
      INSERT INTO shop_sites (id, url, status, family, type)
      VALUES (md5(regexp_replace(split_part(?, '#', 1), '/$', '') || ?), ?, 'accepted', 'unknown', 'unknown')
      ON CONFLICT (url) DO NOTHING
      RETURNING url
    `,
    [url, '2164802aa948726ee717662bcc17f7295e278340d9dcf4f0'],
  );
  if (result.rows.length === 0) {
    return { ok: false as const, errorKey: 'duplicateUrl' satisfies SubmitSiteUrlErrorKey };
  }
  return { ok: true as const, url };
}

const publicGatewayPaymentMethods = new Set([
  'alipay', 'wechat', 'visa', 'mastercard', 'stripe', 'paypal', 'tether', 'bitcoin', 'applepay', 'googlepay',
]);

function publicGatewaySlug(host: string) {
  const slug = host.toLowerCase().replace(/^www\./, '').replace(/\.[a-z]{2,}$/i, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  return slug || 'gateway';
}

export async function submitGatewaySite(input: { url: string; apiEndpoint?: string; name: string; summary: string; paymentMethods: string[] }) {
  const validation = validatePublicSubmittedUrl(input.url);
  if (!validation.ok) return { ok: false as const, errorKey: 'gatewayInvalidUrl' satisfies SubmitSiteUrlErrorKey };
  const apiEndpointInput = input.apiEndpoint?.trim() ?? '';
  let apiEndpoint = '';
  if (apiEndpointInput) {
    try {
      const parsedApiEndpoint = new URL(apiEndpointInput);
      if (parsedApiEndpoint.protocol !== 'http:' && parsedApiEndpoint.protocol !== 'https:') throw new Error('unsupported protocol');
      parsedApiEndpoint.hash = '';
      apiEndpoint = parsedApiEndpoint.toString().replace(/\/$/, '');
    } catch {
      return { ok: false as const, errorKey: 'gatewayInvalidApiEndpoint' satisfies SubmitSiteUrlErrorKey };
    }
  }
  const name = input.name.trim();
  const summary = input.summary.trim();
  const paymentMethods = [...new Set(input.paymentMethods.map(value => value.trim().toLowerCase()))].filter(value => publicGatewayPaymentMethods.has(value));
  if (!name) return { ok: false as const, errorKey: 'invalidGatewayName' as const };
  if (name.length > 20) return { ok: false as const, errorKey: 'gatewayNameTooLong' as const };
  if (summary.length > 150) return { ok: false as const, errorKey: 'gatewaySummaryTooLong' as const };
  const url = validation.url;
  getPool();
  const mysqlHost = new URL(url).hostname.toLowerCase().replace(/^www\./, '');
  const mysqlBaseSlug = publicGatewaySlug(mysqlHost);
  let mysqlSlug = mysqlBaseSlug;
  for (let index = 2; index <= 1000; index += 1) {
    if ((await getPool().query('SELECT 1 FROM gateway_sites WHERE slug = ? LIMIT 1', [mysqlSlug])).rows.length === 0) break;
    mysqlSlug = `${mysqlBaseSlug}-${index}`;
  }
  const mysqlId = createHash('sha256').update(`${url.replace(/#.*/, '').replace(/\/$/, '')}:2164802aa948726ee717662bcc17f7295e278340d9dcf4f0`).digest('hex');
  const [mysqlWriteResult] = await pool!.execute(`INSERT IGNORE INTO gateway_sites (site_id, url, api_endpoint, status, name, family, type, slug, host, weight, summary, payment_methods, created_at) VALUES (?, ?, ?, 'accepted', ?, NULL, 'unknown', ?, ?, 50, ?, ?, UTC_TIMESTAMP())`, [mysqlId, url, apiEndpoint, name, mysqlSlug, mysqlHost, summary, JSON.stringify(paymentMethods)]);
  return (mysqlWriteResult as mysql.ResultSetHeader).affectedRows > 0
    ? { ok: true as const, url }
    : { ok: false as const, errorKey: 'duplicateUrl' satisfies SubmitSiteUrlErrorKey };
  const host = new URL(url).hostname.toLowerCase().replace(/^www\./, '');
  const db = getPool();
  if ((await db.query('SELECT 1 FROM gateway_sites WHERE url = ? LIMIT 1', [url])).rows.length > 0) {
    return { ok: false as const, errorKey: 'duplicateUrl' satisfies SubmitSiteUrlErrorKey };
  }
  const baseSlug = publicGatewaySlug(host);
  let slug = baseSlug;
  for (let index = 2; index <= 1000; index += 1) {
    if ((await db.query('SELECT 1 FROM gateway_sites WHERE slug = ? LIMIT 1', [slug])).rows.length === 0) break;
    slug = `${baseSlug}-${index}`;
  }
  const result = await db.query(
    `INSERT INTO gateway_sites (url, api_endpoint, status, site_id, name, family, type, slug, host, weight, summary, payment_methods)
     VALUES (?, ?, 'accepted', md5(? || ?), ?, NULL, 'unknown', ?, ?, 50, ?, ?)
     ON CONFLICT (url) DO NOTHING RETURNING url`,
    [url, apiEndpoint, '2164802aa948726ee717662bcc17f7295e278340d9dcf4f0', name, slug, host, summary, JSON.stringify(paymentMethods)],
  );
  if (result.rows.length === 0) return { ok: false as const, errorKey: 'duplicateUrl' satisfies SubmitSiteUrlErrorKey };
  return { ok: true as const, url };
}

export async function recordSearchTerm(term: string, resultCount: number) {
  const normalized = normalizeSearchText(term);
  const safeResultCount = Number.isFinite(resultCount) ? Math.max(0, Math.floor(resultCount)) : 0;
  if (!normalized || normalized.length < 2) return { recorded: false };
  if (/^https?:\/\//i.test(normalized) || /\/shop\//i.test(normalized) || /[a-z0-9-]+(\.[a-z0-9-]+)+/i.test(normalized)) {
    return { recorded: false };
  }

  getPool();
  await pool!.execute(`INSERT INTO shop_search_terms (term, total_count, result_count, last_seen_at) VALUES (?, 1, ?, UTC_TIMESTAMP()) ON DUPLICATE KEY UPDATE total_count = total_count + 1, result_count = VALUES(result_count), last_seen_at = UTC_TIMESTAMP()`, [normalized, safeResultCount]);
  return { recorded: true };

  await getPool().query(
    `
      INSERT INTO shop_search_terms (term, total_count, result_count, last_seen_at)
      VALUES (?, 1, ?, now())
      ON CONFLICT (term) DO UPDATE SET
        total_count = shop_search_terms.total_count + 1,
        result_count = EXCLUDED.result_count,
        last_seen_at = now()
    `,
    [normalized, safeResultCount],
  );
  return { recorded: true };
}

export async function recordProductClick(input: ProductClickInput) {
  const siteId = input.siteId.trim();
  const productUrl = input.productUrl?.trim() ?? '';
  const categoryName = input.categoryName?.trim() ?? '';
  const name = input.name?.trim() ?? '';
  if (!siteId) return { recorded: false as const };
  if (!productUrl && (!categoryName || !name)) return { recorded: false as const };

  const mysqlMatch = await getPool().query(`SELECT shop_products.id FROM shop_products INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id WHERE shop_products.site_id = ? AND shop_sites.status = 'online' AND shop_sites.type = 'cardShop' AND ((? <> '' AND shop_products.product_url = ?) OR (? = '' AND shop_products.category_name = ? AND shop_products.name = ?)) ORDER BY shop_products.refreshed_at DESC, shop_products.name ASC LIMIT 1`, [siteId, productUrl, productUrl, productUrl, categoryName, name]);
  if (!mysqlMatch.rows[0]) return { recorded: false as const };
  getPool();
  await pool!.execute('UPDATE shop_products SET click_count = click_count + 1 WHERE id = ?', [mysqlMatch.rows[0].id]);
  return { recorded: true as const };

  const result = await getPool().query(
    `
      UPDATE shop_products
      SET click_count = click_count + 1
      WHERE ctid IN (
        SELECT shop_products.ctid
        FROM shop_products
        INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id
        WHERE shop_products.site_id = ?
          AND shop_sites.status = 'online'
          AND shop_sites.type = 'cardShop'
          AND (
            (? <> '' AND shop_products.product_url = ?)
            OR (? = '' AND shop_products.category_name = ? AND shop_products.name = ?)
          )
        ORDER BY shop_products.refreshed_at DESC, shop_products.name ASC
        LIMIT 1
      )
      RETURNING site_id
    `,
    [siteId, productUrl, categoryName, name],
  );
  return { recorded: result.rows.length > 0 };
}

export async function loadPopularSearchTerms(limit = 10, presetPopularSearchTerms: string[] = []) {
  const mysqlSnapshot = await loadPublicSnapshot<PopularSearchTermsSnapshot>('popular-search-terms');
  if (mysqlSnapshot && mysqlSnapshot.terms.length >= limit) {
    const terms = mysqlSnapshot.terms.slice(0, Math.max(1, Math.min(30, Math.floor(limit))));
    return { terms, normalizedTerms: terms.map(normalizeSearchText) };
  }
  return loadMySqlPopularSearchTerms(limit, presetPopularSearchTerms);
  const safeLimit = Math.max(1, Math.min(30, Math.floor(limit)));
  const snapshot = await loadPublicSnapshot<PopularSearchTermsSnapshot>('popular-search-terms');
  if (snapshot && snapshot.terms.length >= safeLimit) {
    const terms = snapshot.terms.slice(0, safeLimit);
    return {
      terms,
      normalizedTerms: terms.map(normalizeSearchText),
    };
  }
  const db = getPool();
  const runtimeResult = await db.query(
    `
      SELECT
        shop_search_terms.term,
        shop_search_terms.total_count,
        shop_search_terms.last_seen_at
      FROM shop_search_terms
      WHERE shop_search_terms.total_count > 0
        AND shop_search_terms.result_count > 0
      ORDER BY shop_search_terms.total_count DESC, shop_search_terms.result_count DESC, shop_search_terms.last_seen_at DESC, shop_search_terms.term ASC
      LIMIT ?
    `,
    [safeLimit],
  );
  const runtimeTerms = runtimeResult.rows.map(row => String(row.term));
  const seen = new Set(runtimeTerms.map(normalizeSearchText));
  const remaining = Math.max(0, safeLimit - runtimeTerms.length);
  if (remaining === 0) {
    return {
      terms: runtimeTerms,
      normalizedTerms: runtimeTerms.map(normalizeSearchText),
    };
  }

  const presetResult = await db.query(
    `
      WITH candidate_terms AS (
        SELECT DISTINCT ON (lower(trim(term))) trim(term) AS term, lower(trim(term)) AS normalized_term, ordinality
        FROM unnest(?) WITH ORDINALITY AS input_terms(term, ordinality)
        WHERE trim(term) <> ''
        ORDER BY lower(trim(term)), ordinality ASC
      )
      SELECT candidate_terms.term
      FROM candidate_terms
      INNER JOIN shop_products ON lower(shop_products.category_name || ' ' || shop_products.name) LIKE '%' || candidate_terms.normalized_term || '%'
      INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id
        AND shop_sites.status = 'online'
        AND shop_sites.type = 'cardShop'
      GROUP BY candidate_terms.term, candidate_terms.ordinality
      HAVING COUNT(shop_products.*) > 0
      ORDER BY candidate_terms.ordinality ASC
      LIMIT ?
    `,
    [presetPopularSearchTerms, remaining],
  );
  const mergedTerms = runtimeTerms.slice();
  for (const row of presetResult.rows) {
    const term = String(row.term);
    const normalized = normalizeSearchText(term);
    if (seen.has(normalized)) continue;
    seen.add(normalized);
    mergedTerms.push(term);
  }
  return {
    terms: mergedTerms.slice(0, safeLimit),
    normalizedTerms: mergedTerms.slice(0, safeLimit).map(normalizeSearchText),
  };
}

export type PublicOfficialPriceRow = {
  appSlug: string;
  planSlug: string;
  appName: string;
  planName: string;
  displayName: string;
  urlSlug: string;
  isDefault: boolean;
  displayOrder: number;
  countryCode: string;
  countryLabel: string;
  currencyCode: string;
  priceText: string;
  priceValue: number;
  cnyPrice: number;
  usdPrice: number;
  rubPrice: number;
  fetchedAt: string;
};

export type PublicModelLeaderboardRow = {
  taskSlug: string;
  sourceName: string;
  sourceUrl: string;
  sourceGroupSlug: string;
  sourceBoardSlug: string;
  rank: number;
  modelName: string;
  score: number;
  fetchedAt: string;
};

export type PublicOfficialPriceCatalogRow = {
  appSlug: string;
  planSlug: string;
  appName: string;
  planName: string;
  displayName: string;
  urlSlug: string;
  isDefault: boolean;
  displayOrder: number;
};

function mapOfficialPriceRow(row: Record<string, unknown>): PublicOfficialPriceRow {
  return {
    appSlug: String(row.app_slug),
    planSlug: String(row.plan_slug),
    appName: String(row.app_name),
    planName: String(row.plan_name),
    displayName: String(row.display_name),
    urlSlug: String(row.url_slug),
    isDefault: Boolean(row.is_default),
    displayOrder: Number(row.display_order) || 0,
    countryCode: String(row.country_code),
    countryLabel: String(row.country_label),
    currencyCode: String(row.currency_code),
    priceText: String(row.price_text),
    priceValue: Number(row.price_value),
    cnyPrice: Number(row.cny_price),
    usdPrice: Number(row.usd_price),
    rubPrice: Number(row.rub_price),
    fetchedAt: String(row.fetched_at),
  };
}

export async function loadOfficialPriceCatalog(): Promise<PublicOfficialPriceCatalogRow[]> {
  const mysqlCatalogSnapshot = await loadPublicSnapshot<PublicOfficialPriceCatalogRow[]>('official-price-catalog');
  if (mysqlCatalogSnapshot) return mysqlCatalogSnapshot;
  return loadMySqlOfficialPriceCatalog();
  const snapshot = await loadPublicSnapshot<PublicOfficialPriceCatalogRow[]>('official-price-catalog');
  if (snapshot) return snapshot;

  const result = await getPool().query(`
    SELECT DISTINCT ON (app_slug, plan_slug)
      app_slug,
      plan_slug,
      app_name,
      plan_name,
      display_name,
      url_slug,
      is_default,
      display_order
    FROM official_prices
    WHERE trim(url_slug) <> ''
      AND lower(trim(url_slug)) NOT IN ('default', 'official-price')
      AND trim(display_name) <> ''
    ORDER BY app_slug, plan_slug, display_order ASC
  `);
  return result.rows.map(row => ({
    appSlug: String(row.app_slug),
    planSlug: String(row.plan_slug),
    appName: String(row.app_name),
    planName: String(row.plan_name),
    displayName: String(row.display_name),
    urlSlug: String(row.url_slug),
    isDefault: Boolean(row.is_default),
    displayOrder: Number(row.display_order) || 0,
  }));
}

export async function loadOfficialPricesByUrlSlug(urlSlug: string): Promise<PublicOfficialPriceRow[]> {
  const normalizedSlug = urlSlug.trim().toLowerCase();
  const snapshot = await loadPublicSnapshot<PublicOfficialPriceRow[]>('official-prices');
  if (snapshot) {
    return snapshot
      .filter(row => row.urlSlug.trim().toLowerCase() === normalizedSlug)
      .sort((a, b) => a.cnyPrice - b.cnyPrice);
  }

  const result = await getPool().query(`
    SELECT app_slug, plan_slug, app_name, plan_name, display_name, url_slug, is_default, display_order, country_code, country_label, currency_code, price_text, price_value, cny_price, usd_price, rub_price, fetched_at
    FROM official_prices
    WHERE lower(trim(url_slug)) = ?
    ORDER BY cny_price ASC
  `, [normalizedSlug]);
  return result.rows.map(mapOfficialPriceRow);
}

export async function loadOfficialPrices(): Promise<PublicOfficialPriceRow[]> {
  const snapshot = await loadPublicSnapshot<PublicOfficialPriceRow[]>('official-prices');
  if (snapshot) return snapshot;

  const db = getPool();
  const result = await db.query(`
    SELECT app_slug, plan_slug, app_name, plan_name, display_name, url_slug, is_default, display_order, country_code, country_label, currency_code, price_text, price_value, cny_price, usd_price, rub_price, fetched_at
    FROM official_prices
    ORDER BY display_order ASC, cny_price ASC
  `);
  return result.rows.map(row => mapOfficialPriceRow(row));
}

export async function loadModelLeaderboardTaskSlugs(): Promise<string[]> {
  const snapshot = await loadPublicSnapshot<string[]>('model-leaderboard-task-slugs');
  if (snapshot) return snapshot;

  const result = await getPool().query(`
    SELECT task_slug
    FROM model_leaderboards
    GROUP BY task_slug
    ORDER BY
      CASE task_slug
        WHEN 'coding' THEN 1
        WHEN 'creative-writing' THEN 2
        WHEN 'math' THEN 3
        WHEN 'text-to-image' THEN 4
        ELSE 999
      END ASC,
      task_slug ASC
  `);
  return result.rows.map(row => String(row.task_slug));
}

export async function loadModelLeaderboardRowsForTask(taskSlug: string, options: PublicListLimitOptions = {}): Promise<PublicModelLeaderboardRow[]> {
  const normalizedTaskSlug = taskSlug.trim().toLowerCase();
  const limit = safeListLimit(options.limit);
  const snapshot = await loadPublicSnapshot<PublicModelLeaderboardRow[]>('model-leaderboards');
  if (snapshot) {
    return snapshot
      .filter(row => row.taskSlug.trim().toLowerCase() === normalizedTaskSlug)
      .sort((a, b) => a.rank - b.rank)
      .slice(0, limit ?? snapshot.length);
  }

  const result = await getPool().query(`
    SELECT
      task_slug,
      source_name,
      source_url,
      source_group_slug,
      source_board_slug,
      rank,
      model_name,
      score,
      fetched_at
    FROM model_leaderboards
    WHERE lower(trim(task_slug)) = ?
    ORDER BY rank ASC
    ${limit ? 'LIMIT ?' : ''}
  `, limit ? [normalizedTaskSlug, limit] : [normalizedTaskSlug]);
  return result.rows.map(mapModelLeaderboardRow);
}

export async function loadModelLeaderboardRowsForTaskPage(taskSlug: string, options: PublicListLimitOptions = {}) {
  const mysqlTaskSlug = taskSlug.trim().toLowerCase();
  const mysqlLimit = safeListLimit(options.limit);
  const mysqlRows = await getPool().query(`
    SELECT task_slug, source_name, source_url, source_group_slug, source_board_slug, rank, model_name, score, fetched_at
    FROM model_leaderboards WHERE lower(trim(task_slug)) = ? ORDER BY rank ASC
  `, [mysqlTaskSlug]);
  const mysqlMappedRows = mysqlRows.rows.map(mapModelLeaderboardRow);
  const mysqlLatestFetchedAt = mysqlMappedRows.reduce<string | null>((latest, row) => !latest || new Date(row.fetchedAt).getTime() > new Date(latest).getTime() ? row.fetchedAt : latest, null);
  return { rows: mysqlMappedRows.slice(0, mysqlLimit ?? mysqlMappedRows.length), totalCount: mysqlMappedRows.length, latestFetchedAt: mysqlLatestFetchedAt };
  const normalizedTaskSlug = taskSlug.trim().toLowerCase();
  const limit = safeListLimit(options.limit);
  const snapshot = await loadPublicSnapshot<PublicModelLeaderboardRow[]>('model-leaderboards');
  if (snapshot) {
    const rows = snapshot
      .filter(row => row.taskSlug.trim().toLowerCase() === normalizedTaskSlug)
      .sort((a, b) => a.rank - b.rank);
    const latestFetchedAt = rows.reduce<string | null>((latest, row) => {
      if (!latest) return row.fetchedAt;
      return new Date(row.fetchedAt).getTime() > new Date(latest).getTime() ? row.fetchedAt : latest;
    }, null);
    return {
      rows: rows.slice(0, limit ?? rows.length),
      totalCount: rows.length,
      latestFetchedAt,
    };
  }

  const result = await getPool().query(`
    SELECT
      task_slug,
      source_name,
      source_url,
      source_group_slug,
      source_board_slug,
      rank,
      model_name,
      score,
      fetched_at,
      COUNT(*) OVER() AS total_count,
      MAX(fetched_at) OVER() AS latest_fetched_at
    FROM model_leaderboards
    WHERE lower(trim(task_slug)) = ?
    ORDER BY rank ASC
    ${limit ? 'LIMIT ?' : ''}
  `, limit ? [normalizedTaskSlug, limit] : [normalizedTaskSlug]);
  const firstRow = result.rows[0] ?? {};
  return {
    rows: result.rows.map(mapModelLeaderboardRow),
    totalCount: Number(firstRow.total_count) || 0,
    latestFetchedAt: firstRow.latest_fetched_at ? String(firstRow.latest_fetched_at) : null,
  };
}

function mapModelLeaderboardRow(row: Record<string, unknown>): PublicModelLeaderboardRow {
  return {
    taskSlug: String(row.task_slug),
    sourceName: String(row.source_name),
    sourceUrl: String(row.source_url),
    sourceGroupSlug: String(row.source_group_slug),
    sourceBoardSlug: String(row.source_board_slug),
    rank: Number(row.rank),
    modelName: String(row.model_name),
    score: Number(row.score),
    fetchedAt: String(row.fetched_at),
  };
}

export async function loadModelLeaderboards(): Promise<PublicModelLeaderboardRow[]> {
  const snapshot = await loadPublicSnapshot<PublicModelLeaderboardRow[]>('model-leaderboards');
  if (snapshot) return snapshot;

  const db = getPool();
  const result = await db.query(`
    SELECT
      task_slug,
      source_name,
      source_url,
      source_group_slug,
      source_board_slug,
      rank,
      model_name,
      score,
      fetched_at
    FROM model_leaderboards
    ORDER BY
      CASE task_slug
        WHEN 'coding' THEN 1
        WHEN 'creative-writing' THEN 2
        WHEN 'math' THEN 3
        WHEN 'text-to-image' THEN 4
        ELSE 999
      END ASC,
      rank ASC
  `);
  return result.rows.map(row => mapModelLeaderboardRow(row));
}

