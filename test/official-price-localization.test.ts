/**
 * 文件说明: 锁定官方订阅参考价的语言货币和来源展示，不把中文样例来源泄漏到英文/俄文页面。
 */
import assert from 'node:assert/strict';
import test from 'node:test';
import { localizeOfficialPriceGroups } from '../src/localized-display.js';
import type { OfficialPriceGroup } from '../src/official-price.js';
import type { PublicOfficialPriceRow } from '../src/store.js';

const price: PublicOfficialPriceRow = {
  appSlug: 'chatgpt', planSlug: 'plus', appName: 'ChatGPT', planName: 'Plus', displayName: 'ChatGPT Plus',
  urlSlug: 'chatgpt-plus', isDefault: true, displayOrder: 10, countryCode: 'US', countryLabel: '美国',
  currencyCode: 'USD', priceText: '$20.00', priceValue: 20, cnyPrice: 144, usdPrice: 20, rubPrice: 1840,
  sourceId: 'reference-cardnav-official-price', sourceName: 'CardNav 官方订阅公开参考',
  sourcePageUrl: 'https://cardnav.xyz/official-price/chatgpt-pro-5x', sampledAt: '2026-08-27T22:55:00.000Z',
  isSample: true, fetchedAt: '2026-08-27T22:55:00.000Z',
};

const group: OfficialPriceGroup = {
  key: 'chatgpt:plus', appSlug: 'chatgpt', planSlug: 'plus', urlSlug: 'chatgpt-plus', pathname: '/official-price/chatgpt-plus',
  appName: 'ChatGPT', planName: 'Plus', displayName: 'ChatGPT Plus', isDefault: true, displayOrder: 10, prices: [price],
};

test('official price equivalents and reference labels localize for zh en ru', () => {
  const zh = localizeOfficialPriceGroups([group], 'zh')[0].prices[0];
  const en = localizeOfficialPriceGroups([group], 'en')[0].prices[0];
  const ru = localizeOfficialPriceGroups([group], 'ru')[0].prices[0];
  assert.equal(zh.equivalentCurrencyCode, 'CNY');
  assert.equal(en.equivalentCurrencyCode, 'USD');
  assert.equal(ru.equivalentCurrencyCode, 'RUB');
  assert.match(en.equivalentPriceText, /20\.00/);
  assert.match(ru.equivalentPriceText, /1[\s ]840/);
  assert.equal(en.localizedSourceName, 'CardNav official plan public reference');
  assert.equal(ru.localizedSourceName, 'Публичная справка CardNav по официальному плану');
});
