/**
 * 文件说明: 锁定公开参考样例的可追溯边界，避免把演示数据变成无来源的实时承诺。
 */
import assert from 'node:assert/strict';
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
