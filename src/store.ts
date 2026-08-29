/**
 * 文件说明: 负责公开站点首页的数据读取、提交入库和搜索行为持久化。
 */
import 'dotenv/config';
import { createHash } from 'node:crypto';
import mysql from 'mysql2/promise';
import { aggregateCatalogProducts, catalogProductSlugsForTarget } from './catalog.js';
import { mergeModelLeaderboardTaskSlugs } from './model-leaderboard.js';
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
  availabilityPercent: number | null;
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
  sampledAt: string | null;
  isSample: boolean;
  sourceName: string;
  sourcePageUrl: string;
  region: string;
  benefitText: string;
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
  id?: string;
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
  standardProduct?: string;
  platform?: string;
  productType?: string;
  currencyCode?: string;
  channelCount?: number | null;
  availableChannelCount?: number | null;
  outOfStockChannelCount?: number | null;
  sampledAt?: string | null;
  isSample?: boolean;
  sourceName?: string;
  sourcePageUrl?: string;
  sourcePriority?: number;
  channelDetails?: Array<{
    siteId: string;
    siteName: string;
    inStock: boolean;
    price: string;
    priceNumber: number | null;
    priceUnit: string | null;
    sampledAt: string | null;
    isSample: boolean;
  }>;
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
  | 'homepage-announcement'
  | 'official-price-catalog'
  | 'official-prices'
  | 'model-leaderboard-task-slugs'
  | 'model-leaderboards';

