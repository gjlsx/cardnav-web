/**
 * 文件说明: 将公开页面的有限参考样例幂等写入本机 MySQL，并同步商品页公开快照。
 */
import 'dotenv/config';
import mysql from 'mysql2/promise';
import { initializeMySqlSchema } from '../src/database.js';
import { catalogPlanModels, catalogProducts, aggregateCatalogProducts } from '../src/catalog.js';
import { packShopProductsData, type PublicShopProductsData } from '../src/shop-products-data.js';
import { referenceDataSources, referenceProductSamples } from '../src/reference-samples.js';

const config = {
  host: process.env.MYSQL_HOST || '127.0.0.1',
  port: Number(process.env.MYSQL_PORT || 3306),
  user: process.env.MYSQL_USER || 'root',
  password: process.env.MYSQL_PASSWORD,
  database: process.env.MYSQL_DATABASE || 'ailovemoney',
};

function toMySqlDate(value: string) {
  return new Date(value).toISOString().slice(0, 19).replace('T', ' ');
}

async function main() {
  await initializeMySqlSchema(config);
  const connection = await mysql.createConnection(config);
  try {
    await connection.beginTransaction();
    for (const source of referenceDataSources) {
      await connection.execute(
        `INSERT INTO reference_data_sources (id, name, source_page_url, sampled_at, is_sample, usage_note, priority)
         VALUES (?, ?, ?, ?, TRUE, ?, ?)
         ON DUPLICATE KEY UPDATE name = VALUES(name), source_page_url = VALUES(source_page_url), sampled_at = VALUES(sampled_at), is_sample = TRUE, usage_note = VALUES(usage_note), priority = VALUES(priority)`,
        [source.id, source.name, source.sourcePageUrl, toMySqlDate(source.sampledAt), source.usageNote, source.priority],
      );
    }

    const sourceIds = referenceDataSources.map(source => source.id);
    const placeholders = sourceIds.map(() => '?').join(', ');
    await connection.execute(`DELETE FROM shop_products WHERE is_sample = TRUE AND source_id IN (${placeholders})`, sourceIds);
    await connection.execute("DELETE FROM shop_sites WHERE family = 'reference-sample' AND id LIKE 'reference-%'");

    const sites = [...new Map(referenceProductSamples.map(sample => [sample.siteId, sample])).values()];
    for (const site of sites) {
      const siteProducts = referenceProductSamples.filter(sample => sample.siteId === site.siteId);
      const inStockCount = siteProducts.filter(sample => sample.inStock).length;
      await connection.execute(
        `INSERT INTO shop_sites (id, name, url, last_product_refresh_success_at, score, sponsor, product_count, in_stock_product_count, status, type, family)
         VALUES (?, ?, NULL, ?, 50, FALSE, ?, ?, 'online', 'cardShop', 'reference-sample')
         ON DUPLICATE KEY UPDATE name = VALUES(name), url = NULL, last_product_refresh_success_at = VALUES(last_product_refresh_success_at), score = 50, sponsor = FALSE, product_count = VALUES(product_count), in_stock_product_count = VALUES(in_stock_product_count), status = 'online', type = 'cardShop', family = 'reference-sample'`,
        [site.siteId, site.siteName, toMySqlDate(site.sampledAt), siteProducts.length, inStockCount],
      );
    }

    for (const product of catalogProducts) {
      await connection.execute(
        `INSERT INTO catalog_products (slug, target_kind, target_slug, platform, product_type, display_name, aliases, modality)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
         ON DUPLICATE KEY UPDATE target_kind = VALUES(target_kind), target_slug = VALUES(target_slug), platform = VALUES(platform), product_type = VALUES(product_type), display_name = VALUES(display_name), aliases = VALUES(aliases), modality = VALUES(modality)`,
        [product.slug, product.targetKind, product.targetSlug, product.platform, product.productType, product.displayName, JSON.stringify(product.aliases), product.modality],
      );
    }
    for (const relation of catalogPlanModels) {
      await connection.execute(
        `INSERT INTO catalog_plan_models (plan_slug, model_family) VALUES (?, ?)
         ON DUPLICATE KEY UPDATE model_family = VALUES(model_family)`,
        [relation.planSlug, relation.modelFamily],
      );
    }

    for (const sample of referenceProductSamples) {
      await connection.execute(
        `INSERT INTO shop_products (
          site_id, source_id, standard_product, platform, product_type, category_name, name, price, price_number, price_unit, currency_code,
          product_url, stock, in_stock, channel_count, available_channel_count, out_of_stock_channel_count, sampled_at, is_sample, refreshed_at, click_count, score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, TRUE, ?, 0, 0)`,
        [
          sample.siteId, sample.sourceId, sample.standardProduct, sample.platform, sample.productType, sample.categoryName, sample.name,
          sample.price, sample.priceNumber, sample.priceUnit, sample.currencyCode, sample.inStock, sample.channelCount,
          sample.availableChannelCount, sample.outOfStockChannelCount, toMySqlDate(sample.sampledAt), toMySqlDate(sample.sampledAt),
        ],
      );
    }

    const rawData: PublicShopProductsData = {
      sites: sites.map(site => ({
        id: site.siteId, name: site.siteName, url: '', lastProductRefreshSuccessAt: site.sampledAt,
        lastProductRefreshSuccessTime: toMySqlDate(site.sampledAt), score: 50, sponsor: false,
      })),
      products: referenceProductSamples.map(sample => ({
        categoryName: sample.categoryName, name: sample.name, price: sample.price, priceNumber: sample.priceNumber, priceUnit: sample.priceUnit,
        inStock: sample.inStock, refreshedAt: sample.sampledAt, refreshTime: toMySqlDate(sample.sampledAt), siteId: sample.siteId,
        siteName: sample.siteName, siteUrl: '', siteProductRefreshSuccessAt: sample.sampledAt,
        siteProductRefreshSuccessTime: toMySqlDate(sample.sampledAt), siteScore: 50, siteSponsor: false, clickCount: 0, score: 0,
        standardProduct: sample.standardProduct, platform: sample.platform, productType: sample.productType, currencyCode: sample.currencyCode,
        channelCount: sample.channelCount, availableChannelCount: sample.availableChannelCount, outOfStockChannelCount: sample.outOfStockChannelCount,
        sampledAt: sample.sampledAt, isSample: true,
        sourceName: referenceDataSources.find(source => source.id === sample.sourceId)?.name ?? '',
        sourcePageUrl: referenceDataSources.find(source => source.id === sample.sourceId)?.sourcePageUrl ?? '',
        sourcePriority: referenceDataSources.find(source => source.id === sample.sourceId)?.priority ?? 0,
      })),
      totalSiteCount: sites.length,
      totalProductCount: referenceProductSamples.length,
      totalInStockProductCount: referenceProductSamples.filter(sample => sample.inStock).length,
      latestRefreshedAt: referenceProductSamples.map(sample => sample.sampledAt).sort().at(-1) ?? null,
      latestRefreshTime: toMySqlDate(referenceProductSamples.map(sample => sample.sampledAt).sort().at(-1) ?? ''),
      isPartial: false,
    };
    const data: PublicShopProductsData = {
      ...rawData,
      products: aggregateCatalogProducts(rawData.products),
      totalProductCount: aggregateCatalogProducts(rawData.products).length,
      totalInStockProductCount: aggregateCatalogProducts(rawData.products).filter(product => product.inStock).length,
    };
    const snapshots = [
      ['shop-products', data],
      ['shop-products-packed', packShopProductsData(data)],
    ] as const;
    for (const [key, payload] of snapshots) {
      await connection.execute(
        'INSERT INTO public_snapshot_entries (`key`, payload) VALUES (?, ?) ON DUPLICATE KEY UPDATE payload = VALUES(payload)',
        [key, JSON.stringify(payload)],
      );
    }
    await connection.commit();
    const [counts] = await connection.query<{ sources: number; products: number; sites: number }[]>(`
      SELECT
        (SELECT COUNT(*) FROM reference_data_sources WHERE is_sample = TRUE) AS sources,
        (SELECT COUNT(*) FROM shop_products WHERE is_sample = TRUE) AS products,
        (SELECT COUNT(*) FROM shop_sites WHERE family = 'reference-sample') AS sites
    `);
    console.log(JSON.stringify({ seeded: counts[0], snapshotKeys: snapshots.map(([key]) => key) }));
  } catch (error) {
    await connection.rollback();
    throw error;
  } finally {
    await connection.end();
  }
}

main().catch(error => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
