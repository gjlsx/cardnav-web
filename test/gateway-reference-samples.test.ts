/**
 * 文件说明: 锁定网关公开参考样例的可追溯、非实时和排序边界。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { referenceGatewaySamples, referenceGatewayModelCoverage } from '../src/reference-samples.js';
import { formatBeijingRefreshTime } from '../src/store.js';

const storeSource = fs.readFileSync(path.resolve('src/store.ts'), 'utf8');
const seedSource = fs.readFileSync(path.resolve('scripts/seed-reference-samples.ts'), 'utf8');
const schemaSource = fs.readFileSync(path.resolve('src/database.ts'), 'utf8');

test('gateway reference samples are limited, sourced, score-neutral, and have no outbound URL', () => {
  assert.ok(referenceGatewaySamples.length >= 4 && referenceGatewaySamples.length <= 8);
  for (const sample of referenceGatewaySamples) {
    assert.equal(sample.isSample, true);
    assert.equal(sample.score, 50);
    assert.equal(sample.url, '');
    assert.equal(sample.inviteUrl, '');
    assert.match(sample.sourcePageUrl, /^https:\/\//);
  }
  assert.ok(referenceGatewayModelCoverage.some(coverage => coverage.hasPublicPrice === false));
});

test('gateway support coverage is independent of public price rows and snapshots', () => {
  assert.match(schemaSource, /CREATE TABLE IF NOT EXISTS gateway_model_coverage/);
  assert.match(storeSource, /FROM gateway_model_coverage coverage/);
  assert.match(storeSource, /gateway_sites\.score DESC, gateway_sites\.name ASC/);
  assert.match(seedSource, /'gateway-sites'/);
  assert.match(seedSource, /'gateway-models'/);
  assert.match(seedSource, /gateway_model_coverage/);
});

test('gateway list avoids performance claims and empty reference URLs do not create an open action', () => {
  const siteRowSource = fs.readFileSync(path.resolve('src/components/GatewaySiteTableRow.astro'), 'utf8');
  const detailPageSource = fs.readFileSync(path.resolve('src/pages/llm-gateway/[slug].astro'), 'utf8');
  const deferredTableSource = fs.readFileSync(path.resolve('src/scripts/gateway-detail-tables.js'), 'utf8');
  assert.match(siteRowSource, /site\.outboundUrl \?/);
  assert.match(siteRowSource, /site\.isSample/);
  assert.match(siteRowSource, /site\.latestGatewayRefreshTime/);
  assert.match(siteRowSource, /site\.sourceName/);
  assert.match(detailPageSource, /site\.url \?/);
  assert.match(detailPageSource, /site\.outboundUrl \?/);
  assert.match(detailPageSource, /!site\.isSample/);
  assert.match(deferredTableSource, /if \(site\.outboundUrl \|\| site\.url\)/);
  assert.doesNotMatch(seedSource, /availability_percent|avg_success_latency_ms/);
  assert.match(seedSource, /availabilityPercent: null/);
});

test('gateway row mapper turns SQL NULL URLs into an empty public value', () => {
  assert.match(storeSource, /const url = row\.url == null \? '' : String\(row\.url\)\.trim\(\);/);
  assert.doesNotMatch(storeSource, /const url = String\(row\.url\);/);
});

test('gateway sample snapshots use the same Beijing display time as the detail query', () => {
  assert.equal(formatBeijingRefreshTime('2026-08-27T22:55:00.000Z'), '2026-08-28 06:55:00');
  assert.match(seedSource, /formatBeijingRefreshTime/);
  assert.doesNotMatch(seedSource, /latestGatewayRefreshTime: toMySqlDate/);
});
