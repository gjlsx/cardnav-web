/**
 * 文件说明: 锁定中转站评分披露、赞助外链 rel 与纠错入口，避免把展示分写成 AIGATE 综合评分。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { getMessages } from '../src/i18n/messages.js';

function read(relativePath: string) {
  return fs.readFileSync(path.resolve(relativePath), 'utf8');
}

test('gateway score copy is not claimed as an AIGATE composite score', () => {
  for (const locale of ['zh', 'en', 'ru'] as const) {
    const tip = getMessages(locale).llmGateway.gatewayScoreTip;
    assert.match(tip, /50/);
    assert.doesNotMatch(tip, /即将上线|will launch soon|скоро появится/);
    assert.match(tip, /不是 AIGATE 自有综合评分|not an AIGATE composite score|не собственный комплексный балл AIGATE/);
    assert.doesNotMatch(getMessages(locale).llmGateway.sponsoredSectionTitle, /推荐|Recommended|Рекоменд/);
  }
});

test('sponsored outbound links use sponsored rel and organic source links do not', () => {
  const detailPage = read('src/pages/llm-gateway/[slug].astro');
  const siteRow = read('src/components/GatewaySiteTableRow.astro');
  assert.match(detailPage, /rel=\{site\.sponsor \? 'sponsored noopener noreferrer' : 'noopener noreferrer'\}/);
  assert.doesNotMatch(siteRow, /site\.outboundUrl \?/);
  assert.doesNotMatch(detailPage, /telegramGroupUrl[\s\S]{0,80}rel="sponsored/);
});

test('correction and ranking independence copy sit next to gateway results', () => {
  const homePage = read('src/pages/llm-gateway.astro');
  const modelPage = read('src/pages/llm-gateway/models/[modelId].astro');
  const detailPage = read('src/pages/llm-gateway/[slug].astro');
  assert.match(homePage, /rankingIndependenceNote/);
  assert.match(modelPage, /rankingIndependenceNote/);
  assert.match(detailPage, /rankingIndependenceNote/);
  assert.match(homePage, /reportIssue/);
  assert.match(detailPage, /reportIssue/);
});
