/**
 * 文件说明: 锁定 t08281547.p010 的中转站展示、收录入口与公开样例脱敏边界。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const readSource = (relativePath: string) => fs.readFileSync(path.resolve(relativePath), 'utf8');

test('gateway list keeps only useful comparison columns and provides review contacts', () => {
  const source = readSource('src/pages/llm-gateway.astro');
  const clientSource = readSource('src/scripts/llm-gateway-home.js');
  const siteSource = readSource('src/site.ts');
  assert.doesNotMatch(source, /label=\{t\.llmGateway\.modelCount\}/);
  assert.doesNotMatch(source, /label=\{t\.llmGateway\.paymentMethods\}/);
  assert.doesNotMatch(source, /data-home-site-payment/);
  assert.doesNotMatch(clientSource, /sitePaymentSelect|paymentBadges|sortModelCount/);
  assert.match(source, /gatewaySubmissionEmail/);
  assert.match(siteSource, /gatewaySubmissionEmail = 'xiu\.juan2love@gmail\.com'/);
  assert.match(source, /href=\{telegramGroupUrl\}/);
  assert.match(siteSource, /https:\/\/t\.me\/\+AX9TXrzMaS04OWI1/);
});

test('product presentation omits merchant provider names while the leaderboard discloses its evidence source', () => {
  const shopsSource = readSource('src/scripts/index.js');
  const leaderboardSource = readSource('src/components/ModelLeaderboardContent.astro');
  assert.doesNotMatch(shopsSource, /channel\.siteName/);
  assert.match(leaderboardSource, /item\.localizedSourceName/);
  assert.match(leaderboardSource, /evidence\.sourceUrl/);
});
