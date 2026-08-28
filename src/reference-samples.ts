/**
 * 文件说明: 定义公开页面的有限参考样例；仅用于本地演示和页面验证，不代表实时价格、库存或购买建议。
 */

export type ReferenceDataSource = {
  id: string;
  name: string;
  sourcePageUrl: string;
  sampledAt: string;
  usageNote: string;
  priority: number;
};

export type ReferenceProductSample = {
  id: string;
  sourceId: string;
  siteId: string;
  siteName: string;
  platform: string;
  productType: string;
  standardProduct: string;
  categoryName: string;
  name: string;
  price: string;
  priceNumber: number | null;
  priceUnit: string | null;
  currencyCode: string;
  inStock: boolean;
  channelCount: number | null;
  availableChannelCount: number | null;
  outOfStockChannelCount: number | null;
  sampledAt: string;
};

export type ReferenceGatewaySample = {
  id: string;
  sourceId: string;
  sourcePageUrl: string;
  name: string;
  family: string;
  summary: string;
  score: number;
  url: '';
  inviteUrl: '';
  isSample: true;
  sampledAt: string;
};

export type ReferenceGatewayModelCoverage = {
  siteId: string;
  modelId: string;
  modelFamily: string;
  sourceId: string;
  observedAt: string;
  isSample: true;
  hasPublicPrice: boolean;
};

export type ReferenceOfficialPriceSample = {
  sourceId: string;
  sourcePageUrl: string;
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
  sampledAt: string;
  isSample: true;
};

const sampledAt = '2026-08-27T22:55:00.000Z';

export const referenceDataSources: ReferenceDataSource[] = [
  {
    id: 'reference-cardnav-home',
    name: 'CardNav 公开首页参考',
    sourcePageUrl: 'https://cardnav.xyz/',
    sampledAt,
    usageNote: '公开首页的短商品和中转站展示字段，仅作本地参考样例。',
    priority: 20,
  },
  {
    id: 'reference-priceai-channels',
    name: 'PriceAI 公开渠道列表参考',
    sourcePageUrl: 'https://priceai.cc/channels',
    sampledAt,
    usageNote: '公开标准商品/渠道聚合字段，仅作本地参考样例。',
    priority: 30,
  },
  {
    id: 'reference-openprice-products',
    name: 'OpenPrice 公开商品列表参考',
    sourcePageUrl: 'https://www.openprice.cc/card-products',
    sampledAt,
    usageNote: '公开按平台分组的最低参考价字段，仅作本地参考样例。',
    priority: 10,
  },
  {
    id: 'reference-cardnav-official-price',
    name: 'CardNav 官方订阅公开参考',
    sourcePageUrl: 'https://cardnav.xyz/official-price/chatgpt-pro-5x',
    sampledAt,
    usageNote: '公开官方订阅页的信息层级与地区价格字段，仅作本地参考样例，非实时或官方价格承诺。',
    priority: 20,
  },
  {
    id: 'reference-cardnav-leaderboard',
    name: 'CardNav 公开模型排行参考',
    sourcePageUrl: 'https://cardnav.xyz/model-leaderboard',
    sampledAt,
    usageNote: '公开任务分类与 Top 模型信息层级的参考样例，不是本站实时评测或购买建议。',
    priority: 20,
  },
];