type PublicListLimitOptions = {
  limit?: number;
  /** Explicit observed gateway model-family filter for /llm-gateway?model=. */
  modelFamily?: string;
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
    const payload = result.rows[0]?.payload;
    if (payload == null) return null;
    return (typeof payload === 'string' ? JSON.parse(payload) : payload) as T;
  } catch (error) {
    if (typeof error === 'object' && error && 'code' in error && (error.code === '42P01' || error.code === 'ER_NO_SUCH_TABLE')) {
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
  const url = row.url == null ? '' : String(row.url).trim();
  const inviteUrl = row.invite_url ? String(row.invite_url).trim() : '';
  const isSample = row.is_sample === true || row.is_sample === 1 || row.is_sample === '1';
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
    availabilityPercent: isSample || row.availability_percent == null ? null : Number(row.availability_percent),
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
    sampledAt: row.sampled_at ? String(row.sampled_at) : null,
    isSample,
    sourceName: String(row.source_name || ''),
    sourcePageUrl: String(row.source_page_url || ''),
    region: String(row.region || ''),
    benefitText: String(row.benefit_text || ''),
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

function mapMySqlGatewaySiteRow(row: Record<string, unknown>) {
  const site = mapGatewaySiteRow(row);
  return {
    ...site,
    displayModelFamilies: site.modelFamilies.length > 0 ? site.modelFamilies : site.modelTypes,
  };
}

async function mysqlGatewaySiteRows(options: { slug?: string; modelId?: string; modelFamily?: string; limit?: number | null } = {}) {
  const values: unknown[] = [];
  let modelFilter = '';
  if (options.modelId) {
    modelFilter = ' AND EXISTS (SELECT 1 FROM gateway_model_coverage coverage WHERE coverage.site_id = gateway_sites.site_id AND coverage.model_id = ?)';
    values.push(options.modelId);
  }
  const normalizedModelFamily = options.modelFamily?.trim().toLowerCase();
  if (normalizedModelFamily) {
    modelFilter += ` AND EXISTS (
      SELECT 1 FROM gateway_model_coverage coverage
      WHERE coverage.site_id = gateway_sites.site_id
        AND LOWER(TRIM(COALESCE(coverage.model_family, ''))) = ?
    )`;
    values.push(normalizedModelFamily);
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
      gateway_sites.region,
      gateway_sites.benefit_text,
      gateway_sites.sponsor,
      gateway_sites.model_types,
      gateway_sites.payment_methods,
      gateway_sites.sampled_at,
      gateway_sites.is_sample,
      reference_data_sources.name AS source_name,
      reference_data_sources.source_page_url,
      COALESCE(coverage_summary.model_count, 0) AS model_count,
      COALESCE(price_summary.price_count, 0) AS price_count,
      COALESCE(coverage_summary.model_families, '') AS model_families,
      COALESCE(GREATEST(coverage_summary.latest_gateway_refresh_at, price_summary.latest_gateway_refresh_at), coverage_summary.latest_gateway_refresh_at, price_summary.latest_gateway_refresh_at) AS latest_gateway_refresh_at
    FROM gateway_sites
    LEFT JOIN reference_data_sources ON reference_data_sources.id = gateway_sites.source_id
    LEFT JOIN (
      SELECT site_id, COUNT(DISTINCT model_id) AS model_count,
        COALESCE(GROUP_CONCAT(DISTINCT NULLIF(model_family, '') ORDER BY model_family SEPARATOR ','), '') AS model_families,
        MAX(observed_at) AS latest_gateway_refresh_at
      FROM gateway_model_coverage
      GROUP BY site_id
    ) AS coverage_summary ON coverage_summary.site_id = gateway_sites.site_id
    LEFT JOIN (
      SELECT site_id, COUNT(*) AS price_count, MAX(fetched_at) AS latest_gateway_refresh_at
      FROM gateway_model_prices
      WHERE input_price IS NOT NULL OR output_price IS NOT NULL OR cache_input_price IS NOT NULL OR cache_output_price IS NOT NULL
      GROUP BY site_id
    ) AS price_summary ON price_summary.site_id = gateway_sites.site_id
    WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway'${modelFilter}
    ORDER BY gateway_sites.score DESC, COALESCE(coverage_summary.model_count, 0) DESC, gateway_sites.name ASC
    ${options.limit ? 'LIMIT ?' : ''}
  `, options.limit ? [...values, options.limit] : values);
  return result.rows.map(mapMySqlGatewaySiteRow);
}

type ShopProductsOptions = { productLimit?: number; inStockOnly?: boolean; target?: string };

function applyCatalogTarget(products: PublicProductRow[], target: string | undefined) {
  const normalized = String(target || '').trim();
  if (!normalized) return products;
  const slugs = catalogProductSlugsForTarget(normalized);
  return products.filter(product => slugs.includes(String(product.standardProduct || '')));
}

async function loadMySqlShopProductsData(options: ShopProductsOptions): Promise<PublicShopProductsData> {
  const limit = typeof options.productLimit === 'number' && Number.isFinite(options.productLimit) ? Math.max(1, Math.floor(options.productLimit)) : null;
  const productsResult = await getPool().query(`
    SELECT
      shop_products.site_id, shop_sites.name AS site_name, shop_sites.url AS site_url,
      shop_sites.score AS site_score, shop_sites.sponsor AS site_sponsor,
      shop_sites.last_product_refresh_success_at AS site_product_refresh_success_at,
      shop_products.category_name, shop_products.name, shop_products.price, shop_products.price_number,
      shop_products.price_unit, shop_products.product_url, shop_products.stock, shop_products.in_stock,
      shop_products.click_count, shop_products.score, shop_products.refreshed_at, shop_products.standard_product,
      shop_products.platform, shop_products.product_type, shop_products.currency_code, shop_products.channel_count,
      shop_products.available_channel_count, shop_products.out_of_stock_channel_count, shop_products.sampled_at,
      shop_products.is_sample, reference_data_sources.name AS source_name, reference_data_sources.source_page_url,
      reference_data_sources.priority AS source_priority
    FROM shop_products
    INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id
    LEFT JOIN reference_data_sources ON reference_data_sources.id = shop_products.source_id
    WHERE shop_sites.status = 'online' AND shop_sites.type = 'cardShop'
    ORDER BY shop_sites.sponsor DESC, shop_products.score DESC, shop_sites.score DESC, shop_products.in_stock DESC,
      shop_products.refreshed_at DESC, shop_products.category_name ASC, shop_products.name ASC
  `);
  const rawProducts: PublicProductRow[] = productsResult.rows.map(row => {
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
      standardProduct: String(row.standard_product || ''), platform: String(row.platform || ''), productType: String(row.product_type || ''),
      currencyCode: String(row.currency_code || ''), channelCount: row.channel_count == null ? null : Number(row.channel_count),
      availableChannelCount: row.available_channel_count == null ? null : Number(row.available_channel_count),
      outOfStockChannelCount: row.out_of_stock_channel_count == null ? null : Number(row.out_of_stock_channel_count),
      sampledAt: row.sampled_at ? String(row.sampled_at) : null,
      isSample: row.is_sample === true || row.is_sample === 1 || row.is_sample === '1', sourceName: String(row.source_name || ''), sourcePageUrl: String(row.source_page_url || ''), sourcePriority: Number(row.source_priority) || 0,
    };
  });
  const aggregateProducts = applyCatalogTarget(aggregateCatalogProducts(rawProducts), options.target);
  const products = limit ? aggregateProducts.slice(0, limit) : aggregateProducts;
  const sitesResult = await getPool().query(`SELECT id, name, url, score, sponsor, last_product_refresh_success_at FROM shop_sites WHERE status = 'online' AND type = 'cardShop' ORDER BY sponsor DESC, score DESC, product_count DESC, in_stock_product_count DESC, last_product_refresh_success_at DESC, id ASC`);
  const summaryResult = await getPool().query(`
    SELECT COUNT(*) AS total_site_count,
      MAX(last_product_refresh_success_at) AS latest_refreshed_at
    FROM shop_sites WHERE status = 'online' AND type = 'cardShop'
  `);
  const summary = summaryResult.rows[0] ?? {};
  return {
    sites: sitesResult.rows.map(row => { const at = row.last_product_refresh_success_at ? String(row.last_product_refresh_success_at) : null; return { id: String(row.id || ''), name: String(row.name || ''), url: String(row.url || ''), lastProductRefreshSuccessAt: at, lastProductRefreshSuccessTime: formatBeijingRefreshTime(at), score: Number(row.score) || 0, sponsor: row.sponsor === true || row.sponsor === 1 || row.sponsor === '1' }; }),
    products, totalSiteCount: Number(summary.total_site_count) || 0, totalProductCount: aggregateProducts.length,
    totalInStockProductCount: aggregateProducts.filter(product => product.inStock).length, latestRefreshedAt: summary.latest_refreshed_at ? String(summary.latest_refreshed_at) : null,
    latestRefreshTime: formatBeijingRefreshTime(summary.latest_refreshed_at ? String(summary.latest_refreshed_at) : null),
    isPartial: aggregateProducts.length > products.length,
  };
}

async function loadMySqlGatewaySites(options: PublicListLimitOptions): Promise<PublicGatewaySitesData> {
  const limit = safeListLimit(options.limit);
  const normalizedModelFamily = options.modelFamily?.trim().toLowerCase();
  const sites = await mysqlGatewaySiteRows({ limit, modelFamily: normalizedModelFamily });
  const modelFamilyCondition = normalizedModelFamily ? ` AND EXISTS (
    SELECT 1 FROM gateway_model_coverage filtered_coverage
    WHERE filtered_coverage.site_id = gateway_sites.site_id
      AND LOWER(TRIM(COALESCE(filtered_coverage.model_family, ''))) = ?
  )` : '';
  const summaryResult = await getPool().query(`
    SELECT COUNT(*) AS total_site_count, COALESCE(SUM(price_count > 0), 0) AS sites_with_prices_count,
      COALESCE(SUM(model_count), 0) AS total_model_count, COALESCE(SUM(price_count), 0) AS total_price_count
    FROM (
      SELECT gateway_sites.site_id, COUNT(DISTINCT coverage.model_id) AS model_count,
        COUNT(DISTINCT CASE WHEN prices.input_price IS NOT NULL OR prices.output_price IS NOT NULL OR prices.cache_input_price IS NOT NULL OR prices.cache_output_price IS NOT NULL THEN prices.id END) AS price_count
      FROM gateway_sites
      LEFT JOIN gateway_model_coverage coverage ON coverage.site_id = gateway_sites.site_id
      LEFT JOIN gateway_model_prices prices ON prices.site_id = gateway_sites.site_id
      WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway'${modelFamilyCondition}
      GROUP BY gateway_sites.site_id
    ) AS online_sites
  `, normalizedModelFamily ? [normalizedModelFamily] : []);
  const summary = summaryResult.rows[0] ?? {};
  return { sites, totalSiteCount: Number(summary.total_site_count) || 0, sitesWithPricesCount: Number(summary.sites_with_prices_count) || 0, totalModelCount: Number(summary.total_model_count) || 0, totalPriceCount: Number(summary.total_price_count) || 0 };
}

async function loadMySqlGatewayModels(options: PublicListLimitOptions): Promise<PublicGatewayModelsData> {
  const limit = safeListLimit(options.limit);
  const result = await getPool().query(`
    SELECT coverage.model_id, COALESCE(NULLIF(coverage.model_family, ''), 'Other') AS model_family,
      COUNT(DISTINCT coverage.site_id) AS support_site_count,
      COUNT(DISTINCT CASE WHEN prices.input_price IS NOT NULL OR prices.output_price IS NOT NULL OR prices.cache_input_price IS NOT NULL OR prices.cache_output_price IS NOT NULL THEN prices.id END) AS price_count,
      MAX(COALESCE(prices.fetched_at, coverage.observed_at)) AS latest_gateway_refresh_at, MAX(gateway_sites.score) AS max_site_score
    FROM gateway_model_coverage coverage
    INNER JOIN gateway_sites ON gateway_sites.site_id = coverage.site_id
    LEFT JOIN gateway_model_prices prices ON prices.site_id = coverage.site_id AND prices.model_id = coverage.model_id
    WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway'
    GROUP BY coverage.model_id, COALESCE(NULLIF(coverage.model_family, ''), 'Other')
    ORDER BY support_site_count DESC, max_site_score DESC, coverage.model_id ASC ${limit ? 'LIMIT ?' : ''}
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
    SELECT coverage.model_id, COALESCE(NULLIF(coverage.model_family, ''), 'Other') AS model_family,
      COUNT(DISTINCT coverage.site_id) AS support_site_count,
      COUNT(DISTINCT CASE WHEN prices.input_price IS NOT NULL OR prices.output_price IS NOT NULL OR prices.cache_input_price IS NOT NULL OR prices.cache_output_price IS NOT NULL THEN prices.id END) AS price_count,
      MAX(COALESCE(prices.fetched_at, coverage.observed_at)) AS latest_gateway_refresh_at
    FROM gateway_model_coverage coverage
    INNER JOIN gateway_sites ON gateway_sites.site_id = coverage.site_id
    LEFT JOIN gateway_model_prices prices ON prices.site_id = coverage.site_id AND prices.model_id = coverage.model_id
    WHERE gateway_sites.status = 'online' AND gateway_sites.type = 'gateway' AND coverage.model_id = ?
    GROUP BY coverage.model_id, COALESCE(NULLIF(coverage.model_family, ''), 'Other') LIMIT 1
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

export async function loadShopProductsData(options: ShopProductsOptions = {}): Promise<PublicShopProductsData> {
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
  const productLimit = typeof options.productLimit === 'number' && Number.isFinite(options.productLimit)
    ? Math.max(1, Math.floor(options.productLimit))
    : null;
  if (snapshot) {
    const snapshotIsAggregate = snapshot.products.every(product => Array.isArray(product.channelDetails));
    const aggregateProducts = applyCatalogTarget(snapshotIsAggregate ? snapshot.products : aggregateCatalogProducts(snapshot.products), options.target);
    const sourceProducts = aggregateProducts.map(product => ({ ...product, siteSponsor: product.siteSponsor === true }));
    const products = productLimit == null ? sourceProducts : sourceProducts.slice(0, productLimit);
    const sites = productLimit == null
      ? snapshot.sites.map(site => ({ ...site, sponsor: site.sponsor === true }))
      : snapshot.sites.filter(site => products.some(product => product.siteId === site.id)).map(site => ({ ...site, sponsor: site.sponsor === true }));
    const totalInStockProductCount = aggregateProducts.filter(product => product.inStock).length;
    const availableCount = aggregateProducts.length;
    return {
      ...snapshot,
      sites,
      products,
      totalProductCount: aggregateProducts.length,
      totalInStockProductCount,
      ...(productLimit == null ? {} : { initialProductLimit: productLimit }),
      isPartial: availableCount > products.length,
    };
  }
  return loadMySqlShopProductsData(options);
}

export async function loadPackedShopProductsSnapshot(): Promise<PackedShopProductsData | null> {
  return loadPublicSnapshot<PackedShopProductsData>('shop-products-packed');
}

export function normalizeHomepageAnnouncement(payload: unknown, fallbackMessage: string) {
  const message = typeof payload === 'object' && payload && 'message' in payload
    ? String((payload as { message?: unknown }).message || '').trim()
    : '';
  return message || fallbackMessage;
}

export async function loadHomepageAnnouncement(fallbackMessage: string) {
  const snapshot = await loadPublicSnapshot<unknown>('homepage-announcement');
  return { message: normalizeHomepageAnnouncement(snapshot, fallbackMessage) };
}

export async function loadGatewaySites(options: PublicListLimitOptions = {}): Promise<PublicGatewaySitesData> {
  const snapshot = await loadPublicSnapshot<PublicGatewaySitesData>('gateway-sites');
  if (snapshot) {
    const limit = safeListLimit(options.limit);
    const sites = sortGatewaySites(filterGatewaySitesByModelFamily(snapshot.sites, options.modelFamily));
    return {
      ...snapshot,
      sites: sites.slice(0, limit ?? sites.length).map(site => ({ ...site, sponsor: site.sponsor === true })),
      totalSiteCount: sites.length,
      sitesWithPricesCount: sites.filter(site => site.priceCount > 0).length,
    };
  }
  return loadMySqlGatewaySites(options);
}

/** Public default order: score first, then broader observed model coverage, then a stable name tie-breaker. */
export function sortGatewaySites(sites: PublicGatewaySiteRow[]) {
  return sites.slice().sort((left, right) =>
    (right.siteScore ?? 0) - (left.siteScore ?? 0)
    || right.modelCount - left.modelCount
    || left.name.localeCompare(right.name, 'zh-Hans-CN'),
  );
}

/** Keeps only sites with an explicit observed coverage family; no name inference. */
export function filterGatewaySitesByModelFamily(sites: PublicGatewaySiteRow[], modelFamily?: string) {
  const normalized = modelFamily?.trim().toLowerCase();
  if (!normalized) return sites.slice();
  return sites.filter(site => site.modelFamilies.some(family => family.trim().toLowerCase() === normalized));
}

export async function loadGatewayModels(options: PublicListLimitOptions = {}): Promise<PublicGatewayModelsData> {
  const snapshot = await loadPublicSnapshot<PublicGatewayModelsData>('gateway-models');
  if (snapshot) {
    const limit = safeListLimit(options.limit);
    return { ...snapshot, models: snapshot.models.slice(0, limit ?? snapshot.models.length) };
  }
  return loadMySqlGatewayModels(options);
}

export async function loadGatewaySiteBySlug(slug: string): Promise<PublicGatewaySiteRow | null> {
  const normalizedSlug = slug.trim();
  if (!normalizedSlug) return null;
  const snapshot = await loadPublicSnapshot<Pick<PublicGatewaySitesData, 'sites'>>('gateway-sites');
  const site = snapshot?.sites.find(item => item.slug === normalizedSlug);
  if (site) return { ...site, sponsor: site.sponsor === true };
  return loadMySqlGatewaySiteBySlug(normalizedSlug);
}

export async function loadGatewayDetail(slug: string, options: { priceLimit?: number } = {}): Promise<PublicGatewayDetail | null> {
  return loadMySqlGatewayDetail(slug, options);
}

export async function loadGatewayModelDetail(pathId: string, options: { siteLimit?: number } = {}): Promise<PublicGatewayModelDetail | null> {
  return loadMySqlGatewayModelDetail(pathId.trim(), options);
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
  if (!validation.ok) return { ok: false as const, errorKey: validation.reason satisfies SubmitSiteUrlErrorKey };
  const url = validation.url;
  getPool();
  const id = createHash('sha256').update(`${url.replace(/#.*/, '').replace(/\/$/, '')}:2164802aa948726ee717662bcc17f7295e278340d9dcf4f0`).digest('hex');
  const [writeResult] = await pool!.execute(
    `INSERT IGNORE INTO shop_sites (id, url, status, family, type) VALUES (?, ?, 'accepted', 'unknown', 'unknown')`,
    [id, url],
  );
  return (writeResult as mysql.ResultSetHeader).affectedRows > 0
    ? { ok: true as const, url }
    : { ok: false as const, errorKey: 'duplicateUrl' satisfies SubmitSiteUrlErrorKey };
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
      const parsed = new URL(apiEndpointInput);
      if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('unsupported protocol');
      parsed.hash = '';
      apiEndpoint = parsed.toString().replace(/\/$/, '');
    } catch {
      return { ok: false as const, errorKey: 'gatewayInvalidApiEndpoint' satisfies SubmitSiteUrlErrorKey };
    }
  }
  const name = input.name.trim();
  const summary = input.summary.trim();
  const paymentMethods = [...new Set(input.paymentMethods.map(value => value.trim().toLowerCase()))]
    .filter(value => publicGatewayPaymentMethods.has(value));
  if (!name) return { ok: false as const, errorKey: 'invalidGatewayName' as const };
  if (name.length > 20) return { ok: false as const, errorKey: 'gatewayNameTooLong' as const };
  if (summary.length > 150) return { ok: false as const, errorKey: 'gatewaySummaryTooLong' as const };
  const url = validation.url;
  const host = new URL(url).hostname.toLowerCase().replace(/^www\./, '');
  const baseSlug = publicGatewaySlug(host);
  let slug = baseSlug;
  for (let index = 2; index <= 1000; index += 1) {
    if ((await getPool().query('SELECT 1 FROM gateway_sites WHERE slug = ? LIMIT 1', [slug])).rows.length === 0) break;
    slug = `${baseSlug}-${index}`;
  }
  getPool();
  const id = createHash('sha256').update(`${url.replace(/#.*/, '').replace(/\/$/, '')}:2164802aa948726ee717662bcc17f7295e278340d9dcf4f0`).digest('hex');
  const [writeResult] = await pool!.execute(
    `INSERT IGNORE INTO gateway_sites (site_id, url, api_endpoint, status, name, family, type, slug, host, weight, summary, payment_methods, created_at) VALUES (?, ?, ?, 'accepted', ?, NULL, 'unknown', ?, ?, 50, ?, ?, UTC_TIMESTAMP())`,
    [id, url, apiEndpoint, name, slug, host, summary, JSON.stringify(paymentMethods)],
  );
  return (writeResult as mysql.ResultSetHeader).affectedRows > 0
    ? { ok: true as const, url }
    : { ok: false as const, errorKey: 'duplicateUrl' satisfies SubmitSiteUrlErrorKey };
}

export async function recordSearchTerm(term: string, resultCount: number) {
  const normalized = normalizeSearchText(term);
  const safeResultCount = Number.isFinite(resultCount) ? Math.max(0, Math.floor(resultCount)) : 0;
  if (!normalized || normalized.length < 2 || /^https?:\/\//i.test(normalized) || /\/shop\//i.test(normalized) || /[a-z0-9-]+(\.[a-z0-9-]+)+/i.test(normalized)) {
    return { recorded: false };
  }
  getPool();
  await pool!.execute(
    `INSERT INTO shop_search_terms (term, total_count, result_count, last_seen_at) VALUES (?, 1, ?, UTC_TIMESTAMP()) ON DUPLICATE KEY UPDATE total_count = total_count + 1, result_count = VALUES(result_count), last_seen_at = UTC_TIMESTAMP()`,
    [normalized, safeResultCount],
  );
  return { recorded: true };
}

export async function recordProductClick(input: ProductClickInput) {
  const siteId = input.siteId.trim();
  const productUrl = input.productUrl?.trim() ?? '';
  const categoryName = input.categoryName?.trim() ?? '';
  const name = input.name?.trim() ?? '';
  if (!siteId || (!productUrl && (!categoryName || !name))) return { recorded: false as const };
  const match = await getPool().query(
    `SELECT shop_products.id FROM shop_products INNER JOIN shop_sites ON shop_sites.id = shop_products.site_id WHERE shop_products.site_id = ? AND shop_sites.status = 'online' AND shop_sites.type = 'cardShop' AND ((? <> '' AND shop_products.product_url = ?) OR (? = '' AND shop_products.category_name = ? AND shop_products.name = ?)) ORDER BY shop_products.refreshed_at DESC, shop_products.name ASC LIMIT 1`,
    [siteId, productUrl, productUrl, productUrl, categoryName, name],
  );
  const id = match.rows[0]?.id;
  if (id == null) return { recorded: false as const };
  getPool();
  await pool!.execute('UPDATE shop_products SET click_count = click_count + 1 WHERE id = ?', [String(id)]);
  return { recorded: true as const };
}

export async function loadPopularSearchTerms(limit = 10, presetPopularSearchTerms: string[] = []) {
  const safeLimit = Math.max(1, Math.min(30, Math.floor(limit)));
  const snapshot = await loadPublicSnapshot<PopularSearchTermsSnapshot>('popular-search-terms');
  if (snapshot && snapshot.terms.length >= safeLimit) {
    const terms = snapshot.terms.slice(0, safeLimit);
    return { terms, normalizedTerms: terms.map(normalizeSearchText) };
  }
  return loadMySqlPopularSearchTerms(safeLimit, presetPopularSearchTerms);
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
  sourceId: string;
  sourceName: string;
  sourcePageUrl: string;
  sampledAt: string;
  isSample: boolean;
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
  modelFamily: string;
  score: number;
  sourceId: string;
  sampledAt: string;
  isSample: boolean;
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
    sourceId: row.source_id == null ? '' : String(row.source_id),
    sourceName: row.source_name == null ? '' : String(row.source_name),
    sourcePageUrl: row.source_page_url == null ? '' : String(row.source_page_url),
    sampledAt: row.sampled_at == null ? '' : String(row.sampled_at),
    isSample: row.is_sample === true || row.is_sample === 1 || row.is_sample === '1',
    fetchedAt: String(row.fetched_at),
  };
}

export async function loadOfficialPriceCatalog(): Promise<PublicOfficialPriceCatalogRow[]> {
  const snapshot = await loadPublicSnapshot<PublicOfficialPriceCatalogRow[]>('official-price-catalog');
  return snapshot ?? loadMySqlOfficialPriceCatalog();
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
    SELECT official_prices.app_slug, official_prices.plan_slug, official_prices.app_name, official_prices.plan_name, official_prices.display_name, official_prices.url_slug, official_prices.is_default, official_prices.display_order, official_prices.country_code, official_prices.country_label, official_prices.currency_code, official_prices.price_text, official_prices.price_value, official_prices.cny_price, official_prices.usd_price, official_prices.rub_price, official_prices.source_id, official_prices.sampled_at, official_prices.is_sample, official_prices.fetched_at,
      COALESCE(reference_data_sources.name, '') AS source_name, COALESCE(reference_data_sources.source_page_url, '') AS source_page_url
    FROM official_prices LEFT JOIN reference_data_sources ON reference_data_sources.id = official_prices.source_id
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
    SELECT official_prices.app_slug, official_prices.plan_slug, official_prices.app_name, official_prices.plan_name, official_prices.display_name, official_prices.url_slug, official_prices.is_default, official_prices.display_order, official_prices.country_code, official_prices.country_label, official_prices.currency_code, official_prices.price_text, official_prices.price_value, official_prices.cny_price, official_prices.usd_price, official_prices.rub_price, official_prices.source_id, official_prices.sampled_at, official_prices.is_sample, official_prices.fetched_at,
      COALESCE(reference_data_sources.name, '') AS source_name, COALESCE(reference_data_sources.source_page_url, '') AS source_page_url
    FROM official_prices LEFT JOIN reference_data_sources ON reference_data_sources.id = official_prices.source_id
    ORDER BY display_order ASC, cny_price ASC
  `);
  return result.rows.map(row => mapOfficialPriceRow(row));
}

export async function loadModelLeaderboardTaskSlugs(): Promise<string[]> {
  const snapshot = await loadPublicSnapshot<string[]>('model-leaderboard-task-slugs');
  if (snapshot) return mergeModelLeaderboardTaskSlugs(snapshot);

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
        WHEN 'video-generation' THEN 5
        ELSE 999
      END ASC,
      task_slug ASC
  `);
  return mergeModelLeaderboardTaskSlugs(result.rows.map(row => String(row.task_slug)));
}

