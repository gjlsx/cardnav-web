/**
 * 文件说明: 约束公开站点的品牌、社群占位和赞助商展示要求。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const readSource = (relativePath: string) => fs.readFileSync(path.resolve(relativePath), 'utf8');
const siteSource = readSource('src/site.ts');
const publicPageSource = readSource('src/layouts/PublicPage.astro');
const sponsorsSource = readSource('src/components/Sponsors.astro');

test('public runtime uses ai.lovemoney.live and blank community placeholders', () => {
  assert.match(siteSource, /publicSiteUrl = process\.env\.PUBLIC_SITE_URL \|\| 'https:\/\/ai\.lovemoney\.live'/);
  assert.match(siteSource, /telegramGroupUrl = ''/);
  assert.match(siteSource, /xProfileUrl = ''/);
  assert.match(siteSource, /qqGroupUrl = ''/);
  assert.doesNotMatch(siteSource, /cardnav\.xyz|t\.me\/cardnav_xyz_group|github\.com\/charleslee8266|x\.com\/CharlesLee8266/);
});

test('shared page shell removes the hero and GitHub while keeping empty community placeholders', () => {
  assert.doesNotMatch(publicPageSource, /githubRepoUrl|shouldShowHero/);
  assert.match(publicPageSource, /telegramGroupUrl/);
  assert.match(publicPageSource, /xProfileUrl/);
  assert.match(publicPageSource, /qqGroupUrl/);
  assert.match(publicPageSource, /<span[^>]*>\s*\{t\.announcement\.message\}/);
});

test('sponsors render images only without outbound links or copy', () => {
  assert.doesNotMatch(sponsorsSource, /<a\s+href=|sponsor-name|sponsor-copy|sponsor-plan-title|sponsor-plan-grid/);
  assert.match(sponsorsSource, /<img src=\{sponsor\.image\.src\}/);
});