export const referenceProductSamples: ReferenceProductSample[] = [
  {
    id: 'reference-priceai-chatgpt-basic', sourceId: 'reference-priceai-channels', siteId: 'reference-merchant-huasheng', siteName: '花生店铺（公开参考）',
    platform: 'ChatGPT', productType: '成品账号', standardProduct: 'chatgpt-basic-account', categoryName: 'ChatGPT · 成品账号', name: 'ChatGPT 普号',
    price: '¥0.30', priceNumber: 0.3, priceUnit: '¥', currencyCode: 'CNY', inStock: true, channelCount: 182, availableChannelCount: 111, outOfStockChannelCount: 71, sampledAt,
  },
  {
    id: 'reference-priceai-claude-pro', sourceId: 'reference-priceai-channels', siteId: 'reference-merchant-mufeng', siteName: '沐风源头（公开参考）',
    platform: 'Claude', productType: '订阅/会员', standardProduct: 'claude-pro', categoryName: 'Claude · 订阅/会员', name: 'Claude Pro',
    price: '¥128', priceNumber: 128, priceUnit: '¥', currencyCode: 'CNY', inStock: true, channelCount: 120, availableChannelCount: 88, outOfStockChannelCount: 32, sampledAt,
  },
  {
    id: 'reference-priceai-gemini-pro', sourceId: 'reference-priceai-channels', siteId: 'reference-merchant-cc-cat', siteName: 'cc-cat（公开参考）',
    platform: 'Gemini', productType: '成品账号', standardProduct: 'gemini-pro-account', categoryName: 'Gemini · 成品账号', name: 'Gemini Pro 成品号',
    price: '¥3.80', priceNumber: 3.8, priceUnit: '¥', currencyCode: 'CNY', inStock: true, channelCount: 365, availableChannelCount: 187, outOfStockChannelCount: 178, sampledAt,
  },
  {
    id: 'reference-priceai-super-grok', sourceId: 'reference-priceai-channels', siteId: 'reference-merchant-zhilian', siteName: '直连AI（公开参考）',
    platform: 'Grok', productType: '订阅/会员', standardProduct: 'super-grok', categoryName: 'Grok · 订阅/会员', name: 'Super Grok',
    price: '¥56.03', priceNumber: 56.03, priceUnit: '¥', currencyCode: 'CNY', inStock: true, channelCount: 196, availableChannelCount: 119, outOfStockChannelCount: 77, sampledAt,
  },
  {
    id: 'reference-openprice-claude-basic', sourceId: 'reference-openprice-products', siteId: 'reference-merchant-openprice', siteName: 'OpenPrice 公开渠道样例',
    platform: 'Claude', productType: '成品账号', standardProduct: 'claude-basic-account', categoryName: 'Claude · 成品账号', name: 'Claude 普通号',
    price: '¥3.09', priceNumber: 3.09, priceUnit: '¥', currencyCode: 'CNY', inStock: true, channelCount: 29, availableChannelCount: null, outOfStockChannelCount: null, sampledAt,
  },
  {
    id: 'reference-openprice-claude-pro', sourceId: 'reference-openprice-products', siteId: 'reference-merchant-openprice', siteName: 'OpenPrice 公开渠道样例',
    platform: 'Claude', productType: '成品账号', standardProduct: 'claude-pro-account', categoryName: 'Claude · 成品账号', name: 'Claude Pro ｜成品号',
    price: '¥77.25', priceNumber: 77.25, priceUnit: '¥', currencyCode: 'CNY', inStock: true, channelCount: 74, availableChannelCount: null, outOfStockChannelCount: null, sampledAt,
  },
  {
    id: 'reference-openprice-chatgpt-basic', sourceId: 'reference-openprice-products', siteId: 'reference-merchant-openprice', siteName: 'OpenPrice 公开渠道样例',
    platform: 'ChatGPT', productType: '成品账号', standardProduct: 'chatgpt-basic-account', categoryName: 'ChatGPT · 成品账号', name: 'ChatGPT 普通号',
    price: '¥0.30', priceNumber: 0.3, priceUnit: '¥', currencyCode: 'CNY', inStock: true, channelCount: 25, availableChannelCount: null, outOfStockChannelCount: null, sampledAt,
  },
  {
    id: 'reference-cardnav-gpt-pro', sourceId: 'reference-cardnav-home', siteId: 'reference-merchant-geniuscoder', siteName: 'GeniusCoder（公开参考）',
    platform: 'GPT', productType: 'API 额度', standardProduct: 'gpt-pro-20x-credit', categoryName: 'GPT · API 额度', name: 'G Pro 20x 10刀额度',
    price: '¥9.50', priceNumber: 9.5, priceUnit: '¥', currencyCode: 'CNY', inStock: true, channelCount: null, availableChannelCount: null, outOfStockChannelCount: null, sampledAt,
  },
  {
    id: 'reference-cardnav-chatgpt-plus', sourceId: 'reference-cardnav-home', siteId: 'reference-merchant-shihui', siteName: '实惠AI批发网（公开参考）',
    platform: 'ChatGPT', productType: '兑换码', standardProduct: 'chatgpt-plus-code', categoryName: 'ChatGPT · 兑换码', name: 'ChatGPT Plus 月会员兑换码',
    price: '¥19', priceNumber: 19, priceUnit: '¥', currencyCode: 'CNY', inStock: true, channelCount: null, availableChannelCount: null, outOfStockChannelCount: null, sampledAt,
  },
];

