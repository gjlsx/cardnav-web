import assert from 'node:assert/strict';
import test from 'node:test';
import { aggregateCatalogProducts, catalogProductSlugsForTarget, catalogProductTarget } from '../src/catalog.js';

test('standard product aggregation keeps the highest-priority source and chooses its lowest offer', () => {
  const products = aggregateCatalogProducts([
    {
      standardProduct: 'chatgpt-plus', platform: 'ChatGPT', productType: 'subscription', categoryName: 'ChatGPT', name: 'ChatGPT Plus',
      price: '¥120', priceNumber: 120, priceUnit: '¥', currencyCode: 'CNY', inStock: true, refreshedAt: '2026-08-28T00:00:00.000Z',
      refreshTime: '', siteId: 'merchant-a', siteName: '商家 A', siteUrl: '', siteProductRefreshSuccessAt: null, siteProductRefreshSuccessTime: '', siteScore: 50,
      siteSponsor: false, clickCount: 0, score: 0, sourceName: '低优先级', sourcePriority: 10, isSample: true,
    },
    {
      standardProduct: 'chatgpt-plus', platform: 'ChatGPT', productType: 'subscription', categoryName: 'ChatGPT', name: 'ChatGPT Plus',
      price: '¥99', priceNumber: 99, priceUnit: '¥', currencyCode: 'CNY', inStock: false, refreshedAt: '2026-08-28T01:00:00.000Z',
      refreshTime: '', siteId: 'merchant-b', siteName: '商家 B', siteUrl: '', siteProductRefreshSuccessAt: null, siteProductRefreshSuccessTime: '', siteScore: 50,
      siteSponsor: false, clickCount: 0, score: 0, sourceName: '同优先级', sourcePriority: 20, isSample: true,
    },
    {
      standardProduct: 'chatgpt-plus', platform: 'ChatGPT', productType: 'subscription', categoryName: 'ChatGPT', name: 'ChatGPT Plus',
      price: '¥88', priceNumber: 88, priceUnit: '¥', currencyCode: 'CNY', inStock: true, refreshedAt: '2026-08-28T02:00:00.000Z',
      refreshTime: '', siteId: 'merchant-c', siteName: '商家 C', siteUrl: '', siteProductRefreshSuccessAt: null, siteProductRefreshSuccessTime: '', siteScore: 50,
      siteSponsor: false, clickCount: 0, score: 0, sourceName: '同优先级', sourcePriority: 20, isSample: true,
    },
  ]);

  assert.equal(products.length, 1);
  assert.equal(products[0].priceNumber, 88);
  assert.equal(products[0].channelCount, 2);
  assert.equal(products[0].availableChannelCount, 1);
  assert.equal(products[0].channelDetails?.map(channel => channel.siteId).join(','), 'merchant-c,merchant-b');
  assert.equal(products[0].siteScore, 50, 'source priority must never overwrite a site display score');
});

test('catalog targets use declared mappings only', () => {
  assert.deepEqual(catalogProductTarget('chatgpt-plus'), { kind: 'subscription_plan', slug: 'chatgpt-plus' });
  assert.equal(catalogProductTarget('made-up-gpt-plan'), null);
  assert.deepEqual(catalogProductSlugsForTarget('chatgpt-plus'), ['chatgpt-basic-account', 'chatgpt-plus-code', 'gpt-pro-20x-credit']);
});
