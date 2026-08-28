/**
 * 文件说明: 锁定公开参考样例的可追溯边界，避免把演示数据变成无来源的实时承诺。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import {
  referenceDataSources,
  referenceLeaderboardSamples,
  referenceOfficialPriceSamples,
  referenceProductSamples,
} from '../src/reference-samples.js';
import { MODEL_LEADERBOARD_TASK_SLUGS } from '../src/model-leaderboard.js';
import { officialPlanRelation } from '../src/official-price.js';

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

test('official price reference samples cover four apps, regional rows, provenance, and both public snapshots', async () => {
  const sourceIds = new Set(referenceDataSources.map(source => source.id));
  const appSlugs = new Set(referenceOfficialPriceSamples.map(sample => sample.appSlug));
  assert.deepEqual([...appSlugs].sort(), ['chatgpt', 'claude', 'gemini', 'grok']);
  for (const appSlug of appSlugs) {
    assert.ok(referenceOfficialPriceSamples.filter(sample => sample.appSlug === appSlug).length >= 2);
  }
  for (const sample of referenceOfficialPriceSamples) {
    assert.ok(sourceIds.has(sample.sourceId));
    assert.equal(sample.isSample, true);
    assert.match(sample.urlSlug, /^[a-z0-9-]+$/);
    assert.ok(sample.sourcePageUrl.startsWith('https://'));
  }

  const source = await fs.promises.readFile(path.resolve('scripts/seed-reference-samples.ts'), 'utf8');
  assert.match(source, /'official-price-catalog'/);
  assert.match(source, /'official-prices'/);
  assert.match(source, /referenceOfficialPriceSamples/);
  assert.match(source, /ON DUPLICATE KEY UPDATE/);
});

test('leaderboard reference samples fill four tasks, keep video-generation empty, and stay sourced', async () => {
  const sourceIds = new Set(referenceDataSources.map(source => source.id));
  assert.ok(sourceIds.has('reference-cardnav-leaderboard'));
  const tasks = new Set(referenceLeaderboardSamples.map(sample => sample.taskSlug));
  assert.deepEqual([...tasks].sort(), ['coding', 'creative-writing', 'math', 'text-to-image']);
  assert.ok(!tasks.has('video-generation'));
  assert.ok(MODEL_LEADERBOARD_TASK_SLUGS.includes('video-generation'));
  for (const sample of referenceLeaderboardSamples) {
    assert.ok(sourceIds.has(sample.sourceId));
    assert.equal(sample.isSample, true);
    assert.match(sample.sourceUrl, /^https:\/\//);
    assert.ok(sample.rank >= 1);
  }
  const source = await fs.promises.readFile(path.resolve('scripts/seed-reference-samples.ts'), 'utf8');
  assert.match(source, /'model-leaderboard-task-slugs'/);
  assert.match(source, /'model-leaderboards'/);
  assert.match(source, /referenceLeaderboardSamples/);
  assert.doesNotMatch(source, /video-generation.*rank/);
});

test('official plan details use only declared internal catalog and model-family relations', () => {
  assert.deepEqual(officialPlanRelation('chatgpt-plus'), { catalogTarget: 'chatgpt-plus', modelFamily: 'gpt' });
  assert.deepEqual(officialPlanRelation('claude-pro'), { catalogTarget: 'claude-pro', modelFamily: 'claude' });
  assert.deepEqual(officialPlanRelation('gemini-advanced'), { catalogTarget: 'gemini', modelFamily: 'gemini' });
  assert.deepEqual(officialPlanRelation('grok-supergrok'), { catalogTarget: 'super-grok', modelFamily: 'grok' });
  assert.equal(officialPlanRelation('unverified-plan'), null);
});