// The public pages name these services and model families, but this seed does
// not infer an official URL, invitation, health metric, or commercial action.
export const referenceGatewaySamples: ReferenceGatewaySample[] = [
  {
    id: 'reference-gateway-lingxi-ai', sourceId: 'reference-cardnav-home', sourcePageUrl: 'https://cardnav.xyz/',
    name: 'Lingxi AI（公开参考）', family: 'New API', summary: '公开页面列出的聚合 API 参考样例；只展示已观察到的模型覆盖。', score: 50, url: '', inviteUrl: '', isSample: true, sampledAt,
  },
  {
    id: 'reference-gateway-genius-coder', sourceId: 'reference-cardnav-home', sourcePageUrl: 'https://cardnav.xyz/',
    name: 'Genius Coder（公开参考）', family: 'Sub2API', summary: '公开页面列出的 API 中转参考样例；价格与可用性需自行核对。', score: 50, url: '', inviteUrl: '', isSample: true, sampledAt,
  },
  {
    id: 'reference-gateway-packy-code', sourceId: 'reference-cardnav-home', sourcePageUrl: 'https://cardnav.xyz/',
    name: 'Packy Code（公开参考）', family: 'New API', summary: '公开页面列出的 API 中转参考样例；不代表实时状态。', score: 50, url: '', inviteUrl: '', isSample: true, sampledAt,
  },
  {
    id: 'reference-gateway-mfapi', sourceId: 'reference-priceai-channels', sourcePageUrl: 'https://priceai.cc/channels',
    name: 'MFAPI（公开参考）', family: 'Sub2API', summary: '公开频道列表中的中转站参考样例；只保留公开模型标识。', score: 50, url: '', inviteUrl: '', isSample: true, sampledAt,
  },
  {
    id: 'reference-gateway-beibei', sourceId: 'reference-priceai-channels', sourcePageUrl: 'https://priceai.cc/channels',
    name: '贝贝（公开参考）', family: 'Sub2API', summary: '公开频道列表中的中转站参考样例；不含性能、购买或邀请信息。', score: 50, url: '', inviteUrl: '', isSample: true, sampledAt,
  },
];

export const referenceGatewayModelCoverage: ReferenceGatewayModelCoverage[] = [
  { siteId: 'reference-gateway-lingxi-ai', modelId: 'gpt-4o', modelFamily: 'GPT', sourceId: 'reference-cardnav-home', observedAt: sampledAt, isSample: true, hasPublicPrice: false },
  { siteId: 'reference-gateway-lingxi-ai', modelId: 'claude-3-5-sonnet', modelFamily: 'Claude', sourceId: 'reference-cardnav-home', observedAt: sampledAt, isSample: true, hasPublicPrice: false },
  { siteId: 'reference-gateway-lingxi-ai', modelId: 'deepseek-v3', modelFamily: 'DeepSeek', sourceId: 'reference-cardnav-home', observedAt: sampledAt, isSample: true, hasPublicPrice: false },
  { siteId: 'reference-gateway-genius-coder', modelId: 'gpt-4o', modelFamily: 'GPT', sourceId: 'reference-cardnav-home', observedAt: sampledAt, isSample: true, hasPublicPrice: false },
  { siteId: 'reference-gateway-packy-code', modelId: 'claude-3-5-sonnet', modelFamily: 'Claude', sourceId: 'reference-cardnav-home', observedAt: sampledAt, isSample: true, hasPublicPrice: false },
  { siteId: 'reference-gateway-packy-code', modelId: 'gemini-1.5-pro', modelFamily: 'Gemini', sourceId: 'reference-cardnav-home', observedAt: sampledAt, isSample: true, hasPublicPrice: false },
  { siteId: 'reference-gateway-mfapi', modelId: 'deepseek-v3', modelFamily: 'DeepSeek', sourceId: 'reference-priceai-channels', observedAt: sampledAt, isSample: true, hasPublicPrice: false },
  { siteId: 'reference-gateway-mfapi', modelId: 'qwen-max', modelFamily: 'Qwen', sourceId: 'reference-priceai-channels', observedAt: sampledAt, isSample: true, hasPublicPrice: false },
  { siteId: 'reference-gateway-beibei', modelId: 'qwen-max', modelFamily: 'Qwen', sourceId: 'reference-priceai-channels', observedAt: sampledAt, isSample: true, hasPublicPrice: false },
];