export async function loadModelLeaderboardRowsForTask(taskSlug: string, options: PublicListLimitOptions = {}): Promise<PublicModelLeaderboardRow[]> {
  const normalizedTaskSlug = taskSlug.trim().toLowerCase();
  const limit = safeListLimit(options.limit);
  const snapshot = await loadPublicSnapshot<PublicModelLeaderboardRow[]>('model-leaderboards');
  if (snapshot) {
    return snapshot
      .filter(row => row.taskSlug.trim().toLowerCase() === normalizedTaskSlug)
      .map(normalizeModelLeaderboardRow)
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
      model_family,
      score,
      source_id,
      sampled_at,
      is_sample,
      fetched_at
    FROM model_leaderboards
    WHERE lower(trim(task_slug)) = ?
    ORDER BY rank ASC
    ${limit ? 'LIMIT ?' : ''}
  `, limit ? [normalizedTaskSlug, limit] : [normalizedTaskSlug]);
  return result.rows.map(mapModelLeaderboardRow);
}

export async function loadModelLeaderboardRowsForTaskPage(taskSlug: string, options: PublicListLimitOptions = {}) {
  const normalizedTaskSlug = taskSlug.trim().toLowerCase();
  const limit = safeListLimit(options.limit);
  const snapshot = await loadPublicSnapshot<PublicModelLeaderboardRow[]>('model-leaderboards');
  const allRows = snapshot
    ? snapshot.filter(row => row.taskSlug.trim().toLowerCase() === normalizedTaskSlug).map(normalizeModelLeaderboardRow).sort((a, b) => a.rank - b.rank)
    : (await getPool().query(`SELECT task_slug, source_name, source_url, source_group_slug, source_board_slug, rank, model_name, model_family, score, source_id, sampled_at, is_sample, fetched_at FROM model_leaderboards WHERE lower(trim(task_slug)) = ? ORDER BY rank ASC`, [normalizedTaskSlug])).rows.map(mapModelLeaderboardRow);
  const latestFetchedAt = allRows.reduce<string | null>((latest, row) => !latest || new Date(row.fetchedAt).getTime() > new Date(latest).getTime() ? row.fetchedAt : latest, null);
  return { rows: allRows.slice(0, limit ?? allRows.length), totalCount: allRows.length, latestFetchedAt };
}

function mapModelLeaderboardRow(row: Record<string, unknown>): PublicModelLeaderboardRow {
  return normalizeModelLeaderboardRow({
    taskSlug: String(row.task_slug ?? row.taskSlug ?? ''),
    sourceName: String(row.source_name ?? row.sourceName ?? ''),
    sourceUrl: String(row.source_url ?? row.sourceUrl ?? ''),
    sourceGroupSlug: String(row.source_group_slug ?? row.sourceGroupSlug ?? ''),
    sourceBoardSlug: String(row.source_board_slug ?? row.sourceBoardSlug ?? ''),
    rank: Number(row.rank),
    modelName: String(row.model_name ?? row.modelName ?? ''),
    modelFamily: String(row.model_family ?? row.modelFamily ?? ''),
    score: Number(row.score),
    sourceId: row.source_id == null && row.sourceId == null ? '' : String(row.source_id ?? row.sourceId),
    sampledAt: row.sampled_at == null && row.sampledAt == null ? '' : String(row.sampled_at ?? row.sampledAt),
    isSample: row.is_sample === true || row.is_sample === 1 || row.is_sample === '1' || row.isSample === true,
    fetchedAt: String(row.fetched_at ?? row.fetchedAt ?? ''),
  });
}

function normalizeModelLeaderboardRow(row: PublicModelLeaderboardRow): PublicModelLeaderboardRow {
  return {
    taskSlug: String(row.taskSlug || ''),
    sourceName: String(row.sourceName || ''),
    sourceUrl: String(row.sourceUrl || ''),
    sourceGroupSlug: String(row.sourceGroupSlug || ''),
    sourceBoardSlug: String(row.sourceBoardSlug || ''),
    rank: Number(row.rank) || 0,
    modelName: String(row.modelName || ''),
    modelFamily: String(row.modelFamily || ''),
    score: Number(row.score) || 0,
    sourceId: String(row.sourceId || ''),
    sampledAt: String(row.sampledAt || ''),
    isSample: row.isSample === true,
    fetchedAt: String(row.fetchedAt || ''),
  };
}

export async function loadModelLeaderboards(): Promise<PublicModelLeaderboardRow[]> {
  const snapshot = await loadPublicSnapshot<PublicModelLeaderboardRow[]>('model-leaderboards');
  if (snapshot) return snapshot.map(normalizeModelLeaderboardRow);

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
      model_family,
      score,
      source_id,
      sampled_at,
      is_sample,
      fetched_at
    FROM model_leaderboards
    ORDER BY
      CASE task_slug
        WHEN 'coding' THEN 1
        WHEN 'creative-writing' THEN 2
        WHEN 'math' THEN 3
        WHEN 'text-to-image' THEN 4
        WHEN 'video-generation' THEN 5
        ELSE 999
      END ASC,
      rank ASC
  `);
  return result.rows.map(row => mapModelLeaderboardRow(row));
}

