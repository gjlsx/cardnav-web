/**
 * 文件说明: 锁定公开参考样例的可追溯边界，避免把演示数据变成无来源的实时承诺。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { referenceDataSources, referenceProductSamples } from '../src/reference-samples.js';

test('reference product samples are few, sourced, and explicitly non-transactional', () => {
  assert.ok(referenceProductSamples.length > 0 && referenceProductSamples.length <= 12);
  const sourceIds = new Set(referenceDataSources.map(source => source.id));
  for (const sample of referenceProductSamples) {
    assert.ok(sourceIds.has(sample.sourceId));
    assert.match(sample.siteId, /^reference-/);
    assert.equal(sample.priceUnit, '¥');
    assert.equal(sample.currencyCode, 'CNY');
  }
  for (const source of referenceDataSources) assert.match(source.sourcePageUrl, /^https:\/\//);
});

test('reference seed only refreshes product snapshots and never overwrites popular search terms', async () => {
  const source = await fs.promises.readFile(path.resolve('scripts/seed-reference-samples.ts'), 'utf8');
  const snapshots = source.match(/const snapshots = \[[\s\S]*?\] as const/)?.[0] ?? '';
  assert.match(snapshots, /'shop-products'/);
  assert.match(snapshots, /'shop-products-packed'/);
  assert.doesNotMatch(snapshots, /'popular-search-terms'/);
});
