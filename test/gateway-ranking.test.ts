/**
 * 文件说明: 锁定中转站自然榜与赞助展示的服务端隔离，赞助不得改写自然顺序或分数。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { paginateGatewayRanking, splitGatewaySiteRanking, type RankedGatewaySite } from '../src/gateway-ranking.js';

function site(overrides: Partial<RankedGatewaySite> & Pick<RankedGatewaySite, 'name'>): RankedGatewaySite {
  return {
    siteScore: 50,
    modelCount: 1,
    sponsor: false,
    ...overrides,
  };
}

test('toggling sponsor does not change natural order or display scores', () => {
  const naturalInput = [
    site({ name: 'Gamma', siteScore: 50, modelCount: 3 }),
    site({ name: 'Alpha', siteScore: 80, modelCount: 1 }),
    site({ name: 'Beta', siteScore: 80, modelCount: 4 }),
  ];
  const sponsoredInput = naturalInput.map(row => (
    row.name === 'Gamma' ? { ...row, sponsor: true } : { ...row }
  ));

  const withoutSponsor = splitGatewaySiteRanking(naturalInput);
  const withSponsor = splitGatewaySiteRanking(sponsoredInput);

  assert.deepEqual(
    withSponsor.natural.map(row => ({ name: row.name, siteScore: row.siteScore })),
    withoutSponsor.natural.map(row => ({ name: row.name, siteScore: row.siteScore })),
  );
  assert.deepEqual(
    withSponsor.natural.map(row => row.name),
    ['Beta', 'Alpha', 'Gamma'],
  );
  assert.deepEqual(withoutSponsor.sponsored.map(row => row.name), []);
  assert.deepEqual(withSponsor.sponsored.map(row => row.name), ['Gamma']);
});

test('sponsored collection never removes a naturally qualified partner from natural results', () => {
  const rows = [
    site({ name: 'Partner', siteScore: 90, modelCount: 2, sponsor: true }),
    site({ name: 'Other', siteScore: 40, modelCount: 8, sponsor: false }),
  ];
  const ranking = splitGatewaySiteRanking(rows);

  assert.deepEqual(ranking.natural.map(row => row.name), ['Partner', 'Other']);
  assert.deepEqual(ranking.sponsored.map(row => row.name), ['Partner']);
  assert.equal(ranking.natural[0]?.siteScore, 90);
});

test('no sponsor input keeps the existing natural sort and an empty sponsored list', () => {
  const rows = [
    site({ name: 'Zed', siteScore: 50, modelCount: 2 }),
    site({ name: 'Ann', siteScore: 50, modelCount: 2 }),
  ];
  const ranking = splitGatewaySiteRanking(rows);

  assert.deepEqual(ranking.natural.map(row => row.name), ['Ann', 'Zed']);
  assert.deepEqual(ranking.sponsored, []);
});

test('ranking pagination slices the natural list without dropping sponsored rows', () => {
  const rows = [
    site({ name: 'High', siteScore: 90, modelCount: 2, sponsor: true }),
    site({ name: 'Mid', siteScore: 40, modelCount: 1 }),
    site({ name: 'Low', siteScore: 10, modelCount: 8 }),
  ];
  const page = paginateGatewayRanking(rows, 1);

  assert.deepEqual(page.items.map(row => row.name), ['Mid', 'Low']);
  assert.deepEqual(page.sponsored.map(row => row.name), ['High']);
  assert.equal(page.offset, 1);
});

test('aiapipk-style multipliers and source ranks are not used as natural sort keys', () => {
  const ranking = splitGatewaySiteRanking([
    site({ name: 'Low', siteScore: 50, modelCount: 1, sponsor: true }),
    site({ name: 'High', siteScore: 50, modelCount: 9, sponsor: false }),
  ]);

  assert.deepEqual(ranking.natural.map(row => row.name), ['High', 'Low']);
  assert.equal(ranking.natural.every(row => row.siteScore === 50), true);
});

test('gateway JSON endpoints reuse the same split helper for SSR and deferred loads', () => {
  const sitesApi = fs.readFileSync(path.resolve('src/pages/api/llm-gateway/sites.json.ts'), 'utf8');
  const modelSitesApi = fs.readFileSync(path.resolve('src/pages/api/llm-gateway/model-sites/[modelId].json.ts'), 'utf8');
  assert.match(sitesApi, /paginateGatewayRanking/);
  assert.match(sitesApi, /sponsored/);
  assert.match(modelSitesApi, /paginateGatewayRanking/);
  assert.match(modelSitesApi, /sponsored/);
});
