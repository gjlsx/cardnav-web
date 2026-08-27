/**
 * 文件说明: 定义公开页面的有限参考样例；仅用于本地演示和页面验证，不代表实时价格、库存或购买建议。
 */

export type ReferenceDataSource = {
  id: string;
  name: string;
  sourcePageUrl: string;
  sampledAt: string;
  usageNote: string;
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

const sampledAt = '2026-08-27T22:55:00.000Z';

export const referenceDataSources: ReferenceDataSource[] = [
  {
    id: 'reference-cardnav-home',
    name: 'CardNav 公开首页参考',
    sourcePageUrl: 'https://cardnav.xyz/',
    sampledAt,
    usageNote: '公开首页的短商品和中转站展示字段，仅作本地参考样例。',
  },
  {
    id: 'reference-priceai-channels',
    name: 'PriceAI 公开渠道列表参考',
    sourcePageUrl: 'https://priceai.cc/channels',
    sampledAt,
    usageNote: '公开标准商品/渠道聚合字段，仅作本地参考样例。',
  },
  {
    id: 'reference-openprice-products',
    name: 'OpenPrice 公开商品列表参考',
    sourcePageUrl: 'https://www.openprice.cc/card-products',
    sampledAt,
    usageNote: '公开按平台分组的最低参考价字段，仅作本地参考样例。',
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
