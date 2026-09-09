/**
 * 文件说明: 锁定模型榜单首屏、加载更多和 API 共用来源证据而不伪造分数。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const component = fs.readFileSync('src/components/ModelLeaderboardContent.astro', 'utf8');
const api = fs.readFileSync('src/pages/api/model-leaderboard/[taskSlug].json.ts', 'utf8');
const widgets = fs.readFileSync('src/scripts/page-widgets.js', 'utf8');

test('SSR leaderboard rows display evidence labels, safe source links, and a non-zero unknown state', () => {
  assert.match(component, /item\.evidence/);
  assert.match(component, /evidence\.sourceUrl/);
  assert.match(component, /t\.leaderboard\.notProvided/);
  assert.match(component, /t\.leaderboard\.methodNotRecorded/);
  assert.doesNotMatch(component, /item\.score\.toFixed/);
});

test('load-more API forwards the same evidence contract without exposing unverified values', () => {
  for (const key of ['sourceUrl', 'sourceName', 'sampledAt', 'groupKey', 'status', 'methodStatus']) {
    assert.match(api, new RegExp(`\\b${key}\\b`));
  }
  assert.match(api, /evidence\.displayScore/);
  assert.match(api, /evidence\.displayRank/);
});

test('browser-rendered rows preserve nullable score and source evidence instead of coercing null', () => {
  assert.match(widgets, /item\.score === null/);
  assert.match(widgets, /item\.sourceUrl/);
  assert.match(widgets, /item\.methodNotice/);
  assert.doesNotMatch(widgets, /const score = Number\(item\.score\)/);
});
