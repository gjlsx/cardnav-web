/**
 * 文件说明: 验证公开 Shop 数据、热门词和点击只使用 online cardShop 记录。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const storeSource = fs.readFileSync(path.resolve('src/store.ts'), 'utf8');

test('public shop reads and interactions require online card shops', () => {
  assert.match(storeSource, /FROM shop_sites\s+WHERE status = 'online'\s+AND type = 'cardShop'/);
  assert.match(storeSource, /INNER JOIN shop_sites ON shop_sites\.id = shop_products\.site_id\s+WHERE shop_sites\.status = 'online'\s+AND shop_sites\.type = 'cardShop'/);
  assert.match(storeSource, /SELECT shop_products\.id FROM shop_products INNER JOIN shop_sites[\s\S]+?shop_sites\.status = 'online'[\s\S]+?shop_sites\.type = 'cardShop'/);
  assert.match(storeSource, /UPDATE shop_products SET click_count = click_count \+ 1 WHERE id = \?/);
  assert.match(storeSource, /SELECT term FROM shop_search_terms WHERE total_count > 0 AND result_count > 0/);
});

test('shop default applies canonical aggregation and keeps merchant/product details internal', () => {
  const browserSource = fs.readFileSync(path.resolve('src/scripts/index.js'), 'utf8');
  const merchantViewSource = fs.readFileSync(path.resolve('src/scripts/shops-merchant-view.js'), 'utf8');
  assert.match(storeSource, /aggregateCatalogProducts\(rawProducts\)/);
  assert.match(browserSource, /shopProductChannelDetails/);
  assert.match(browserSource, /document\.createElement\('span'\)/);
  assert.doesNotMatch(browserSource.match(/function createTrackedProductLink[\s\S]+?function tableLabel/)?.[0] ?? '', /\.href\s*=/);
  assert.doesNotMatch(merchantViewSource, /document\.createElement\('a'\)|\.href\s*=/);
});

test('public gateway sites expose sponsor marker and pin sponsors before score sorting', () => {
  assert.match(storeSource, /gateway_sites\.sponsor/);
  assert.match(storeSource, /ORDER BY gateway_sites\.sponsor DESC, gateway_sites\.score DESC/);
});

test('public shop products expose sponsor marker and prioritize sponsored products', () => {
  assert.match(storeSource, /shop_sites\.sponsor AS site_sponsor/);
  assert.match(storeSource, /ORDER BY shop_sites\.sponsor DESC, shop_products\.score DESC/);
});

test('public gateway detail does not truncate model price rows', () => {
  const detailQuery = storeSource.match(/export async function loadGatewayDetail[\s\S]+?return \{/)?.[0] ?? '';
  assert.doesNotMatch(detailQuery, /LIMIT\s+80\b/);
});
