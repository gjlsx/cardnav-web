/**
 * 文件说明: 标准商品目录和公开报价的确定性聚合规则。
 * 目录映射只接受人工声明，绝不通过名称猜测模型或订阅关系。
 */
import type { PublicProductRow } from './store.js';

export type CatalogTarget = { kind: 'model' | 'subscription_plan'; slug: string };

export const catalogProducts = [
  { slug: 'chatgpt-basic-account', targetKind: 'model', targetSlug: 'gpt', platform: 'ChatGPT', productType: 'account', displayName: 'ChatGPT 普通账号', aliases: ['chatgpt 普号'], modality: 'text' },
  { slug: 'chatgpt-plus-code', targetKind: 'subscription_plan', targetSlug: 'chatgpt-plus', platform: 'ChatGPT', productType: 'redeem_code', displayName: 'ChatGPT Plus 兑换码', aliases: ['chatgpt plus 月会员兑换码'], modality: 'text' },
  { slug: 'claude-basic-account', targetKind: 'model', targetSlug: 'claude', platform: 'Claude', productType: 'account', displayName: 'Claude 普通账号', aliases: ['claude 普通号'], modality: 'text' },
  { slug: 'claude-pro', targetKind: 'subscription_plan', targetSlug: 'claude-pro', platform: 'Claude', productType: 'subscription', displayName: 'Claude Pro', aliases: ['claude pro 订阅'], modality: 'text' },
  { slug: 'claude-pro-account', targetKind: 'model', targetSlug: 'claude', platform: 'Claude', productType: 'account', displayName: 'Claude Pro 成品号', aliases: ['claude pro 成品号'], modality: 'text' },
  { slug: 'gemini-pro-account', targetKind: 'model', targetSlug: 'gemini', platform: 'Gemini', productType: 'account', displayName: 'Gemini Pro 成品号', aliases: ['gemini pro'], modality: 'text' },
  { slug: 'gpt-pro-20x-credit', targetKind: 'model', targetSlug: 'gpt', platform: 'GPT', productType: 'api_credit', displayName: 'GPT Pro 20x 额度', aliases: ['g pro 20x 10刀额度'], modality: 'text' },
  { slug: 'super-grok', targetKind: 'subscription_plan', targetSlug: 'super-grok', platform: 'Grok', productType: 'subscription', displayName: 'Super Grok', aliases: ['supergrok'], modality: 'text' },
] as const;

export const catalogPlanModels = [
  { planSlug: 'chatgpt-plus', modelFamily: 'GPT' },
  { planSlug: 'claude-pro', modelFamily: 'Claude' },
  { planSlug: 'super-grok', modelFamily: 'Grok' },
] as const;

export function catalogProductTarget(slug: string): CatalogTarget | null {
  const normalized = slug.trim();
  if (catalogPlanModels.some(entry => entry.planSlug === normalized)) {
    return { kind: 'subscription_plan', slug: normalized };
  }
  const product = catalogProducts.find(entry => entry.slug === normalized);
  return product ? { kind: product.targetKind, slug: product.targetSlug } : null;
}

/** Returns only manually declared SKU relations for an internal model/plan target. */
export function catalogProductSlugsForTarget(target: string): string[] {
  const normalized = target.trim().toLowerCase();
  if (!normalized) return [];
  const matchingFamilies = catalogPlanModels
    .filter(entry => entry.planSlug.toLowerCase() === normalized)
    .map(entry => entry.modelFamily.toLowerCase());
  return catalogProducts
    .filter(product => product.targetSlug.toLowerCase() === normalized
      || (matchingFamilies.includes(product.targetSlug.toLowerCase()) && product.targetKind === 'model'))
    .map(product => product.slug);
}

function latestTime(rows: PublicProductRow[]) {
  return rows.map(row => row.sampledAt || row.refreshedAt || '').sort().at(-1) || null;
}

function sourcePriority(row: PublicProductRow) {
  return Number.isFinite(row.sourcePriority) ? Number(row.sourcePriority) : 0;
}

function compareOffer(a: PublicProductRow, b: PublicProductRow) {
  const aPrice = typeof a.priceNumber === 'number' ? a.priceNumber : Number.POSITIVE_INFINITY;
  const bPrice = typeof b.priceNumber === 'number' ? b.priceNumber : Number.POSITIVE_INFINITY;
  return aPrice - bPrice || Number(b.inStock) - Number(a.inStock) || String(a.siteName).localeCompare(String(b.siteName), 'zh-Hans-CN');
}

/**
 * One public row per declared standard SKU. The best available source tier wins;
 * duplicate offers inside that tier are represented by the cheapest one, while
 * the channel details remain available for a local drill-down.
 */
export function aggregateCatalogProducts(rows: PublicProductRow[]): PublicProductRow[] {
  const grouped = new Map<string, PublicProductRow[]>();
  for (const row of rows) {
    const key = String(row.standardProduct || '').trim();
    if (!key) continue;
    grouped.set(key, [...(grouped.get(key) ?? []), row]);
  }

  return [...grouped.entries()].map(([standardProduct, candidates]) => {
    const highestPriority = Math.max(...candidates.map(sourcePriority));
    const selected = candidates.filter(candidate => sourcePriority(candidate) === highestPriority).sort(compareOffer);
    const cheapest = selected[0];
    const detailRows = selected.map(row => ({
      siteId: row.siteId,
      siteName: row.siteName,
      inStock: row.inStock,
      price: row.price,
      priceNumber: row.priceNumber,
      priceUnit: row.priceUnit,
      sampledAt: row.sampledAt || row.refreshedAt || null,
      isSample: row.isSample === true,
    }));
    const at = latestTime(selected);
    return {
      ...cheapest,
      id: `catalog:${standardProduct}`,
      standardProduct,
      productUrl: '',
      siteId: `catalog:${standardProduct}`,
      siteName: `${selected.length} 个渠道`,
      siteUrl: '',
      siteScore: 50,
      siteSponsor: false,
      channelCount: selected.length,
      availableChannelCount: selected.filter(row => row.inStock).length,
      outOfStockChannelCount: selected.filter(row => !row.inStock).length,
      inStock: selected.some(row => row.inStock),
      sampledAt: at,
      refreshedAt: at,
      refreshTime: cheapest.refreshTime,
      channelDetails: detailRows,
    };
  }).sort((a, b) => String(a.platform || '').localeCompare(String(b.platform || ''), 'zh-Hans-CN') || String(a.name).localeCompare(String(b.name), 'zh-Hans-CN'));
}
