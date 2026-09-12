/**
 * 文件说明: 锁定中转站自然表不再按赞助 sticky，以及独立赞助区走 p002 隔离结果。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

function read(relativePath: string) {
  return fs.readFileSync(path.resolve(relativePath), 'utf8');
}

test('gateway list and model detail keep sponsor sticky out of the natural table', () => {
  const homePage = read('src/pages/llm-gateway.astro');
  const modelPage = read('src/pages/llm-gateway/models/[modelId].astro');
  const homeScript = read('src/scripts/llm-gateway-home.js');
  const detailScript = read('src/scripts/gateway-detail-tables.js');

  assert.doesNotMatch(homePage, /stickySortKey="sticky"/);
  assert.doesNotMatch(homePage, /isStickyGatewaySite/);
  assert.doesNotMatch(modelPage, /stickySortKey="sticky"/);
  assert.doesNotMatch(modelPage, /isStickyGatewaySite/);
  assert.doesNotMatch(homeScript, /sortSticky: isStickySite\(site\) \? 1 : 0/);
  assert.doesNotMatch(homeScript, /sticky: isStickySite\(site\) \? 1 : 0/);
  assert.doesNotMatch(detailScript, /sticky: site\.sponsor \? 1 : 0/);
  assert.doesNotMatch(detailScript, /sortSticky: site\.sponsor \? 1 : 0/);
});

test('gateway list and model detail render a labeled sponsored region from the ranking split', () => {
  const homePage = read('src/pages/llm-gateway.astro');
  const modelPage = read('src/pages/llm-gateway/models/[modelId].astro');
  const homeScript = read('src/scripts/llm-gateway-home.js');
  const detailScript = read('src/scripts/gateway-detail-tables.js');

  const sponsoredComponent = read('src/components/GatewaySponsoredSites.astro');
  assert.match(homePage, /splitGatewaySiteRanking/);
  assert.match(homePage, /GatewaySponsoredSites/);
  assert.match(homePage, /sponsoredSectionTitle/);
  assert.match(modelPage, /splitGatewaySiteRanking/);
  assert.match(modelPage, /GatewaySponsoredSites/);
  assert.match(sponsoredComponent, /data-gateway-sponsored/);
  assert.match(homeScript, /payload\.sponsored/);
  assert.match(detailScript, /payload\.sponsored/);
});

test('shop sponsored pinning remains a separate product path', () => {
  const shopPinning = read('src/shop-sponsored-pinning.ts');
  const shopStore = read('src/store.ts');
  assert.match(shopPinning, /prioritizeShopProductRows/);
  assert.match(shopStore, /ORDER BY shop_sites\.sponsor DESC, shop_products\.score DESC/);
});