// These are intentionally bounded public reference rows. Currency conversions
// are fixed sample values for display verification, not live exchange quotes.
export const referenceOfficialPriceSamples: ReferenceOfficialPriceSample[] = [
  { sourceId: 'reference-cardnav-official-price', sourcePageUrl: 'https://cardnav.xyz/official-price/chatgpt-pro-5x', appSlug: 'chatgpt', planSlug: 'plus', appName: 'ChatGPT', planName: 'Plus', displayName: 'ChatGPT Plus', urlSlug: 'chatgpt-plus', isDefault: true, displayOrder: 10, countryCode: 'US', countryLabel: '美国', currencyCode: 'USD', priceText: '$20.00', priceValue: 20, cnyPrice: 144, usdPrice: 20, rubPrice: 1840, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-official-price', sourcePageUrl: 'https://cardnav.xyz/official-price/chatgpt-pro-5x', appSlug: 'chatgpt', planSlug: 'plus', appName: 'ChatGPT', planName: 'Plus', displayName: 'ChatGPT Plus', urlSlug: 'chatgpt-plus', isDefault: true, displayOrder: 10, countryCode: 'JP', countryLabel: '日本', currencyCode: 'JPY', priceText: '¥3,000', priceValue: 3000, cnyPrice: 139, usdPrice: 19.3, rubPrice: 1776, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-official-price', sourcePageUrl: 'https://cardnav.xyz/official-price/chatgpt-pro-5x', appSlug: 'chatgpt', planSlug: 'plus', appName: 'ChatGPT', planName: 'Plus', displayName: 'ChatGPT Plus', urlSlug: 'chatgpt-plus', isDefault: true, displayOrder: 10, countryCode: 'TR', countryLabel: '土耳其', currencyCode: 'TRY', priceText: '₺699.99', priceValue: 699.99, cnyPrice: 153, usdPrice: 21.2, rubPrice: 1950, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-official-price', sourcePageUrl: 'https://cardnav.xyz/official-price/chatgpt-pro-5x', appSlug: 'claude', planSlug: 'pro', appName: 'Claude', planName: 'Pro', displayName: 'Claude Pro', urlSlug: 'claude-pro', isDefault: false, displayOrder: 20, countryCode: 'US', countryLabel: '美国', currencyCode: 'USD', priceText: '$20.00', priceValue: 20, cnyPrice: 144, usdPrice: 20, rubPrice: 1840, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-official-price', sourcePageUrl: 'https://cardnav.xyz/official-price/chatgpt-pro-5x', appSlug: 'claude', planSlug: 'pro', appName: 'Claude', planName: 'Pro', displayName: 'Claude Pro', urlSlug: 'claude-pro', isDefault: false, displayOrder: 20, countryCode: 'GB', countryLabel: '英国', currencyCode: 'GBP', priceText: '£18.00', priceValue: 18, cnyPrice: 166, usdPrice: 23, rubPrice: 2116, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-official-price', sourcePageUrl: 'https://cardnav.xyz/official-price/chatgpt-pro-5x', appSlug: 'gemini', planSlug: 'advanced', appName: 'Gemini', planName: 'Advanced', displayName: 'Gemini Advanced', urlSlug: 'gemini-advanced', isDefault: false, displayOrder: 30, countryCode: 'US', countryLabel: '美国', currencyCode: 'USD', priceText: '$19.99', priceValue: 19.99, cnyPrice: 144, usdPrice: 19.99, rubPrice: 1839, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-official-price', sourcePageUrl: 'https://cardnav.xyz/official-price/chatgpt-pro-5x', appSlug: 'gemini', planSlug: 'advanced', appName: 'Gemini', planName: 'Advanced', displayName: 'Gemini Advanced', urlSlug: 'gemini-advanced', isDefault: false, displayOrder: 30, countryCode: 'JP', countryLabel: '日本', currencyCode: 'JPY', priceText: '¥2,900', priceValue: 2900, cnyPrice: 135, usdPrice: 18.7, rubPrice: 1720, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-official-price', sourcePageUrl: 'https://cardnav.xyz/official-price/chatgpt-pro-5x', appSlug: 'grok', planSlug: 'supergrok', appName: 'Grok', planName: 'SuperGrok', displayName: 'SuperGrok', urlSlug: 'grok-supergrok', isDefault: false, displayOrder: 40, countryCode: 'US', countryLabel: '美国', currencyCode: 'USD', priceText: '$30.00', priceValue: 30, cnyPrice: 216, usdPrice: 30, rubPrice: 2760, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-official-price', sourcePageUrl: 'https://cardnav.xyz/official-price/chatgpt-pro-5x', appSlug: 'grok', planSlug: 'supergrok', appName: 'Grok', planName: 'SuperGrok', displayName: 'SuperGrok', urlSlug: 'grok-supergrok', isDefault: false, displayOrder: 40, countryCode: 'GB', countryLabel: '英国', currencyCode: 'GBP', priceText: '£25.00', priceValue: 25, cnyPrice: 230, usdPrice: 31.8, rubPrice: 2926, sampledAt, isSample: true },
];

export type ReferenceLeaderboardSample = {
  sourceId: string;
  sourceName: string;
  sourceUrl: string;
  sourceGroupSlug: string;
  sourceBoardSlug: string;
  taskSlug: string;
  rank: number;
  modelName: string;
  modelFamily: string;
  score: number;
  sampledAt: string;
  isSample: true;
};

// Bounded public-page ranks for display verification. Scores stay attributed
// to the source page and are never this site's live evaluation.
export const referenceLeaderboardSamples: ReferenceLeaderboardSample[] = [
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/coding', sourceGroupSlug: 'text', sourceBoardSlug: 'coding', taskSlug: 'coding', rank: 1, modelName: 'gpt-4o', modelFamily: 'GPT', score: 1456.21, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/coding', sourceGroupSlug: 'text', sourceBoardSlug: 'coding', taskSlug: 'coding', rank: 2, modelName: 'claude-3-5-sonnet', modelFamily: 'Claude', score: 1448.17, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/coding', sourceGroupSlug: 'text', sourceBoardSlug: 'coding', taskSlug: 'coding', rank: 3, modelName: 'deepseek-v3', modelFamily: 'DeepSeek', score: 1410.44, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/creative-writing', sourceGroupSlug: 'text', sourceBoardSlug: 'creative-writing', taskSlug: 'creative-writing', rank: 1, modelName: 'claude-3-5-sonnet', modelFamily: 'Claude', score: 1433.08, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/creative-writing', sourceGroupSlug: 'text', sourceBoardSlug: 'creative-writing', taskSlug: 'creative-writing', rank: 2, modelName: 'gpt-4o', modelFamily: 'GPT', score: 1411.62, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/creative-writing', sourceGroupSlug: 'text', sourceBoardSlug: 'creative-writing', taskSlug: 'creative-writing', rank: 3, modelName: 'qwen-max', modelFamily: 'Qwen', score: 1388.9, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/math', sourceGroupSlug: 'text', sourceBoardSlug: 'math', taskSlug: 'math', rank: 1, modelName: 'gemini-1.5-pro', modelFamily: 'Gemini', score: 1462.55, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/math', sourceGroupSlug: 'text', sourceBoardSlug: 'math', taskSlug: 'math', rank: 2, modelName: 'gpt-4o', modelFamily: 'GPT', score: 1440.12, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/math', sourceGroupSlug: 'text', sourceBoardSlug: 'math', taskSlug: 'math', rank: 3, modelName: 'deepseek-v3', modelFamily: 'DeepSeek', score: 1422.73, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/text-to-image', sourceGroupSlug: 'image', sourceBoardSlug: 'text-to-image', taskSlug: 'text-to-image', rank: 1, modelName: 'imagen-3', modelFamily: 'Gemini', score: 1288.4, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/text-to-image', sourceGroupSlug: 'image', sourceBoardSlug: 'text-to-image', taskSlug: 'text-to-image', rank: 2, modelName: 'gpt-image', modelFamily: 'GPT', score: 1264.8, sampledAt, isSample: true },
  { sourceId: 'reference-cardnav-leaderboard', sourceName: 'CardNav 公开模型排行参考', sourceUrl: 'https://cardnav.xyz/model-leaderboard/text-to-image', sourceGroupSlug: 'image', sourceBoardSlug: 'text-to-image', taskSlug: 'text-to-image', rank: 3, modelName: 'flux-1', modelFamily: '', score: 1210.15, sampledAt, isSample: true },
];
